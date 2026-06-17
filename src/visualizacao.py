from collections import defaultdict
from typing import List, Dict, Any
import math

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from .processo import Processo


CORES_MAP = {
    "execucao": "#22c55e",
    "executando": "#22c55e",
    "sobrecarga": "#ef4444",
    "ocioso": "#64748b",
    "bloqueado_mem": "#3b82f6",
    "esperando": "#f59e0b",
}

GANTT_STATUS_STYLE = {
    "esperando": {"height": 0.18, "offset": 0.24, "alpha": 0.82, "zorder": 3},
    "bloqueado_mem": {"height": 0.18, "offset": -0.24, "alpha": 0.88, "zorder": 3},
    "execucao": {"height": 0.48, "offset": 0.0, "alpha": 1.0, "zorder": 4},
    "sobrecarga": {"height": 0.48, "offset": 0.0, "alpha": 1.0, "zorder": 4},
    "ocioso": {"height": 0.48, "offset": 0.0, "alpha": 0.72, "zorder": 4},
}

FRAMES_POR_LINHA = 8


def _ordenar_pid(pid: str):
    if pid.startswith("P") and pid[1:].isdigit():
        return int(pid[1:])
    if pid == "CPU":
        return 10_000
    return pid


def _converter_log_ticks_para_eventos(log_ticks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not log_ticks:
        return []

    timeline_por_id = defaultdict(list)
    for tick_info in log_ticks:
        tipo = "execucao" if tick_info["status"] == "executando" else tick_info["status"]
        timeline_por_id[tick_info["id"]].append((tick_info["tick"], tipo))

    eventos = []
    for id_proc, timeline in timeline_por_id.items():
        timeline.sort(key=lambda item: item[0])
        inicio, tipo_atual = timeline[0]
        tick_anterior = inicio

        for tick, tipo in timeline[1:]:
            if tipo != tipo_atual or tick != tick_anterior + 1:
                eventos.append({
                    "id": id_proc,
                    "tipo": tipo_atual,
                    "inicio": inicio,
                    "fim": tick_anterior + 1,
                })
                inicio = tick
                tipo_atual = tipo
            tick_anterior = tick

        eventos.append({
            "id": id_proc,
            "tipo": tipo_atual,
            "inicio": inicio,
            "fim": tick_anterior + 1,
        })

    return eventos


def gerar_gantt(
    log_ticks: List[Dict[str, Any]],
    processos_terminados: List[Processo],
    caminho_saida: str,
    algoritmo_nome: str,
):
    eventos = _converter_log_ticks_para_eventos(log_ticks)
    fig_height = 2.4 + max(1, len({e["id"] for e in eventos})) * 0.62
    fig, ax = plt.subplots(figsize=(16, fig_height), constrained_layout=False)
    fig.patch.set_facecolor("#090d18")
    ax.set_facecolor("#0f172a")

    if not eventos:
        ax.text(0.5, 0.5, "No data to display.", ha="center", va="center", color="#e2e8f0")
        ax.axis("off")
        return fig

    ids = sorted({p.id for p in processos_terminados} | {e["id"] for e in eventos}, key=_ordenar_pid)
    y_pos = {pid: idx for idx, pid in enumerate(ids)}

    max_time = max(evento["fim"] for evento in eventos)
    limite_x = max(1, max_time)

    for idx, pid in enumerate(ids):
        ax.barh(
            y=idx,
            width=limite_x,
            left=0,
            height=0.78,
            color="#111827" if idx % 2 == 0 else "#0b1220",
            edgecolor="#253044",
            linewidth=0.6,
            zorder=1,
        )

    eventos_ordenados = sorted(
        eventos,
        key=lambda item: {"esperando": 0, "bloqueado_mem": 1, "ocioso": 2, "sobrecarga": 3, "execucao": 4}.get(item["tipo"], 0),
    )

    for evento in eventos_ordenados:
        inicio = evento["inicio"]
        fim = evento["fim"]
        duracao = fim - inicio
        if duracao <= 0:
            continue

        tipo = evento["tipo"]
        estilo = GANTT_STATUS_STYLE.get(tipo, {"height": 0.42, "offset": 0.0, "alpha": 1.0, "zorder": 4})
        if evento["id"] == "CPU":
            estilo = {**estilo, "height": 0.50, "offset": 0.0}

        ax.barh(
            y=y_pos[evento["id"]] + estilo["offset"],
            width=duracao,
            left=inicio,
            height=estilo["height"],
            color=CORES_MAP.get(tipo, "#e2e8f0"),
            edgecolor="#020617",
            linewidth=0.5,
            alpha=estilo["alpha"],
            zorder=estilo["zorder"],
        )

    for processo in processos_terminados:
        if processo.deadline is None or processo.id not in y_pos:
            continue
        ax.vlines(
            x=processo.deadline,
            ymin=y_pos[processo.id] - 0.42,
            ymax=y_pos[processo.id] + 0.42,
            colors="#f97316",
            linestyles="dashed",
            lw=1.8,
            zorder=5,
        )
        ax.text(
            processo.deadline,
            y_pos[processo.id] - 0.47,
            "D",
            color="#fed7aa",
            fontsize=8,
            ha="center",
            va="bottom",
            fontweight="bold",
            zorder=6,
        )

    legend_handles = [
        mpatches.Patch(color=CORES_MAP["execucao"], label="Running"),
        mpatches.Patch(color=CORES_MAP["esperando"], label="CPU queue"),
        mpatches.Patch(color=CORES_MAP["bloqueado_mem"], label="Memory blocked"),
        mpatches.Patch(color=CORES_MAP["sobrecarga"], label="Context switch"),
        mpatches.Patch(color=CORES_MAP["ocioso"], label="CPU idle"),
        plt.Line2D([0], [0], color="#f97316", linestyle="dashed", lw=1.8, label="Deadline"),
    ]
    legenda = ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=6,
        fontsize=9,
        frameon=False,
    )
    for texto in legenda.get_texts():
        texto.set_color("#e2e8f0")

    ax.set_title(f"Timeline - {algoritmo_nome}", fontsize=16, pad=16, color="#f8fafc", fontweight="bold")
    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(list(y_pos.keys()), color="#e2e8f0", fontweight="bold")
    ax.set_xlabel("Time (t.u.)", color="#cbd5e1", labelpad=10)
    ax.set_xlim(0, max(1, max_time * 1.03))
    ax.grid(True, axis="x", linestyle="--", alpha=0.18, color="#94a3b8", zorder=0)
    ax.tick_params(axis="x", colors="#cbd5e1")
    ax.tick_params(axis="y", colors="#e2e8f0", length=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#475569")
    ax.margins(y=0.08)
    ax.invert_yaxis()
    fig.subplots_adjust(left=0.06, right=0.985, top=0.86, bottom=0.22)
    return fig


def gerar_visualizacao_memoria_ram(status_memoria: Dict[str, Any]):
    frames = status_memoria.get("frames_ram", [])
    num_frames = status_memoria.get("num_frames", len(frames))
    rows = max(1, math.ceil(max(1, num_frames) / FRAMES_POR_LINHA))
    cols = FRAMES_POR_LINHA

    fig, ax = plt.subplots(figsize=(8, max(3, rows * 0.9)))
    ax.set_title(f"RAM ({num_frames} frames)")
    ax.axis("off")

    for i, frame in enumerate(frames):
        row = i // cols
        col = i % cols
        y = rows - 1 - row
        ocupado = frame.get("ocupado")
        pid = frame.get("processo_id")
        pagina = frame.get("pagina_num")

        if ocupado:
            pid_hash = sum(ord(char) for char in str(pid))
            cor = plt.cm.get_cmap("tab20")(pid_hash % 20)
            texto = f"Frame {frame['indice']}\nProcess {pid}\nPage {pagina}"
        else:
            cor = "#e5e7eb"
            texto = f"Frame {frame['indice']}\nFree"

        ax.add_patch(plt.Rectangle((col, y), 1, 1, color=cor, ec="#111827", lw=0.7))
        ax.text(col + 0.5, y + 0.5, texto, ha="center", va="center", fontsize=7, color="#ffffff", weight="bold")

    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect("equal", adjustable="box")
    return fig


def gerar_visualizacao_disco(status_memoria: Dict[str, Any] | None = None):
    status_memoria = status_memoria or {}
    paginas = status_memoria.get("paginas_disco", []) or status_memoria.get("historico_swap", [])

    fig, ax = plt.subplots(figsize=(4, 5))
    ax.set_title("Swap")
    ax.axis("off")

    ax.add_patch(mpatches.Ellipse((0.5, 0.82), 0.7, 0.18, color="#e5e7eb", ec="#111827", lw=1))
    ax.plot([0.15, 0.15], [0.82, 0.22], color="#111827", lw=1)
    ax.plot([0.85, 0.85], [0.82, 0.22], color="#111827", lw=1)
    ax.add_patch(mpatches.Ellipse((0.5, 0.22), 0.7, 0.18, color="#d1d5db", ec="#111827", lw=1))

    texto = "No evicted pages"
    if paginas:
        recentes = paginas[-6:]
        texto = "\n".join(f"Process {p['pid']} - Page {p['pagina']}" for p in recentes)

    ax.text(0.5, 0.52, texto, ha="center", va="center", fontsize=9, weight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return fig


def gerar_visualizacao_tabela_invertida(status_memoria: Dict[str, Any]):
    num_frames = status_memoria.get("num_frames", 0)
    tabela_dados = status_memoria.get("tabela_invertida", [])
    mapeamentos = {
        item["frame"]: f"Process {item['pid']} / Page {item['pagina']}"
        for item in tabela_dados
    }

    cell_text = []
    cell_colors = []
    for frame in range(num_frames):
        pid_page = mapeamentos.get(frame, "Free")
        valido = "V" if pid_page != "Free" else "I"
        cell_text.append([str(frame), pid_page, valido])
        cell_colors.append(["#eef2ff"] * 3 if valido == "V" else ["#ffffff"] * 3)

    fig, ax = plt.subplots(figsize=(4.8, max(4, num_frames * 0.25)))
    ax.axis("off")
    tabela = ax.table(
        cellText=cell_text,
        colLabels=["Frame", "Process / Page", "Bit"],
        loc="center",
        cellLoc="center",
        colWidths=[0.25, 0.5, 0.25],
        cellColours=cell_colors,
    )
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(9)
    tabela.scale(1, 1.15)
    return fig
