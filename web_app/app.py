import html
import os
import sys

import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


DIRETORIO_ATUAL = os.path.dirname(__file__)
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, ".."))
sys.path.append(DIRETORIO_RAIZ)


if get_script_run_ctx(suppress_warning=True) is None:
    print(
        "This file is a Streamlit app.\n"
        "Run it with:\n"
        "  .\\venv\\Scripts\\python.exe -m streamlit run web_app/app.py\n"
    )
    sys.exit(0)

try:
    from src.processo import Processo
    from src.simulador import Simulador
    from src.escalonadores import (
        EscalonadorFIFO,
        EscalonadorSJF,
        EscalonadorRoundRobin,
        EscalonadorEDF,
        EscalonadorCFSSim,
    )
    from src.metricas import gerar_dataframe_metricas, gerar_dict_resumo
    from src.memoria import GerenciadorMemoria, NUM_FRAMES
except ImportError as exc:
    st.error(f"Could not import project modules: {exc}")
    st.stop()


st.set_page_config(
    page_title="OS Simulator",
    layout="wide",
    initial_sidebar_state="expanded",
)


PALETA_PROCESSOS = [
    "#1d4ed8", "#15803d", "#b91c1c", "#7e22ce", "#c2410c",
    "#0e7490", "#9f1239", "#4338ca", "#4d7c0f", "#0f766e",
]

DEFAULT_PROCESSOS = [
    {"ativo": True, "id": "P1", "chegada": 0, "execucao": 5, "deadline": 12, "prioridade": 2, "paginas": 5},
    {"ativo": True, "id": "P2", "chegada": 1, "execucao": 4, "deadline": 9, "prioridade": 1, "paginas": 4},
    {"ativo": True, "id": "P3", "chegada": 2, "execucao": 6, "deadline": 14, "prioridade": 3, "paginas": 6},
    {"ativo": True, "id": "P4", "chegada": 4, "execucao": 3, "deadline": 8, "prioridade": 1, "paginas": 3},
    {"ativo": True, "id": "P5", "chegada": 6, "execucao": 5, "deadline": 16, "prioridade": 2, "paginas": 5},
    {"ativo": False, "id": "P6", "chegada": 8, "execucao": 4, "deadline": 18, "prioridade": 3, "paginas": 4},
    {"ativo": False, "id": "P7", "chegada": 10, "execucao": 3, "deadline": 20, "prioridade": 1, "paginas": 3},
    {"ativo": False, "id": "P8", "chegada": 12, "execucao": 6, "deadline": 24, "prioridade": 2, "paginas": 6},
]


