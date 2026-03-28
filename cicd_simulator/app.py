import streamlit as st
from core.engine import CICDEngine

st.set_page_config(
    page_title="Simulador CI/CD",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; color: #1E293B; }
    section[data-testid="stSidebar"] {
        background-color: #F1F5F9;
        border-right: 1px solid #E2E8F0;
    }
    .stButton > button {
        background-color: #8B5CF6;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: background 0.2s;
    }
    .stButton > button:hover { background-color: #7C3AED; color: #FFFFFF; }
    .stTextInput > div > input {
        background-color: #FFFFFF;
        color: #1E293B;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
    }
    .stSelectbox > div { background-color: #FFFFFF; color: #1E293B; border-radius: 6px; }
    h1, h2, h3 { color: #1E293B !important; font-family: 'Inter', sans-serif !important; }
    div[data-testid="stInfo"] {
        background-color: #EFF6FF;
        border-left: 4px solid #60A5FA;
        color: #1E293B;
        border-radius: 8px;
    }
    hr { border-color: #E2E8F0; }
    </style>
    """,
    unsafe_allow_html=True,
)

AGENT_ICONS  = {"Ubuntu": "🐧", "Windows": "🪟", "macOS": "🍎", "Alpine": "🏔️"}
STATUS_ICONS = {"pending": "⬜", "in_progress": "🔄", "successful": "✅", "failed": "❌"}
STATUS_LABELS = {
    "pending":     "PENDIENTE",
    "in_progress": "EN PROGRESO",
    "successful":  "EXITOSO",
    "failed":      "FALLIDO",
}
LOG_COLORS = {
    "INFO":    "#60A5FA",
    "SUCCESS": "#059669",
    "WARNING": "#F59E0B",
    "ERROR":   "#F87171",
}


def render_agents(agents: list[dict]):
    cols = st.columns(len(agents))
    for col, agent in zip(cols, agents):
        with col:
            color    = "#F87171" if agent["busy"] else "#059669"
            label    = "OCUPADO" if agent["busy"] else "LIBRE"
            icon     = AGENT_ICONS.get(agent["name"], "🖥️")
            job_html = (
                f"<div style='font-size:0.72em;color:#64748B;margin-top:4px'>"
                f"Job: {agent['job']}</div>"
                if agent["busy"] else ""
            )
            st.markdown(
                f"""
                <div style="text-align:center;padding:16px 6px;border-radius:12px;
                            border:2px solid {color};background:#FFFFFF;
                            box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                    <div style="font-size:2.2em">{icon}</div>
                    <div style="font-weight:700;color:#1E293B;margin-top:6px">{agent['name']}</div>
                    <div style="margin-top:6px;font-size:0.76em;font-weight:700;color:{color}">{label}</div>
                    {job_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_pipeline_card(pipeline_entry: dict):
    stages     = pipeline_entry["stages"]
    agent_name = pipeline_entry["agent"]
    job_id     = pipeline_entry["job_id"]
    done       = pipeline_entry["done"]

    status_styles = {
        "pending":     ("background:#F8FAFC;border-color:#E2E8F0;", "#64748B"),
        "in_progress": ("background:#EFF6FF;border-color:#60A5FA;", "#1D4ED8"),
        "successful":  ("background:#F0FDF4;border-color:#059669;", "#065F46"),
        "failed":      ("background:#FFF1F2;border-color:#F87171;", "#B91C1C"),
    }

    done_tag = (
        "<span style='font-size:0.75em;color:#94A3B8;margin-left:8px'>(finalizado)</span>"
        if done else ""
    )
    st.markdown(
        f"<div style='font-size:0.85em;font-weight:600;color:#475569;"
        f"margin-bottom:8px'>🖥️ {agent_name} — Job {job_id}{done_tag}</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(stages))
    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            icon      = STATUS_ICONS.get(stage["status"], "⬜")
            label     = STATUS_LABELS.get(stage["status"], stage["status"])
            bg_style, text_color = status_styles.get(
                stage["status"],
                ("background:#F8FAFC;border-color:#E2E8F0;", "#64748B"),
            )
            st.markdown(
                f"""
                <div style="text-align:center;padding:12px 4px;border-radius:10px;
                            border:2px solid;{bg_style}
                            box-shadow:0 1px 4px rgba(0,0,0,0.05);">
                    <div style="font-size:1.6em">{icon}</div>
                    <div style="font-size:0.75em;font-weight:600;margin-top:4px;
                                color:#1E293B">{stage['name']}</div>
                    <div style="font-size:0.65em;margin-top:3px;font-weight:600;
                                color:{text_color}">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if i < len(stages) - 1:
                st.markdown(
                    "<div style='text-align:center;font-size:1.2em;"
                    "color:#8B5CF6;padding-top:8px'>→</div>",
                    unsafe_allow_html=True,
                )


def render_stack(stack: list[dict], current_version: str):
    st.markdown(
        f"<div style='margin-bottom:12px;color:#1E293B'>Versión activa: "
        f"<span style='color:#059669;font-weight:700;font-size:1.1em'>"
        f"{current_version}</span></div>",
        unsafe_allow_html=True,
    )
    if not stack:
        st.markdown(
            "<div style='color:#94A3B8;font-style:italic'>Pila vacía.</div>",
            unsafe_allow_html=True,
        )
        return
    for i, version in enumerate(stack):
        is_top  = i == 0
        border  = "#F59E0B" if is_top else "#E2E8F0"
        top_tag = (
            "&nbsp;<span style='font-size:0.72em;color:#F59E0B;font-weight:700'>◄ CIMA</span>"
            if is_top else ""
        )
        st.markdown(
            f"""
            <div style="padding:10px 14px;margin-bottom:6px;border-radius:8px;
                        border-left:4px solid {border};background:#FFFFFF;
                        box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                <span style="font-weight:700;color:#1E293B">{version['version']}</span>
                {top_tag}<br/>
                <span style="font-size:0.74em;color:#94A3B8">commit: {version['commit']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_queue(queue: list[dict]):
    if not queue:
        st.markdown(
            "<div style='color:#94A3B8;font-style:italic;padding:8px'>Cola vacía.</div>",
            unsafe_allow_html=True,
        )
        return
    for i, job in enumerate(queue):
        st.markdown(
            f"""
            <div style="padding:10px 14px;margin-bottom:6px;border-radius:8px;
                        border-left:4px solid #8B5CF6;background:#FFFFFF;
                        box-shadow:0 1px 3px rgba(0,0,0,0.05);font-size:0.86em;">
                <b style="color:#1E293B">#{i+1} — {job['id']}</b><br/>
                <span style="color:#64748B">{job['author']} → {job['repo']} ({job['branch']})</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_logs(logs: list[dict], level_filter: str, text_filter: str):
    filtered = logs
    if level_filter != "TODOS":
        filtered = [l for l in filtered if l["level"] == level_filter]
    if text_filter:
        filtered = [l for l in filtered if text_filter.lower() in l["message"].lower()]

    if not filtered:
        st.markdown(
            "<div style='color:#94A3B8;font-style:italic;padding:8px'>"
            "No hay logs que coincidan.</div>",
            unsafe_allow_html=True,
        )
        return

    lines_html = ""
    for log in reversed(filtered):
        color = LOG_COLORS.get(log["level"], "#1E293B")
        lines_html += (
            f'<div style="margin-bottom:5px">'
            f'<span style="color:{color};font-weight:700">[{log["level"]}]</span> '
            f'<span style="color:#94A3B8">[{log["stage"]}]</span> '
            f'<span style="color:#334155">{log["message"]}</span>'
            f'</div>'
        )

    st.markdown(
        f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                    padding:16px;font-family:'Courier New',monospace;font-size:0.82em;
                    max-height:340px;overflow-y:auto;">
            {lines_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


if "engine" not in st.session_state:
    st.session_state.engine = CICDEngine()
if "system_message" not in st.session_state:
    st.session_state.system_message = ""

engine: CICDEngine = st.session_state.engine

with st.sidebar:
    st.markdown(
        "<h2 style='color:#8B5CF6;font-family:Inter,sans-serif'>🚀 Simulador CI/CD</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Estructuras de Datos — Universidad Cooperativa de Colombia")
    st.divider()

    st.subheader("📥 Nuevo Job")
    repo   = st.text_input("Repositorio", value="mi-app-backend")
    branch = st.text_input("Rama",        value="main")
    author = st.text_input("Autor",       value="dev-01")

    if st.button("⬆️ Hacer Push / Encolar Job", use_container_width=True):
        job = engine.receive_job(repository=repo, branch=branch, author=author)
        st.session_state.system_message = f"✅ Job **{job.id}** encolado correctamente."
        st.rerun()

    st.divider()
    st.subheader("⚙️ Ejecutar Pipeline")

    if st.button("🔀 Despachar Job → Agente", use_container_width=True):
        result = engine.dispatch_job()
        st.session_state.system_message = (
            f"✅ Job **{result['job'].id}** asignado a **{result['agent']}**."
            if result["ok"] else f"⚠️ {result['reason']}"
        )
        st.rerun()

    state_sidebar = engine.get_state()
    active_agents = state_sidebar["active_agents"]

    if active_agents:
        selected_agent = st.selectbox(
            "Seleccionar agente a avanzar",
            options=active_agents,
            format_func=lambda a: f"{AGENT_ICONS.get(a, '🖥️')} {a}",
        )
        if st.button("▶️ Ejecutar Siguiente Stage", use_container_width=True):
            with st.spinner("Ejecutando stage..."):
                result = engine.execute_next_stage(agent_name=selected_agent)

            if not result["ok"] and "reason" in result:
                st.session_state.system_message = f"⚠️ {result['reason']}"
            elif result.get("pipeline_end"):
                st.session_state.system_message = (
                    f"🎉 Deploy exitoso — **{result.get('version')}** en producción."
                    if result.get("deploy")
                    else f"❌ Pipeline detenido en **{result.get('stage')}**."
                )
            else:
                st.session_state.system_message = (
                    f"✅ Stage **{result.get('stage')}** completado. "
                    f"Siguiente: **{result.get('next', '—')}**"
                )
            st.rerun()
    else:
        st.button("▶️ Ejecutar Siguiente Stage", use_container_width=True, disabled=True)
        st.caption("Despacha un job primero.")

    st.divider()
    st.subheader("🔴 Emergencia")

    if st.button("⏪ Rollback de Emergencia", use_container_width=True, type="primary"):
        result = engine.execute_rollback()
        st.session_state.system_message = (
            f"⚠️ Rollback ejecutado. Restaurado a **{result['version']}**."
            if result["ok"] else f"⚠️ {result['reason']}"
        )
        st.rerun()

    st.divider()
    if st.button("🗑️ Reiniciar Simulador", use_container_width=True):
        st.session_state.engine         = CICDEngine()
        st.session_state.system_message = "Simulador reiniciado."
        st.rerun()


st.markdown(
    "<h1 style='color:#1E293B;font-family:Inter,sans-serif'>"
    "🖥️ Panel de Control — Pipeline CI/CD</h1>",
    unsafe_allow_html=True,
)

if st.session_state.system_message:
    st.info(st.session_state.system_message)

state = engine.get_state()

col_agents, col_queue, col_stack = st.columns([3, 2, 2])

with col_agents:
    st.subheader("🖥️ Agentes de Ejecución")
    st.caption("Array fijo · 4 servidores virtuales")
    render_agents(state["agents"])

with col_queue:
    st.subheader("📋 Cola de Jobs")
    st.caption(f"{len(state['queue'])} job(s) en espera")
    render_queue(state["queue"])

with col_stack:
    st.subheader("📦 Producción")
    st.caption("Pila de versiones desplegadas")
    render_stack(state["production_stack"], state["current_version"])

st.divider()
st.subheader("🔗 Pipeline — Stages")

if state["pipelines"]:
    for pipeline_entry in state["pipelines"]:
        render_pipeline_card(pipeline_entry)
        st.markdown("<br/>", unsafe_allow_html=True)
else:
    st.markdown(
        "<div style='color:#94A3B8;font-style:italic;padding:8px'>"
        "Sin pipelines activos. Despachá un job para comenzar.</div>",
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("📄 Visor de Logs")

col_f1, col_f2 = st.columns([1, 3])
with col_f1:
    level_filter = st.selectbox("Nivel", options=["TODOS", "INFO", "SUCCESS", "WARNING", "ERROR"])
with col_f2:
    text_filter = st.text_input("Buscar en logs", placeholder="ej: Checkout, Job 3A1B...")

render_logs(state["logs"], level_filter, text_filter)