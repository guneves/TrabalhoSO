from typing import List, Dict, Any

import pandas as pd

from .processo import Processo


def gerar_dataframe_metricas(processos_terminados: List[Processo]) -> pd.DataFrame:
    """
    Gera um DataFrame com as metricas individuais por processo.
    """
    if not processos_terminados:
        return pd.DataFrame()

    processos_ordenados = sorted(processos_terminados, key=lambda p: p.id)
    dados_metricas = []

    for processo in processos_ordenados:
        dados_metricas.append({
            "ID": processo.id,
            "Chegada": processo.chegada,
            "Execucao": processo.execucao,
            "Deadline": processo.deadline_relativo,
            "Deadline Real": processo.deadline,
            "Prioridade": processo.prioridade,
            "Inicio": processo.tempo_primeira_execucao if processo.tempo_primeira_execucao is not None else -1,
            "Termino": processo.tempo_termino if processo.tempo_termino is not None else -1,
            "Turnaround": processo.turnaround if processo.turnaround is not None else 0,
            "Espera fila": processo.tempo_espera if processo.tempo_espera is not None else 0,
            "Bloq. memoria": getattr(processo, "tempo_bloqueado_memoria", 0),
            "Nao executando": processo.tempo_total_nao_executando if processo.tempo_total_nao_executando is not None else 0,
            "Page Hits": getattr(processo, "page_hits", 0),
            "Page Faults": getattr(processo, "page_faults", 0),
            "Deadline OK": "Sim" if processo.deadline_ok else "Nao",
        })

    return pd.DataFrame(dados_metricas)


def gerar_dict_resumo(
    metricas_globais: Dict[str, Any],
    processos_terminados: List[Processo],
) -> Dict[str, Any]:
    """
    Gera um dicionario com as metricas globais do simulador.
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
        "Tempo total": f"{tempo_total:.2f} u.t.",
        "Tempo ocioso da CPU": f"{tempo_ocioso:.2f} u.t.",
        "Tempo em sobrecarga": f"{tempo_sobrecarga:.2f} u.t.",
        "Bloqueio memoria acumulado": f"{tempo_bloqueio_mem:.2f} u.t.",
        "Ticks com page fault": f"{tempo_page_fault_cpu:.2f} u.t.",
        "Trocas de contexto": total_trocas_contexto,
        "Preempcoes": total_preempcoes,
        "Throughput": f"{throughput:.4f} processos/u.t.",
        "Uso da CPU": f"{uso_cpu:.2f}%",
        "Ociosidade da CPU": f"{percent_ociosidade:.2f}%",
        "Turnaround medio": f"{media_turnaround:.2f} u.t.",
        "Espera media na fila": f"{media_espera:.2f} u.t.",
    }