CSS = """
<style>
    :root {
        --bg: #090d18;
        --surface: #111827;
        --surface-raised: #1f2937;
        --ink: #f8fafc;
        --muted: #cbd5e1;
        --line: #334155;
        --accent: #60a5fa;
        --good: #15803d;
        --warn: #c2410c;
        --bad: #b91c1c;
    }

    .stApp,
    div[data-testid="stAppViewContainer"] {
        background: var(--bg);
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2.6rem;
        max-width: 1480px;
    }

    div[data-testid="stSidebar"] {
        background: #111827;
    }

    div[data-testid="stSidebar"] * {
        color: #f9fafb;
    }

    div[data-testid="stSidebar"] [data-baseweb="select"] *,
    div[data-testid="stSidebar"] input,
    div[data-testid="stSidebar"] textarea {
        color: #111827 !important;
    }

    .app-hero {
        border: 1px solid var(--line);
        background: #111827;
        border-radius: 8px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.22);
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 30px;
        line-height: 1.1;
        font-weight: 760;
        letter-spacing: 0;
        margin: 0 0 8px 0;
    }

    .hero-subtitle {
        color: #e2e8f0 !important;
        font-size: 15px;
        margin: 0;
        max-width: 920px;
    }

    .section-heading {
        margin: 22px 0 12px 0;
    }

    .section-title {
        color: #f8fafc !important;
        font-size: 20px;
        font-weight: 720;
        margin: 0;
    }

    .section-desc {
        color: #94a3b8;
        font-size: 13px;
        line-height: 1.45;
        margin-top: 4px;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        margin: 8px 0 14px 0;
    }

    .metric-card,
    .panel,
    .process-card,
    .event-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.22);
    }

    .metric-card {
        padding: 12px 14px;
    }

    .metric-label {
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .04em;
        margin-bottom: 5px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 22px;
        font-weight: 760;
        line-height: 1.1;
    }

    .panel {
        padding: 16px;
        min-height: 130px;
    }

    .panel-title {
        color: #e2e8f0 !important;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .05em;
        margin-bottom: 12px;
    }

    .cpu-main {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }

    .cpu-pid {
        color: #ffffff;
        font-size: 32px;
        font-weight: 780;
        line-height: 1;
    }

    .cpu-state {
        color: #e2e8f0;
        font-size: 14px;
        margin-top: 8px;
    }

    .state-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 92px;
        padding: 7px 10px;
        border-radius: 999px;
        color: white;
        font-size: 12px;
        font-weight: 720;
        background: #6b7280;
    }

    .state-executando { background: var(--good); }
    .state-page_fault { background: var(--bad); }
    .state-sobrecarga { background: var(--warn); }
    .state-ocioso { background: #64748b; }

    .queue-strip {
        display: flex;
        gap: 10px;
        overflow-x: auto;
        padding-bottom: 4px;
    }

    .process-card {
        min-width: 148px;
        padding: 12px;
        background: #111827;
        border-color: #334155;
        border-left: 4px solid var(--proc-color);
        color: #ffffff;
    }

    .process-card strong {
        color: #ffffff;
        font-size: 16px;
    }

    .process-meta {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        margin-top: 10px;
        color: #cbd5e1;
        font-size: 12px;
    }

    .muted-empty {
        color: #e2e8f0;
        border: 1px dashed var(--line);
        border-radius: 8px;
        padding: 18px;
        text-align: center;
        background: #111827;
    }

    .blocked-list,
    .swap-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 10px;
    }

    .memory-summary {
        display: grid;
        grid-template-columns: minmax(240px, 300px) minmax(520px, 1fr);
        gap: 10px;
        align-items: start;
        margin-bottom: 12px;
    }

    .memory-block-title {
        color: #e2e8f0;
        font-size: 12px;
        font-weight: 760;
        letter-spacing: .05em;
        margin: 10px 0 6px;
        text-transform: uppercase;
    }

    .resident-grid {
        display: block;
    }

    .resident-table {
        border: 1px solid #263247;
        border-radius: 8px;
        background: #111827;
        overflow: hidden;
    }

    .resident-row {
        display: grid;
        grid-template-columns: 140px 72px minmax(140px, 1fr) minmax(140px, 1fr);
        gap: 10px;
        align-items: center;
        padding: 8px 10px;
        border-top: 1px solid #253044;
    }

    .resident-row:first-child {
        border-top: 0;
    }

    .resident-row.header {
        background: #172033;
        color: #cbd5e1;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: .05em;
        text-transform: uppercase;
    }

    .resident-process {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #ffffff;
        font-size: 13px;
        font-weight: 760;
    }

    .proc-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--proc-color);
        flex: 0 0 auto;
    }

    .resident-count-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: fit-content;
        min-width: 48px;
        border: 1px solid #475569;
        border-radius: 999px;
        color: #ffffff;
        font-size: 11px;
        font-weight: 720;
        padding: 4px 8px;
        background: #0f172a;
    }

    .resident-list {
        color: #e2e8f0;
        font-size: 12px;
        line-height: 1.4;
        overflow-wrap: anywhere;
    }

    .memory-grid {
        display: grid;
        grid-template-columns: repeat(var(--cols), minmax(86px, 1fr));
        gap: 6px;
        margin-bottom: 12px;
    }

    .mem-frame {
        min-height: 54px;
        border: 1px solid #263247;
        border-left: 3px solid #64748b;
        border-radius: 6px;
        padding: 7px 8px;
        background: #111827;
        color: #ffffff;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .mem-frame.occupied {
        background: #111827;
        border-color: #334155;
        border-left-color: var(--proc-color);
        color: #ffffff;
    }

    .mem-frame.hot {
        outline: 1px solid rgba(96, 165, 250, 0.70);
        outline-offset: 1px;
    }

    .frame-index {
        color: #94a3b8;
        font-size: 10px;
        font-weight: 720;
    }

    .frame-owner {
        font-size: 13px;
        font-weight: 760;
    }

    .event-card {
        padding: 11px 12px;
    }

    .event-line {
        color: #cbd5e1;
        font-size: 12px;
        margin-top: 4px;
    }

    .event-card {
        background: #111827;
        border-color: #263247;
        color: #ffffff;
        min-height: unset;
        display: grid;
        align-content: start;
        gap: 6px;
    }

    .event-kicker {
        color: #cbd5e1;
        font-size: 11px;
        font-weight: 760;
        letter-spacing: .05em;
        text-transform: uppercase;
    }

    .event-status {
        color: #ffffff;
        font-size: 16px;
        line-height: 1;
        font-weight: 780;
    }

    .event-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 4px;
        margin-top: 2px;
    }

    .event-stat {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        border-bottom: 1px solid #253044;
        padding: 5px 0;
        background: transparent;
    }

    .event-stat-label {
        color: #94a3b8;
        font-size: 10px;
        font-weight: 720;
        letter-spacing: .04em;
        text-transform: uppercase;
    }

    .event-stat-value {
        color: #ffffff;
        font-size: 12px;
        font-weight: 760;
        margin-top: 0;
    }

    .timeline-panel {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        margin: 14px 0 18px;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.22);
    }

    .timeline-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 12px;
    }

    .timeline-title {
        color: #ffffff;
        font-size: 18px;
        font-weight: 780;
        line-height: 1.2;
    }

    .timeline-subtitle {
        color: #cbd5e1;
        font-size: 12px;
        margin-top: 4px;
    }

    .timeline-legend {
        display: flex;
        flex-wrap: wrap;
        justify-content: flex-end;
        gap: 8px;
    }

    .timeline-legend-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: #e2e8f0;
        font-size: 11px;
        white-space: nowrap;
    }

    .timeline-swatch {
        width: 12px;
        height: 12px;
        border-radius: 3px;
        background: var(--swatch);
        border: 1px solid rgba(255, 255, 255, 0.22);
    }

    .timeline-scroll {
        overflow-x: auto;
        border: 1px solid #253044;
        border-radius: 8px;
        background: #090d18;
    }

    .timeline-grid {
        display: grid;
        grid-template-columns: 84px repeat(var(--ticks), 18px);
        gap: 2px;
        width: max-content;
        min-width: 100%;
        padding: 10px;
    }

    .timeline-label,
    .timeline-cell {
        min-height: 22px;
        border-radius: 4px;
    }

    .timeline-label {
        position: sticky;
        left: 0;
        z-index: 3;
        display: flex;
        align-items: center;
        color: #f8fafc;
        font-size: 12px;
        font-weight: 760;
        background: #090d18;
        padding-right: 8px;
    }

    .timeline-cell {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 9px;
        font-weight: 780;
        background: #111827;
        border: 1px solid #1f2937;
    }

    .timeline-head-cell {
        min-height: 18px;
        color: #94a3b8;
        background: transparent;
        border: 0;
        font-size: 9px;
        font-weight: 720;
    }

    .timeline-exec,
    .timeline-cpu-exec { background: #22c55e; border-color: #22c55e; }
    .timeline-ready { background: #f59e0b; border-color: #f59e0b; }
    .timeline-blocked { background: #3b82f6; border-color: #3b82f6; }
    .timeline-switch { background: #ef4444; border-color: #ef4444; }
    .timeline-idle { background: #64748b; border-color: #64748b; }
    .timeline-fault { background: #be123c; border-color: #be123c; }

    .timeline-deadline {
        box-shadow: inset 2px 0 0 #f97316;
    }

    .timeline-current {
        outline: 2px solid #e2e8f0;
        outline-offset: 1px;
    }

    .timeline-footnote {
        color: #94a3b8;
        font-size: 11px;
        margin-top: 10px;
    }

    .swap-grid {
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 6px;
    }

    .swap-card {
        background: #111827;
        border: 1px solid #263247;
        border-left: 3px solid var(--proc-color, #64748b);
        border-radius: 6px;
        color: #ffffff;
        padding: 8px 10px;
    }

    .swap-card strong {
        color: #ffffff;
        font-size: 13px;
    }

    .completion-banner {
        display: grid;
        grid-template-columns: minmax(260px, 1.2fr) minmax(420px, 2fr);
        gap: 12px;
        align-items: center;
        border: 1px solid #263247;
        border-left: 3px solid #22c55e;
        border-radius: 8px;
        background: #0f172a;
        color: #ffffff;
        padding: 14px 16px;
        margin: 14px 0 22px;
        box-shadow: none;
    }

    .completion-kicker {
        color: #86efac;
        font-size: 11px;
        font-weight: 760;
        letter-spacing: .06em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .completion-title {
        color: #ffffff;
        font-size: 18px;
        font-weight: 780;
        line-height: 1.1;
        margin-bottom: 6px;
    }

    .completion-subtitle {
        color: #cbd5e1;
        font-size: 12px;
        line-height: 1.45;
    }

    .completion-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(104px, 1fr));
        gap: 6px;
    }

    .completion-stat {
        border: 1px solid #263247;
        border-radius: 6px;
        background: #111827;
        padding: 8px 9px;
    }

    .completion-stat-label {
        color: #94a3b8;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: .05em;
        text-transform: uppercase;
    }

    .completion-stat-value {
        color: #ffffff;
        font-size: 15px;
        font-weight: 780;
        margin-top: 4px;
    }

    @media (max-width: 900px) {
        .memory-summary {
            grid-template-columns: 1fr;
        }

        .resident-row {
            grid-template-columns: 1fr;
            gap: 6px;
        }

        .memory-grid {
            grid-template-columns: repeat(2, minmax(120px, 1fr));
        }

        .completion-banner {
            grid-template-columns: 1fr;
        }

        .timeline-head {
            display: grid;
        }

        .timeline-legend {
            justify-content: flex-start;
        }
    }
</style>
"""


