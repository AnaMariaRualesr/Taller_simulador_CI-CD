import time
import random
import uuid
from data_structures.pipeline import PipelineLinkedList, StageNode
from data_structures.agents import AgentsArray, JobQueue, Job
from data_structures.production import RollbackStack, LogList, ProductionVersion

PIPELINE_STAGES = [
    "Checkout",
    "Instalar Dependencias",
    "Linter",
    "Pruebas Unitarias",
    "Despliegue",
]

STAGE_FAILURE_RATE: dict[str, float] = {
    "Checkout":              0.05,
    "Instalar Dependencias": 0.10,
    "Linter":                0.15,
    "Pruebas Unitarias":     0.15,
    "Despliegue":            0.05,
}

STAGE_DURATION: dict[str, float] = {
    "Checkout":              0.8,
    "Instalar Dependencias": 1.2,
    "Linter":                0.6,
    "Pruebas Unitarias":     1.5,
    "Despliegue":            1.0,
}


class CICDEngine:
    def __init__(self):
        self._agents         = AgentsArray()
        self._job_queue      = JobQueue()
        self._rollback_stack = RollbackStack()
        self._logs           = LogList()
        self._current_version: str = "v0.0.0"
        self._active_pipelines: dict[str, dict] = {}

    def receive_job(self, repository: str, branch: str, author: str) -> Job:
        job = Job(
            id=str(uuid.uuid4())[:8].upper(),
            repository=repository,
            branch=branch,
            author=author,
        )
        self._job_queue.enqueue(job)
        self._logs.add(
            level="INFO",
            message=f"[QUEUE] Job {job.id} encolado — {author} hizo push a '{branch}' en '{repository}'",
            stage="Sistema",
        )
        return job

    def dispatch_job(self) -> dict:
        if self._job_queue.is_empty():
            return {"ok": False, "reason": "La cola de jobs está vacía."}

        agent = self._agents.get_free_agent()
        if agent is None:
            return {"ok": False, "reason": "Todos los agentes están ocupados."}

        job               = self._job_queue.dequeue()
        agent.busy        = True
        agent.current_job = job.id

        pipeline = self._build_pipeline()
        pipeline.start()

        self._active_pipelines[agent.name] = {
            "job":      job,
            "pipeline": pipeline,
            "done":     False,
        }

        self._logs.add(
            level="INFO",
            message=f"[DISPATCH] Job {job.id} asignado al agente '{agent.name}'",
            stage="Sistema",
        )
        self._logs.add(
            level="INFO",
            message=f"[PIPELINE] Iniciando pipeline para Job {job.id} en agente '{agent.name}'",
            stage="Sistema",
        )
        return {"ok": True, "job": job, "agent": agent.name}

    def execute_next_stage(self, agent_name: str) -> dict:
        if agent_name not in self._active_pipelines:
            return {"ok": False, "reason": f"No hay pipeline activo para '{agent_name}'."}

        entry: dict                  = self._active_pipelines[agent_name]
        job: Job                     = entry["job"]
        pipeline: PipelineLinkedList = entry["pipeline"]

        if entry["done"]:
            return {"ok": False, "reason": "El pipeline ya finalizó."}

        current: StageNode | None = pipeline.current_stage
        if current is None:
            return {"ok": False, "reason": "El pipeline ya finalizó."}

        stage_name = current.name
        time.sleep(STAGE_DURATION.get(stage_name, 1.0))

        success  = random.random() >= STAGE_FAILURE_RATE.get(stage_name, 0.1)
        has_next = pipeline.advance(success=success)

        self._logs.add(
            level="SUCCESS" if success else "ERROR",
            message=(
                f"[{stage_name.upper()}] "
                f"{'✔ Completado exitosamente' if success else '✘ Falló la ejecución'}"
                f" — Job {job.id} | Agente {agent_name}"
            ),
            stage=stage_name,
        )

        if not success:
            entry["done"] = True
            self._release_agent(agent_name)
            self._logs.add(
                level="ERROR",
                message=f"[PIPELINE] Detenido en '{stage_name}'. Agente '{agent_name}' liberado.",
                stage="Sistema",
            )
            return {
                "ok":           False,
                "stage":        stage_name,
                "pipeline_end": True,
                "reason":       f"Fallo en stage '{stage_name}'",
            }

        if not has_next:
            entry["done"] = True
            self._register_deploy(job)
            self._release_agent(agent_name)
            return {
                "ok":           True,
                "stage":        stage_name,
                "pipeline_end": True,
                "deploy":       True,
                "version":      self._current_version,
            }

        return {
            "ok":           True,
            "stage":        stage_name,
            "pipeline_end": False,
            "next":         pipeline.current_stage.name,
        }

    def execute_rollback(self) -> dict:
        restored = self._rollback_stack.rollback()
        if restored is None:
            self._logs.add(
                level="WARNING",
                message="[ROLLBACK] No hay versión anterior disponible en la pila.",
                stage="Sistema",
            )
            return {"ok": False, "reason": "No hay versión anterior en la pila."}

        self._current_version = restored.version
        self._logs.add(
            level="WARNING",
            message=f"[ROLLBACK] ⚠ Rollback ejecutado. Restaurado a {restored.version} (commit: {restored.commit_hash})",
            stage="Sistema",
        )
        return {"ok": True, "version": restored.version, "commit": restored.commit_hash}

    def get_state(self) -> dict:
        pipelines_info = []
        for agent_name, entry in self._active_pipelines.items():
            stages_info = [
                {"name": node.name, "status": node.status}
                for node in entry["pipeline"].get_all()
            ]
            pipelines_info.append({
                "agent":  agent_name,
                "job_id": entry["job"].id,
                "done":   entry["done"],
                "stages": stages_info,
            })

        return {
            "agents": self._agents.get_status(),
            "queue": [
                {
                    "id":     j.id,
                    "repo":   j.repository,
                    "branch": j.branch,
                    "author": j.author,
                }
                for j in self._job_queue.peek()
            ],
            "production_stack": [
                {"version": v.version, "commit": v.commit_hash}
                for v in self._rollback_stack.get_stack()
            ],
            "current_version": self._current_version,
            "pipelines":       pipelines_info,
            "active_agents": [
                name for name, entry in self._active_pipelines.items()
                if not entry["done"]
            ],
            "logs": [
                {"level": l.level, "stage": l.stage, "message": l.message}
                for l in self._logs.filter()
            ],
        }

    def _build_pipeline(self) -> PipelineLinkedList:
        pipeline = PipelineLinkedList()
        for name in PIPELINE_STAGES:
            pipeline.add_stage(name)
        return pipeline

    def _register_deploy(self, job: Job):
        parts = self._current_version.lstrip("v").split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        self._current_version = "v" + ".".join(parts)
        new_version = ProductionVersion(
            version=self._current_version,
            commit_hash=str(uuid.uuid4())[:7],
        )
        self._rollback_stack.push(new_version)
        self._logs.add(
            level="SUCCESS",
            message=f"[DEPLOY] ✔ Versión {self._current_version} desplegada. Job {job.id} | Commit: {new_version.commit_hash}",
            stage="Despliegue",
        )

    def _release_agent(self, agent_name: str):
        self._agents.release_agent(agent_name)