from collections import deque
from dataclasses import dataclass, field
import time

EXECUTION_AGENTS = ["Ubuntu", "Windows", "macOS", "Alpine"]


@dataclass
class Agent:
    name: str
    busy: bool = False
    current_job: str | None = None


@dataclass
class Job:
    id: str
    repository: str
    branch: str
    author: str
    timestamp: float = field(default_factory=time.time)


class AgentsArray:
    def __init__(self):
        self._agents: list[Agent] = [Agent(name=n) for n in EXECUTION_AGENTS]

    def get_free_agent(self) -> Agent | None:
        for agent in self._agents:
            if not agent.busy:
                return agent
        return None

    def release_agent(self, name: str):
        for agent in self._agents:
            if agent.name == name:
                agent.busy = False
                agent.current_job = None
                break

    def get_status(self) -> list[dict]:
        return [
            {
                "index": i,
                "name": a.name,
                "busy": a.busy,
                "job": a.current_job,
            }
            for i, a in enumerate(self._agents)
        ]


class JobQueue:
    def __init__(self):
        self._queue: deque[Job] = deque()

    def enqueue(self, job: Job):
        self._queue.append(job)

    def dequeue(self) -> Job | None:
        if self._queue:
            return self._queue.popleft()
        return None

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def peek(self) -> list[Job]:
        return list(self._queue)