st.markdown(CSS, unsafe_allow_html=True)


def cor_processo(pid: str) -> str:
    indice = sum(ord(char) for char in pid) % len(PALETA_PROCESSOS)
    return PALETA_PROCESSOS[indice]


def h(valor) -> str:
    return html.escape("" if valor is None else str(valor))


def html_fragment(markup: str) -> str:
    return "".join(line.strip() for line in markup.splitlines() if line.strip())


def section_heading(titulo: str, descricao: str) -> str:
    return html_fragment(f"""
    <div class="section-heading">
        <div class="section-title">{h(titulo)}</div>
        <div class="section-desc">{h(descricao)}</div>
    </div>
    """)


def status_legivel(status: str) -> str:
    return {
        "executando": "Running",
        "page_fault": "Page Fault",
        "sobrecarga": "Context switch",
        "ocioso": "Idle",
        "pronto": "Ready",
        "bloqueado_mem": "Memory blocked",
        "terminado": "Finished",
    }.get(status, status or "Idle")


def ordenar_pid(pid: str):
    if isinstance(pid, str) and pid.startswith("P") and pid[1:].isdigit():
        return int(pid[1:])
    return pid


def processo_para_dict(processo):
    if isinstance(processo, dict):
        return processo

    return {
        "id": processo.id,
        "chegada": processo.chegada,
        "deadline": processo.deadline,
        "tempo_termino": processo.tempo_termino,
    }


