import html
import os
import sys

import pandas as pd
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx


DIRETORIO_ATUAL = os.path.dirname(__file__)
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, ".."))
MPL_CACHE_DIR = os.path.join(DIRETORIO_RAIZ, "out", ".matplotlib")
os.makedirs(MPL_CACHE_DIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", MPL_CACHE_DIR)
sys.path.append(DIRETORIO_RAIZ)

import matplotlib.pyplot as plt


if get_script_run_ctx(suppress_warning=True) is None:
    print(
        "Este arquivo e um app Streamlit.\n"
        "Execute com:\n"
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
    from src.visualizacao import gerar_gantt
    from src.metricas import gerar_dataframe_metricas, gerar_dict_resumo
    from src.memoria import GerenciadorMemoria, NUM_FRAMES
except ImportError as exc:
    st.error(f"Erro ao importar modulos do projeto: {exc}")
    st.stop()


st.set_page_config(
    page_title="Simulador SO",
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
        background:
            linear-gradient(135deg, rgba(29, 78, 216, 0.62), rgba(15, 118, 110, 0.50)),
            #111827;
        border-radius: 8px;
        padding: 22px 26px;
        margin-bottom: 18px;
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28);
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 34px;
        line-height: 1.05;
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

    .section-title {
        color: #f8fafc !important;
        font-size: 20px;
        font-weight: 720;
        margin: 20px 0 10px 0;
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
        background: var(--proc-color);
        border-color: var(--proc-color);
        color: #ffffff;
    }

    .process-card strong {
        color: #ffffff;
        font-size: 18px;
    }

    .process-meta {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        margin-top: 10px;
        color: #ffffff;
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
        grid-template-columns: minmax(280px, 360px) minmax(520px, 1fr);
        gap: 12px;
        align-items: start;
        margin-bottom: 14px;
    }

    .memory-block-title {
        color: #e2e8f0;
        font-size: 12px;
        font-weight: 760;
        letter-spacing: .05em;
        margin: 10px 0 8px;
        text-transform: uppercase;
    }

    .resident-grid {
        display: block;
    }

    .resident-table {
        border: 1px solid #334155;
        border-radius: 8px;
        background: #111827;
        overflow: hidden;
    }

    .resident-row {
        display: grid;
        grid-template-columns: 150px 90px minmax(140px, 1fr) minmax(140px, 1fr);
        gap: 12px;
        align-items: center;
        padding: 10px 12px;
        border-top: 1px solid #253044;
    }

    .resident-row:first-child {
        border-top: 0;
    }

    .resident-row.header {
        background: #1f2937;
        color: #cbd5e1;
        font-size: 11px;
        font-weight: 760;
        letter-spacing: .05em;
        text-transform: uppercase;
    }

    .resident-process {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #ffffff;
        font-size: 14px;
        font-weight: 760;
    }

    .proc-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: var(--proc-color);
        flex: 0 0 auto;
    }

    .resident-count-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: fit-content;
        min-width: 62px;
        border: 1px solid #475569;
        border-radius: 999px;
        color: #ffffff;
        font-size: 12px;
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
        grid-template-columns: repeat(var(--cols), minmax(108px, 1fr));
        gap: 8px;
        margin-bottom: 14px;
    }

    .mem-frame {
        min-height: 74px;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 8px;
        background: #64748b;
        color: #ffffff;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .mem-frame.occupied {
        background: var(--proc-color);
        border-color: var(--proc-color);
        color: #ffffff;
    }

    .mem-frame.hot {
        outline: 3px solid rgba(37, 99, 235, 0.22);
    }

    .frame-index {
        color: #ffffff;
        font-size: 11px;
        font-weight: 720;
    }

    .frame-owner {
        font-size: 15px;
        font-weight: 760;
    }

    .event-card {
        padding: 10px 12px;
    }

    .event-line {
        color: #ffffff;
        font-size: 13px;
        margin-top: 6px;
    }

    .event-card {
        background: #1f2937;
        border-color: #374151;
        color: #ffffff;
        min-height: 132px;
        display: grid;
        align-content: start;
        gap: 8px;
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
        font-size: 24px;
        line-height: 1;
        font-weight: 780;
    }

    .event-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-top: 4px;
    }

    .event-stat {
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 8px;
        background: #0f172a;
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
        font-size: 14px;
        font-weight: 760;
        margin-top: 4px;
    }

    .swap-grid {
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    }

    .swap-card {
        background: #111827;
        border: 1px solid #334155;
        border-left: 5px solid var(--proc-color, #64748b);
        border-radius: 8px;
        color: #ffffff;
        padding: 10px 12px;
    }

    .swap-card strong {
        color: #ffffff;
        font-size: 15px;
    }

    .completion-banner {
        display: grid;
        grid-template-columns: minmax(260px, 1.2fr) minmax(420px, 2fr);
        gap: 16px;
        align-items: center;
        border: 1px solid rgba(34, 197, 94, 0.45);
        border-left: 6px solid #22c55e;
        border-radius: 8px;
        background:
            linear-gradient(135deg, rgba(22, 101, 52, 0.42), rgba(15, 23, 42, 0.96)),
            #0f172a;
        color: #ffffff;
        padding: 18px 20px;
        margin: 18px 0 24px;
        box-shadow: 0 16px 32px rgba(0, 0, 0, 0.24);
    }

    .completion-kicker {
        color: #bbf7d0;
        font-size: 11px;
        font-weight: 760;
        letter-spacing: .06em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .completion-title {
        color: #ffffff;
        font-size: 24px;
        font-weight: 780;
        line-height: 1.1;
        margin-bottom: 6px;
    }

    .completion-subtitle {
        color: #dcfce7;
        font-size: 13px;
        line-height: 1.45;
    }

    .completion-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 8px;
    }

    .completion-stat {
        border: 1px solid rgba(187, 247, 208, 0.25);
        border-radius: 8px;
        background: rgba(15, 23, 42, 0.58);
        padding: 10px;
    }

    .completion-stat-label {
        color: #bbf7d0;
        font-size: 10px;
        font-weight: 760;
        letter-spacing: .05em;
        text-transform: uppercase;
    }

    .completion-stat-value {
        color: #ffffff;
        font-size: 18px;
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


def status_legivel(status: str) -> str:
    return {
        "executando": "Executando",
        "page_fault": "Falha de pagina",
        "sobrecarga": "Troca de contexto",
        "ocioso": "Ociosa",
        "pronto": "Pronto",
        "bloqueado_mem": "Bloqueado memoria",
        "terminado": "Terminado",
    }.get(status, status or "Ociosa")


def ordenar_pid(pid: str):
    if isinstance(pid, str) and pid.startswith("P") and pid[1:].isdigit():
        return int(pid[1:])
    return pid


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
        ("Uso CPU", f"{uso_cpu:.1f}%"),
        ("Fila pronta", fila),
        ("Bloq. memoria", bloqueados),
    ]
    if status_memoria:
        itens.extend([
            ("Falhas pagina", status_memoria.get("total_page_faults", 0)),
            ("Frames usados", f"{status_memoria.get('frames_ocupados', 0)}/{status_memoria.get('num_frames', 0)}"),
        ])
    return render_metric_grid(itens)


def render_completion_message(resultados):
    metricas = resultados.get("metricas_globais", {})
    memoria = resultados.get("status_memoria", {})
    processos_finalizados = resultados.get("processos_terminados", [])

    tempo_total = metricas.get("tempo_total_simulacao", 0)
    uso_cpu = metricas.get("utilizacao_cpu_percent", 0)
    throughput = metricas.get("throughput", 0)

    stats = [
        ("Processos", len(processos_finalizados)),
        ("Tempo total", f"{tempo_total:.0f} u.t."),
        ("Uso da CPU", f"{uso_cpu:.2f}%"),
        ("Throughput", f"{throughput:.4f}"),
    ]

    if memoria:
        stats.extend([
            ("Acertos", memoria.get("total_page_hits", 0)),
            ("Falhas", memoria.get("total_page_faults", 0)),
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
            <div class="completion-kicker">Simulacao finalizada</div>
            <div class="completion-title">Todos os processos ativos foram concluidos.</div>
            <div class="completion-subtitle">
                A execucao terminou sem erros. Confira abaixo o Gantt final, as metricas globais e a tabela de processos.
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
        detalhe = f"Restante {processo['tempo_restante']} u.t. | deadline {processo['deadline']}"
    elif status == "page_fault" and ultima_memoria:
        pid = ultima_memoria.get("pid", "CPU")
        detalhe = (
            f"Pagina {ultima_memoria.get('pagina')} carregada "
            f"no frame {ultima_memoria.get('frame')}"
        )
    else:
        pid = "CPU"
        detalhe = "Sem processo em execucao"

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
        return '<div class="muted-empty">Fila de prontos vazia</div>'

    cards = []
    for posicao, processo in enumerate(fila, start=1):
        pid = processo["id"]
        cards.append(
            html_fragment(f"""
            <div class="process-card" style="--proc-color:{cor_processo(pid)}">
                <strong>{h(posicao)}. {h(pid)}</strong>
                <div class="process-meta">
                    <span>Rest. {h(processo['tempo_restante'])}</span>
                    <span>DL {h(processo['deadline'])}</span>
                    <span>Prio {h(processo['prioridade'])}</span>
                    <span>Pag. {h(processo['num_paginas'])}</span>
                </div>
            </div>
            """)
        )
    return html_fragment(f'<div class="queue-strip">{"".join(cards)}</div>')


def render_blocked(snapshot):
    bloqueados = snapshot.get("processos_bloqueados_memoria", [])
    if not bloqueados:
        return '<div class="muted-empty">Nenhum processo bloqueado por memoria</div>'

    cards = []
    for processo in bloqueados:
        pid = processo["id"]
        cards.append(
            html_fragment(f"""
            <div class="process-card" style="--proc-color:{cor_processo(pid)}">
                <strong>{h(pid)}</strong>
                <div class="process-meta">
                    <span>Volta em {h(processo['tempo_restante_bloqueio'])}</span>
                    <span>Pagina {h(processo.get('pagina'))}</span>
                    <span>Faults {h(processo['page_faults'])}</span>
                    <span>Rest. {h(processo['tempo_restante'])}</span>
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
            <div class="event-kicker">Acesso atual</div>
            <div class="event-status">Aguardando</div>
            <div class="event-line">Nenhuma requisicao de pagina registrada ainda</div>
        </div>
        """)

    resultado = "Falha de pagina" if evento.get("resultado") == "fault" else "Acerto de pagina"
    substituido = evento.get("substituido")
    detalhe_sub = ""
    if substituido:
        detalhe_sub = (
            f"<div class=\"event-line\">Swap: processo {h(substituido['pid'])}, "
            f"pagina {h(substituido['pagina'])}, saiu do frame {h(substituido['frame_origem'])}</div>"
        )

    return html_fragment(f"""
    <div class="event-card">
        <div class="event-kicker">Acesso atual</div>
        <div class="event-status">{h(resultado)}</div>
        <div class="event-grid">
            <div class="event-stat">
                <div class="event-stat-label">Processo</div>
                <div class="event-stat-value">{h(evento.get('pid'))}</div>
            </div>
            <div class="event-stat">
                <div class="event-stat-label">Pagina</div>
                <div class="event-stat-value">{h(evento.get('pagina'))}</div>
            </div>
            <div class="event-stat">
                <div class="event-stat-label">Frame</div>
                <div class="event-stat-value">{h(evento.get('frame'))}</div>
            </div>
        </div>
        <div class="event-line">Politica {h(evento.get('politica'))} no tick {h(evento.get('tick'))}</div>
        {detalhe_sub}
    </div>
    """)


def render_memory_summary(status_memoria):
    return html_fragment(f"""
    <div class="memory-summary">
        {render_memory_event(status_memoria)}
        <div>
            <div class="memory-block-title">Processos na RAM</div>
            {render_memory_processes(status_memoria)}
        </div>
    </div>
    """)


def render_memory_grid(status_memoria):
    frames = status_memoria.get("frames_ram", [])
    if not frames:
        return '<div class="muted-empty">Memoria desativada</div>'

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
        owner = f"Processo {pid}" if ocupado else "Livre"
        uso = f"Pagina {pagina}" if ocupado else "Disponivel"
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
        f'<div class="memory-block-title">Frames da RAM</div>'
        f'<div class="memory-grid" style="--cols:{cols}">{"".join(blocos)}</div>'
    )


def render_memory_processes(status_memoria):
    residentes = status_memoria.get("processos_residentes", [])
    if not residentes:
        return '<div class="muted-empty">Nenhum processo residente na RAM</div>'

    rows = [
        html_fragment("""
        <div class="resident-row header">
            <div>Processo</div>
            <div>Frames</div>
            <div>Paginas na RAM</div>
            <div>Frames ocupados</div>
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
                    <span>Processo {h(pid)}</span>
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
    titulo = "Swap atual" if paginas_atuais else "Historico recente de swap"

    if not paginas:
        return html_fragment("""
        <div class="memory-block-title">Swap</div>
        <div class="muted-empty">Nenhuma substituicao de pagina ocorreu ainda</div>
        """)

    cards = []
    for pagina in paginas[-8:]:
        pid = pagina["pid"]
        cards.append(
            html_fragment(f"""
            <div class="swap-card" style="--proc-color:{cor_processo(pid)}">
                <strong>Processo {h(pid)}</strong>
                <div class="event-line">Pagina {h(pagina['pagina'])} saiu do frame {h(pagina['frame_origem'])} no tick {h(pagina['tick'])}</div>
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
            "Chegada": processo["chegada"],
            "Execucao": processo["execucao"],
            "Restante": processo["tempo_restante"],
            "Deadline": processo["deadline"],
            "Prioridade": processo["prioridade"],
            "Paginas": processo["num_paginas"],
            "Hits": processo["page_hits"],
            "Faults": processo["page_faults"],
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
            erros.append("Existe processo ativo sem PID.")
            continue
        if pid in ids_usados:
            erros.append(f"PID duplicado: {pid}.")
            continue
        ids_usados.add(pid)

        try:
            chegada = int(linha["chegada"])
            execucao = int(linha["execucao"])
            deadline_relativo = int(linha["deadline"])
            prioridade = int(linha["prioridade"])
            paginas = int(linha["paginas"]) if ativar_memoria else 0
        except (TypeError, ValueError):
            erros.append(f"Valores invalidos em {pid}.")
            continue

        if chegada < 0 or execucao <= 0 or deadline_relativo <= 0 or prioridade <= 0 or paginas < 0:
            erros.append(f"Valores fora do intervalo em {pid}.")
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
        erros.append("Ative pelo menos um processo.")

    return processos, erros


st.markdown(
    html_fragment("""
    <div class="app-hero">
        <h1 class="hero-title">Simulador de Sistemas Operacionais</h1>
        <p class="hero-subtitle">Escalonamento, fila da CPU, memoria virtual paginada e eventos em tempo real em uma unica bancada de simulacao.</p>
    </div>
    """),
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("Simulacao")
    algoritmo_nome = st.selectbox("Algoritmo", ("FIFO", "SJF", "RR", "EDF", "CFS"), index=2)
    quantum = st.number_input("Quantum", min_value=1, value=2, step=1)
    sobrecarga_contexto = st.number_input("Sobrecarga de contexto", min_value=0, value=1, step=1)
    tick_delay = st.slider("Intervalo por tick", min_value=0.0, max_value=0.4, value=0.04, step=0.02)

    st.header("Memoria")
    ativar_memoria = st.checkbox("Ativar memoria virtual", value=True)
    politica_memoria = st.selectbox("Substituicao", ("FIFO", "LRU"), disabled=not ativar_memoria)
    frames_memoria = st.slider("Frames da RAM", min_value=4, max_value=NUM_FRAMES, value=12, step=1, disabled=not ativar_memoria)
    custo_disco = st.number_input("Custo do page fault", min_value=0, value=3, step=1, disabled=not ativar_memoria)
    seed_memoria = st.number_input("Seed de paginas", min_value=1, value=42, step=1, disabled=not ativar_memoria)


st.markdown('<div class="section-title">Processos</div>', unsafe_allow_html=True)
df_defaults = pd.DataFrame(DEFAULT_PROCESSOS)
df_editado = st.data_editor(
    df_defaults,
    key="processos_editor",
    hide_index=True,
    width="stretch",
    num_rows="fixed",
    disabled=["id"] if ativar_memoria else ["id", "paginas"],
    column_config={
        "ativo": st.column_config.CheckboxColumn("Ativo"),
        "id": st.column_config.TextColumn("PID"),
        "chegada": st.column_config.NumberColumn("Chegada", min_value=0, step=1),
        "execucao": st.column_config.NumberColumn("Execucao", min_value=1, step=1),
        "deadline": st.column_config.NumberColumn("Deadline relativo", min_value=1, step=1),
        "prioridade": st.column_config.NumberColumn("Prioridade", min_value=1, step=1),
        "paginas": st.column_config.NumberColumn("Paginas", min_value=0, max_value=32, step=1),
    },
)


col_run, col_hint = st.columns([0.22, 0.78])
with col_run:
    executar = st.button("Executar simulacao", type="primary", width="stretch")

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

        st.markdown('<div class="section-title">Tempo real</div>', unsafe_allow_html=True)
        live_metrics_placeholder = st.empty()

        col_cpu, col_fila = st.columns([0.34, 0.66])
        with col_cpu:
            cpu_placeholder = st.empty()
        with col_fila:
            st.markdown('<div class="panel-title">Fila de prontos da CPU</div>', unsafe_allow_html=True)
            fila_placeholder = st.empty()

        col_proc, col_bloq = st.columns([0.58, 0.42])
        with col_proc:
            st.markdown('<div class="panel-title">Estados dos processos</div>', unsafe_allow_html=True)
            processos_placeholder = st.empty()
        with col_bloq:
            st.markdown('<div class="panel-title">Bloqueados por memoria</div>', unsafe_allow_html=True)
            bloqueados_placeholder = st.empty()

        gantt_placeholder = st.empty()

        if ativar_memoria:
            st.markdown('<div class="section-title">Memoria em tempo real</div>', unsafe_allow_html=True)
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
                fig_gantt = gerar_gantt(snapshot["log_gantt"], lista_processos, "", algoritmo_nome)
                gantt_placeholder.pyplot(fig_gantt)
                plt.close(fig_gantt)

            status_memoria = snapshot.get("status_memoria", {})
            if ativar_memoria and status_memoria:
                memoria_summary_placeholder.markdown(render_memory_summary(status_memoria), unsafe_allow_html=True)
                memoria_grid_placeholder.markdown(render_memory_grid(status_memoria), unsafe_allow_html=True)
                swap_placeholder.markdown(render_swap(status_memoria), unsafe_allow_html=True)

        with st.spinner("Executando simulacao..."):
            resultados = simulador.executar(on_tick=on_tick, tick_delay=float(tick_delay))

        st.markdown(render_completion_message(resultados), unsafe_allow_html=True)

        fig_final = gerar_gantt(resultados["log_gantt"], lista_processos, "", algoritmo_nome)
        gantt_placeholder.pyplot(fig_final)
        plt.close(fig_final)

        st.markdown('<div class="section-title">Resultado final</div>', unsafe_allow_html=True)
        metricas_globais = resultados["metricas_globais"]
        status_memoria = resultados.get("status_memoria", {})
        resumo = gerar_dict_resumo(metricas_globais, resultados["processos_terminados"])
        if ativar_memoria and status_memoria:
            resumo["Politica de memoria"] = status_memoria.get("politica")
            resumo["Acertos de pagina"] = status_memoria.get("total_page_hits", 0)
            resumo["Falhas de pagina"] = status_memoria.get("total_page_faults", 0)
            resumo["Taxa de faults"] = f"{status_memoria.get('taxa_page_faults', 0):.2f}%"

        st.markdown(render_metric_grid(resumo.items()), unsafe_allow_html=True)
        st.dataframe(
            gerar_dataframe_metricas(resultados["processos_terminados"]),
            hide_index=True,
            width="stretch",
        )
