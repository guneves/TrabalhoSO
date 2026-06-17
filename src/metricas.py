from typing import List, Dict, Any

import pandas as pd

from .processo import Processo


def gerar_dataframe_metricas(processos_terminados: List[Processo]) -> pd.DataFrame:
    """
    Builds a DataFrame with per-process metrics.
    """
    if not processos_terminados:
        return pd.DataFrame()

    processos_ordenados = sorted(processos_terminados, key=lambda p: p.id)
    dados_metricas = []

    for processo in processos_ordenados:
        dados_metricas.append({
            "ID": processo.id,
            "Arrival": processo.chegada,
            "CPU time": processo.execucao,
            "Deadline": processo.deadline_relativo,
            "Absolute deadline": processo.deadline,
            "Priority": processo.prioridade,
            "Start": processo.tempo_primeira_execucao if processo.tempo_primeira_execucao is not None else -1,
            "Finish": processo.tempo_termino if processo.tempo_termino is not None else -1,
            "Turnaround": processo.turnaround if processo.turnaround is not None else 0,
            "CPU queue wait": processo.tempo_espera if processo.tempo_espera is not None else 0,
            "Memory block time": getattr(processo, "tempo_bloqueado_memoria", 0),
            "Off-CPU time": processo.tempo_total_nao_executando if processo.tempo_total_nao_executando is not None else 0,
            "Page Hits": getattr(processo, "page_hits", 0),
            "Page Faults": getattr(processo, "page_faults", 0),
            "Deadline met": "Yes" if processo.deadline_ok else "No",
        })

    return pd.DataFrame(dados_metricas)


def gerar_dict_resumo(
    metricas_globais: Dict[str, Any],
    processos_terminados: List[Processo],
) -> Dict[str, Any]:
    """
    Builds a dictionary with global simulator metrics.
    """
    tempo_total = metricas_globais.get("tempo_total_simulacao", 0)
    tempo_ocioso = metricas_globais.get("tempo_total_ocioso", 0)
    tempo_sobrecarga = metricas_globais.get("tempo_total_sobrecarga", 0)
    tempo_bloqueio_mem = metricas_globais.get("tempo_total_bloqueio_mem", 0)
    tempo_page_fault_cpu = metricas_globais.get("tempo_total_page_fault_cpu", 0)
    total_trocas_contexto = metricas_globais.get("total_trocas_contexto", 0)
    total_preempcoes = metricas_globais.get("total_preempcoes", 0)
    throughput = metricas_globais.get("throughput", 0)
    uso_cpu = metricas_globais.get("utilizacao_cpu_percent", 0)
    percent_ociosidade = metricas_globais.get("ociosidade_cpu_percent", 0)

    num_processos = len(processos_terminados)
    media_turnaround = 0
    media_espera = 0

    if num_processos > 0:
        soma_turnaround = sum(
            processo.turnaround if processo.turnaround is not None else 0
            for processo in processos_terminados
        )
        soma_espera = sum(
            processo.tempo_espera if processo.tempo_espera is not None else 0
            for processo in processos_terminados
        )
        media_turnaround = soma_turnaround / num_processos
        media_espera = soma_espera / num_processos

    return {
        "Total time": f"{tempo_total:.2f} t.u.",
        "CPU idle time": f"{tempo_ocioso:.2f} t.u.",
        "Total overhead": f"{tempo_sobrecarga:.2f} t.u.",
        "Memory block time": f"{tempo_bloqueio_mem:.2f} t.u.",
        "Page Fault ticks": f"{tempo_page_fault_cpu:.2f} t.u.",
        "Context switches": total_trocas_contexto,
        "Preemptions": total_preempcoes,
        "Throughput": f"{throughput:.4f} processes/t.u.",
        "CPU usage": f"{uso_cpu:.2f}%",
        "CPU idle rate": f"{percent_ociosidade:.2f}%",
        "Average turnaround": f"{media_turnaround:.2f} t.u.",
        "Average CPU queue wait": f"{media_espera:.2f} t.u.",
    }