def render_metric_grid(itens):
    cards = []
    for label, value in itens:
        cards.append(
            html_fragment(f"""
            <div class="metric-card">
                <div class="metric-label">{h(label)}</div>
                <div class="metric-value">{h(value)}</div>
            </div>
            """)
        )
    return html_fragment(f'<div class="metric-grid">{"".join(cards)}</div>')


def render_live_metrics(snapshot):
    metricas = snapshot.get("metricas_globais", {})
    status_memoria = snapshot.get("status_memoria", {})
    tick = snapshot.get("tick", 0)
    tempo_base = max(1, tick + 1)
    uso_cpu = metricas.get("tempo_total_execucao_cpu", 0) / tempo_base * 100
    fila = len(snapshot.get("fila_prontos", []))
    bloqueados = len(snapshot.get("processos_bloqueados_memoria", []))

    itens = [
        ("Tick", tick),
        ("CPU usage", f"{uso_cpu:.1f}%"),
        ("CPU queue", fila),
        ("Memory blocked", bloqueados),
    ]
    if status_memoria:
        itens.extend([
            ("Page Faults", status_memoria.get("total_page_faults", 0)),
            ("Frames used", f"{status_memoria.get('frames_ocupados', 0)}/{status_memoria.get('num_frames', 0)}"),
        ])
    return render_metric_grid(itens)


def render_timeline_grid(log_ticks, processos, algoritmo_nome, tick_atual=None):
    if not log_ticks:
        return '<div class="muted-empty">Timeline waiting for simulation data</div>'

    processos_info = [processo_para_dict(processo) for processo in processos]
    processos_info = sorted(processos_info, key=lambda item: ordenar_pid(item["id"]))
    deadline_por_pid = {
        processo["id"]: processo.get("deadline")
        for processo in processos_info
        if processo.get("deadline") is not None
    }

    max_tick_log = max(item["tick"] for item in log_ticks)
    max_deadline = max(deadline_por_pid.values(), default=0)
    max_tick = max(max_tick_log, max_deadline, tick_atual or 0)
    ticks = list(range(max_tick + 1))

    status_por_linha = {"CPU": {}}
    texto_por_linha = {"CPU": {}}
    for processo in processos_info:
        status_por_linha[processo["id"]] = {}
        texto_por_linha[processo["id"]] = {}

    for evento in log_ticks:
        tick = evento["tick"]
        pid = evento["id"]
        status = evento["status"]

        if pid == "CPU":
            status_por_linha["CPU"][tick] = status
            texto_por_linha["CPU"][tick] = {"sobrecarga": "TC", "ocioso": "", "page_fault": "PF"}.get(status, "")
            continue

        if pid not in status_por_linha:
            status_por_linha[pid] = {}
            texto_por_linha[pid] = {}

        status_por_linha[pid][tick] = status
        texto_por_linha[pid][tick] = ""

        if status == "executando":
            status_por_linha["CPU"][tick] = "cpu_exec"
            texto_por_linha["CPU"][tick] = pid

    status_classes = {
        "executando": "timeline-exec",
        "cpu_exec": "timeline-cpu-exec",
        "esperando": "timeline-ready",
        "bloqueado_mem": "timeline-blocked",
        "sobrecarga": "timeline-switch",
        "ocioso": "timeline-idle",
        "page_fault": "timeline-fault",
    }
    status_labels = {
        "executando": "Running",
        "cpu_exec": "CPU running process",
        "esperando": "CPU queue",
        "bloqueado_mem": "Memory blocked",
        "sobrecarga": "Context switch",
        "ocioso": "CPU idle",
        "page_fault": "Page Fault",
    }

    header = ['<div class="timeline-label">Time</div>']
    for tick in ticks:
        label = str(tick) if tick % 5 == 0 or tick == max_tick else ""
        header.append(f'<div class="timeline-cell timeline-head-cell">{label}</div>')

    rows = ["".join(header)]
    row_ids = ["CPU"] + [processo["id"] for processo in processos_info]

    for row_id in row_ids:
        cells = [f'<div class="timeline-label">{h(row_id)}</div>']
        for tick in ticks:
            status = status_por_linha.get(row_id, {}).get(tick)
            classes = ["timeline-cell"]
            texto = texto_por_linha.get(row_id, {}).get(tick, "")
            titulo_status = "No event"

            if status:
                classes.append(status_classes.get(status, ""))
                titulo_status = status_labels.get(status, status)

            if row_id != "CPU" and deadline_por_pid.get(row_id) == tick:
                classes.append("timeline-deadline")
                texto = texto or "D"

            if tick_atual is not None and tick == tick_atual:
                classes.append("timeline-current")

            titulo = f"{row_id} | tick {tick} | {titulo_status}"
            cells.append(
                f'<div class="{" ".join(classes)}" title="{h(titulo)}">{h(texto)}</div>'
            )

        rows.append("".join(cells))

    legend = [
        ("#22c55e", "Running"),
        ("#f59e0b", "CPU queue"),
        ("#3b82f6", "Memory blocked"),
        ("#be123c", "Page Fault"),
        ("#ef4444", "Context switch"),
        ("#64748b", "CPU idle"),
        ("#f97316", "Deadline"),
    ]
    legend_html = "".join(
        f'<span class="timeline-legend-item"><span class="timeline-swatch" style="--swatch:{cor}"></span>{h(label)}</span>'
        for cor, label in legend
    )

    return html_fragment(f"""
    <div class="timeline-panel">
        <div class="timeline-head">
            <div>
                <div class="timeline-title">Tick timeline - {h(algoritmo_nome)}</div>
                <div class="timeline-subtitle">Each column represents one simulation time unit.</div>
            </div>
            <div class="timeline-legend">{legend_html}</div>
        </div>
        <div class="timeline-scroll">
            <div class="timeline-grid" style="--ticks:{len(ticks)}">
                {"".join(rows)}
            </div>
        </div>
        <div class="timeline-footnote">Hover over a cell to inspect the process, tick, and state.</div>
    </div>
    """)


def render_completion_message(resultados):
    metricas = resultados.get("metricas_globais", {})
    memoria = resultados.get("status_memoria", {})
    processos_finalizados = resultados.get("processos_terminados", [])

    tempo_total = metricas.get("tempo_total_simulacao", 0)
    uso_cpu = metricas.get("utilizacao_cpu_percent", 0)
    throughput = metricas.get("throughput", 0)

    stats = [
        ("Processes", len(processos_finalizados)),
        ("Total time", f"{tempo_total:.0f} t.u."),
        ("CPU usage", f"{uso_cpu:.2f}%"),
        ("Throughput", f"{throughput:.4f}"),
    ]

    if memoria:
        stats.extend([
            ("Page Hits", memoria.get("total_page_hits", 0)),
            ("Page Faults", memoria.get("total_page_faults", 0)),
        ])

    stat_cards = "".join(
        html_fragment(f"""
        <div class="completion-stat">
            <div class="completion-stat-label">{h(label)}</div>
            <div class="completion-stat-value">{h(valor)}</div>
        </div>
        """)
        for label, valor in stats
    )

    return html_fragment(f"""
    <div class="completion-banner">
        <div>
            <div class="completion-kicker">Simulation complete</div>
            <div class="completion-title">Execution finished</div>
            <div class="completion-subtitle">
                All active processes finished. Consolidated results are shown below.
            </div>
        </div>
        <div class="completion-stats">{stat_cards}</div>
    </div>
    """)


def render_cpu_panel(snapshot):
    status = snapshot.get("cpu_status", "ocioso")
    processo = snapshot.get("processo_executando_detalhes")
    memoria = snapshot.get("status_memoria", {})
    ultima_memoria = memoria.get("ultima_requisicao") or {}

    if processo:
        pid = processo["id"]
        detalhe = f"Remaining {processo['tempo_restante']} t.u. | deadline {processo['deadline']}"
    elif status == "page_fault" and ultima_memoria:
        pid = ultima_memoria.get("pid", "CPU")
        detalhe = (
            f"Page {ultima_memoria.get('pagina')} loaded "
            f"into frame {ultima_memoria.get('frame')}"
        )
    else:
        pid = "CPU"
        detalhe = "No process running"

    classe = f"state-{status}"
    return html_fragment(f"""
    <div class="panel">
        <div class="panel-title">CPU</div>
        <div class="cpu-main">
            <div>
                <div class="cpu-pid">{h(pid)}</div>
                <div class="cpu-state">{h(detalhe)}</div>
            </div>
            <span class="state-pill {classe}">{h(status_legivel(status))}</span>
        </div>
    </div>
    """)


def render_queue(snapshot):
    fila = snapshot.get("fila_prontos", [])
    if not fila:
        return '<div class="muted-empty">CPU queue is empty</div>'

    cards = []
    for posicao, processo in enumerate(fila, start=1):
        pid = processo["id"]
        cards.append(
            html_fragment(f"""
            <div class="process-card" style="--proc-color:{cor_processo(pid)}">
                <strong>{h(posicao)}. {h(pid)}</strong>
                <div class="process-meta">
                    <span>Remaining {h(processo['tempo_restante'])}</span>
                    <span>Deadline {h(processo['deadline'])}</span>
                    <span>Priority {h(processo['prioridade'])}</span>
                    <span>Pages {h(processo['num_paginas'])}</span>
                </div>
            </div>
            """)
        )
    return html_fragment(f'<div class="queue-strip">{"".join(cards)}</div>')


def render_blocked(snapshot):
    bloqueados = snapshot.get("processos_bloqueados_memoria", [])
    if not bloqueados:
        return '<div class="muted-empty">No process is blocked by memory</div>'

    cards = []
    for processo in bloqueados:
        pid = processo["id"]
        cards.append(
            html_fragment(f"""
            <div class="process-card" style="--proc-color:{cor_processo(pid)}">
                <strong>{h(pid)}</strong>
                <div class="process-meta">
                    <span>Unblocks in {h(processo['tempo_restante_bloqueio'])}</span>
                    <span>Page {h(processo.get('pagina'))}</span>
                    <span>Page Faults {h(processo['page_faults'])}</span>
                    <span>Remaining {h(processo['tempo_restante'])}</span>
                </div>
            </div>
            """)
        )
    return html_fragment(f'<div class="blocked-list">{"".join(cards)}</div>')


def render_memory_event(status_memoria):
    evento = status_memoria.get("ultima_requisicao")
    if not evento:
        return html_fragment("""
        <div class="event-card">
            <div class="event-status">Waiting</div>
            <div class="event-line">No page access recorded yet</div>
        </div>
        """)

    resultado = "Page Fault" if evento.get("resultado") == "fault" else "Page Hit"
    substituido = evento.get("substituido")
    detalhe_sub = ""
    if substituido:
        detalhe_sub = (
            f"<div class=\"event-line\">Swap: {h(substituido['pid'])} page "
            f"{h(substituido['pagina'])} left frame {h(substituido['frame_origem'])}</div>"
        )

    return html_fragment(f"""
    <div class="event-card">
        <div class="event-status">{h(resultado)}</div>
        <div class="event-grid">
            <div class="event-stat">
                <div class="event-stat-label">Process</div>
                <div class="event-stat-value">{h(evento.get('pid'))}</div>
            </div>
            <div class="event-stat">
                <div class="event-stat-label">Page</div>
                <div class="event-stat-value">{h(evento.get('pagina'))}</div>
            </div>
            <div class="event-stat">
                <div class="event-stat-label">Frame</div>
                <div class="event-stat-value">{h(evento.get('frame'))}</div>
            </div>
        </div>
        <div class="event-line">{h(evento.get('politica'))} at tick {h(evento.get('tick'))}</div>
        {detalhe_sub}
    </div>
    """)


def render_memory_summary(status_memoria):
    return html_fragment(f"""
    <div class="memory-summary">
        <div>
            <div class="memory-block-title">Current access</div>
            {render_memory_event(status_memoria)}
        </div>
        <div>
            <div class="memory-block-title">Processes in RAM</div>
            {render_memory_processes(status_memoria)}
        </div>
    </div>
    """)


def render_memory_grid(status_memoria):
    frames = status_memoria.get("frames_ram", [])
    if not frames:
        return '<div class="muted-empty">Memory is disabled</div>'

    ultima = status_memoria.get("ultima_requisicao") or {}
    frame_quente = ultima.get("frame")
    cols = min(6, max(1, status_memoria.get("num_frames", len(frames))))
    blocos = []

    for frame in frames:
        ocupado = frame.get("ocupado")
        pid = frame.get("processo_id") or "Livre"
        pagina = frame.get("pagina_num")
        indice = frame.get("indice")
        classes = "mem-frame occupied" if ocupado else "mem-frame"
        if indice == frame_quente:
            classes += " hot"

        cor = cor_processo(pid) if ocupado else "#64748b"
        owner = pid if ocupado else "Free"
        uso = f"Page {pagina}" if ocupado else "Available"
        blocos.append(
            html_fragment(f"""
            <div class="{classes}" style="--proc-color:{cor}">
                <span class="frame-index">Frame {h(indice)}</span>
                <span class="frame-owner">{h(owner)}</span>
                <span class="frame-index">{h(uso)}</span>
            </div>
            """)
        )

    return html_fragment(
        f'<div class="memory-block-title">RAM frames</div>'
        f'<div class="memory-grid" style="--cols:{cols}">{"".join(blocos)}</div>'
    )


def render_memory_processes(status_memoria):
    residentes = status_memoria.get("processos_residentes", [])
    if not residentes:
        return '<div class="muted-empty">No process is resident in RAM</div>'

    rows = [
        html_fragment("""
        <div class="resident-row header">
            <div>Process</div>
            <div>Frames</div>
            <div>Pages in RAM</div>
            <div>Occupied frames</div>
        </div>
        """)
    ]
    for processo in sorted(residentes, key=lambda item: ordenar_pid(item["pid"])):
        pid = processo["pid"]
        paginas = ", ".join(str(pagina) for pagina in processo["paginas"])
        frames = ", ".join(str(frame) for frame in processo["frames"])
        rows.append(
            html_fragment(f"""
            <div class="resident-row" style="--proc-color:{cor_processo(pid)}">
                <div class="resident-process">
                    <span class="proc-dot"></span>
                    <span>{h(pid)}</span>
                </div>
                <div><span class="resident-count-pill">{h(processo['qtd_frames'])}</span></div>
                <div class="resident-list">{h(paginas)}</div>
                <div class="resident-list">{h(frames)}</div>
            </div>
            """)
        )
    return html_fragment(f'<div class="resident-table">{"".join(rows)}</div>')


def render_swap(status_memoria):
    paginas_atuais = status_memoria.get("paginas_disco", [])
    historico_swap = status_memoria.get("historico_swap", [])
    paginas = paginas_atuais or historico_swap
    titulo = "Current swap" if paginas_atuais else "Recent swap history"

    if not paginas:
        return html_fragment("""
        <div class="memory-block-title">Swap</div>
        <div class="muted-empty">No page replacement has occurred yet</div>
        """)

    cards = []
    for pagina in paginas[-8:]:
        pid = pagina["pid"]
        cards.append(
            html_fragment(f"""
            <div class="swap-card" style="--proc-color:{cor_processo(pid)}">
                <strong>{h(pid)}</strong>
                <div class="event-line">Page {h(pagina['pagina'])} left frame {h(pagina['frame_origem'])} at tick {h(pagina['tick'])}</div>
            </div>
            """)
        )
    return html_fragment(
        f'<div class="memory-block-title">{titulo}</div>'
        f'<div class="swap-grid">{"".join(cards)}</div>'
    )


def dataframe_estado(snapshot):
    linhas = []
    for processo in sorted(snapshot.get("processos", []), key=lambda item: ordenar_pid(item["id"])):
        linhas.append({
            "PID": processo["id"],
            "Status": status_legivel(processo["status"]),
            "Arrival": processo["chegada"],
            "CPU time": processo["execucao"],
            "Remaining": processo["tempo_restante"],
            "Deadline": processo["deadline"],
            "Priority": processo["prioridade"],
            "Pages": processo["num_paginas"],
            "Page Hits": processo["page_hits"],
            "Page Faults": processo["page_faults"],
            "VRuntime": round(processo["vruntime"], 2),
        })
    return pd.DataFrame(linhas)


def criar_processos_input(df_processos: pd.DataFrame, ativar_memoria: bool):
    processos = []
    erros = []
    ids_usados = set()

    for _, linha in df_processos.iterrows():
        if not bool(linha.get("ativo")):
            continue

        pid = str(linha.get("id", "")).strip()
        if not pid:
            erros.append("There is an active process without a PID.")
            continue
        if pid in ids_usados:
            erros.append(f"Duplicate PID: {pid}.")
            continue
        ids_usados.add(pid)

        try:
            chegada = int(linha["chegada"])
            execucao = int(linha["execucao"])
            deadline_relativo = int(linha["deadline"])
            prioridade = int(linha["prioridade"])
            paginas = int(linha["paginas"]) if ativar_memoria else 0
        except (TypeError, ValueError):
            erros.append(f"Invalid values in {pid}.")
            continue

        if chegada < 0 or execucao <= 0 or deadline_relativo <= 0 or prioridade <= 0 or paginas < 0:
            erros.append(f"Values out of range in {pid}.")
            continue

        processos.append({
            "id": pid,
            "chegada": chegada,
            "execucao": execucao,
            "deadline": chegada + deadline_relativo,
            "deadline_relativo": deadline_relativo,
            "prioridade": prioridade,
            "num_paginas": paginas,
        })

    if not processos:
        erros.append("Enable at least one process.")

    return processos, erros


st.markdown(
    html_fragment("""
    <div class="app-hero">
        <h1 class="hero-title">Operating System Simulator</h1>
        <p class="hero-subtitle">Scheduling, CPU queue, paged virtual memory, Page Faults, and real-time events in one simulation workspace.</p>
    </div>
    """),
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("Simulation")
    algoritmo_nome = st.selectbox("Algorithm", ("FIFO", "SJF", "RR", "EDF", "CFS"), index=2)
    quantum = st.number_input("Quantum", min_value=1, value=2, step=1)
    sobrecarga_contexto = st.number_input("Context switch cost", min_value=0, value=1, step=1)
    tick_delay = st.slider("Tick interval", min_value=0.0, max_value=0.4, value=0.04, step=0.02)

    st.header("Memory")
    ativar_memoria = st.checkbox("Enable virtual memory", value=True)
    politica_memoria = st.selectbox("Replacement policy", ("FIFO", "LRU"), disabled=not ativar_memoria)
    frames_memoria = st.slider("RAM frames", min_value=4, max_value=NUM_FRAMES, value=12, step=1, disabled=not ativar_memoria)
    custo_disco = st.number_input("Page Fault cost", min_value=0, value=3, step=1, disabled=not ativar_memoria)
    seed_memoria = st.number_input("Page access seed", min_value=1, value=42, step=1, disabled=not ativar_memoria)


st.markdown(
    section_heading(
        "Processes",
        "Set arrival time, CPU time, deadline, priority, and pages for each active process.",
    ),
    unsafe_allow_html=True,
)
df_defaults = pd.DataFrame(DEFAULT_PROCESSOS)
df_editado = st.data_editor(
    df_defaults,
    key="processos_editor",
    hide_index=True,
    width="stretch",
    num_rows="fixed",
    disabled=["id"] if ativar_memoria else ["id", "paginas"],
    column_config={
        "ativo": st.column_config.CheckboxColumn("Active"),
        "id": st.column_config.TextColumn("PID"),
        "chegada": st.column_config.NumberColumn("Arrival", min_value=0, step=1),
        "execucao": st.column_config.NumberColumn("CPU time", min_value=1, step=1),
        "deadline": st.column_config.NumberColumn("Relative deadline", min_value=1, step=1),
        "prioridade": st.column_config.NumberColumn("Priority", min_value=1, step=1),
        "paginas": st.column_config.NumberColumn("Pages", min_value=0, max_value=32, step=1),
    },
)


col_run, col_hint = st.columns([0.22, 0.78])
with col_run:
    executar = st.button("Run simulation", type="primary", width="stretch")

if executar:
    processos_input, erros = criar_processos_input(df_editado, ativar_memoria)

    if erros:
        for erro in erros:
            st.error(erro)
    else:
        lista_processos = [Processo(**processo) for processo in processos_input]
        algoritmos_map = {
            "FIFO": EscalonadorFIFO,
            "SJF": EscalonadorSJF,
            "RR": EscalonadorRoundRobin,
            "EDF": EscalonadorEDF,
            "CFS": EscalonadorCFSSim,
        }
        escalonador = algoritmos_map[algoritmo_nome]()
        gerenciador_memoria = None
        if ativar_memoria:
            gerenciador_memoria = GerenciadorMemoria(
                politica=politica_memoria,
                seed=int(seed_memoria),
                num_frames=int(frames_memoria),
            )

        simulador = Simulador(
            processos=lista_processos,
            escalonador=escalonador,
            sobrecarga_contexto=int(sobrecarga_contexto),
            quantum=int(quantum),
            gerenciador_memoria=gerenciador_memoria,
            custo_disco=int(custo_disco) if ativar_memoria else 0,
        )

        st.markdown(
            section_heading(
                "Real time",
                "Track the CPU, CPU queue, memory blocks, and tick-by-tick timeline.",
            ),
            unsafe_allow_html=True,
        )
        live_metrics_placeholder = st.empty()

        col_cpu, col_fila = st.columns([0.34, 0.66])
        with col_cpu:
            cpu_placeholder = st.empty()
        with col_fila:
            st.markdown('<div class="panel-title">CPU queue</div>', unsafe_allow_html=True)
            fila_placeholder = st.empty()

        col_proc, col_bloq = st.columns([0.58, 0.42])
        with col_proc:
            st.markdown('<div class="panel-title">Process states</div>', unsafe_allow_html=True)
            processos_placeholder = st.empty()
        with col_bloq:
            st.markdown('<div class="panel-title">Memory blocked</div>', unsafe_allow_html=True)
            bloqueados_placeholder = st.empty()

        timeline_placeholder = st.empty()

        if ativar_memoria:
            st.markdown(
                section_heading(
                    "Real-time memory",
                    "Inspect the current access, resident processes, RAM frames, and pages sent to swap.",
                ),
                unsafe_allow_html=True,
            )
            memoria_summary_placeholder = st.empty()
            memoria_grid_placeholder = st.empty()
            swap_placeholder = st.empty()
        else:
            memoria_summary_placeholder = None
            memoria_grid_placeholder = None
            swap_placeholder = None

        def on_tick(snapshot):
            live_metrics_placeholder.markdown(render_live_metrics(snapshot), unsafe_allow_html=True)
            cpu_placeholder.markdown(render_cpu_panel(snapshot), unsafe_allow_html=True)
            fila_placeholder.markdown(render_queue(snapshot), unsafe_allow_html=True)
            bloqueados_placeholder.markdown(render_blocked(snapshot), unsafe_allow_html=True)
            processos_placeholder.dataframe(
                dataframe_estado(snapshot),
                hide_index=True,
                width="stretch",
            )

            tick = snapshot.get("tick", 0)
            if tick % 2 == 0:
                timeline_placeholder.markdown(
                    render_timeline_grid(
                        snapshot["log_gantt"],
                        snapshot.get("processos", []),
                        algoritmo_nome,
                        tick_atual=tick,
                    ),
                    unsafe_allow_html=True,
                )

            status_memoria = snapshot.get("status_memoria", {})
            if ativar_memoria and status_memoria:
                memoria_summary_placeholder.markdown(render_memory_summary(status_memoria), unsafe_allow_html=True)
                memoria_grid_placeholder.markdown(render_memory_grid(status_memoria), unsafe_allow_html=True)
                swap_placeholder.markdown(render_swap(status_memoria), unsafe_allow_html=True)

        with st.spinner("Running simulation..."):
            resultados = simulador.executar(on_tick=on_tick, tick_delay=float(tick_delay))

        st.markdown(render_completion_message(resultados), unsafe_allow_html=True)
        timeline_placeholder.markdown(
            render_timeline_grid(
                resultados["log_gantt"],
                lista_processos,
                algoritmo_nome,
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            section_heading(
                "Final result",
                "Consolidated summary and per-process metrics.",
            ),
            unsafe_allow_html=True,
        )
        metricas_globais = resultados["metricas_globais"]
        status_memoria = resultados.get("status_memoria", {})
        resumo = gerar_dict_resumo(metricas_globais, resultados["processos_terminados"])
        if ativar_memoria and status_memoria:
            resumo["Memory policy"] = status_memoria.get("politica")
            resumo["Page Hits"] = status_memoria.get("total_page_hits", 0)
            resumo["Page Faults"] = status_memoria.get("total_page_faults", 0)
            resumo["Page Fault rate"] = f"{status_memoria.get('taxa_page_faults', 0):.2f}%"

        st.markdown(render_metric_grid(resumo.items()), unsafe_allow_html=True)
        st.dataframe(
            gerar_dataframe_metricas(resultados["processos_terminados"]),
            hide_index=True,
            width="stretch",
        )
