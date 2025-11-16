import pandas as pd
from typing import List, Dict, Any
import sys

try:
    from .processo import Processo
except ImportError:
    try:
        from processo import Processo
    except ImportError:
        print("Aviso: Classe 'Processo' não encontrada.", file=sys.stderr)
        class Processo: pass 

def gerar_dataframe_metricas(processos_terminados: List[Processo]) -> pd.DataFrame:
    """
    Gera um DataFrame Pandas com as métricas individuais por processo.
    """
    if not processos_terminados:
        return pd.DataFrame() 
        
    processos_terminados.sort(key=lambda p: p.id)

    dados_metricas = []

    for p in processos_terminados:
        
        turnaround = (p.turnaround if p.turnaround is not None else 0) + 1
        espera = p.tempo_espera if p.tempo_espera is not None else 0
        deadline_ok_str = "Sim" if p.deadline_ok else "Não"
        inicio = p.tempo_primeira_execucao if p.tempo_primeira_execucao is not None else -1
        
        dados_metricas.append({
            'ID': p.id,
            'Chegada': p.chegada,
            'Execução': p.execucao,
            
            'Deadline': p.deadline_relativo,
            'Deadline (Real)': p.deadline,
            
            'Priorid.': p.prioridade,
            'Início': inicio,
            'Término': p.tempo_termino + 1,
            'Turnaround': turnaround,
            'Espera': espera,
            'D. OK?': deadline_ok_str
        })
    
    colunas = ['ID', 'Chegada', 'Execução', 'Deadline', 'Deadline (Real)', 'Priorid.', 
               'Início', 'Término', 'Turnaround', 'Espera', 'D. OK?']
    return pd.DataFrame(dados_metricas, columns=colunas)

def gerar_dict_resumo(
    metricas_globais: Dict[str, Any],
    processos_terminados: List[Processo]
) -> Dict[str, Any]:
    """
    Gera um dicionário com as métricas globais do simulador.
    """
    
    tempo_total = metricas_globais.get("tempo_total_simulacao", 0)
    tempo_ocioso = metricas_globais.get("tempo_total_ocioso", 0)
    total_trocas_contexto = metricas_globais.get("total_trocas_contexto", 0)
    throughput = metricas_globais.get("throughput", 0)
    percent_ociosidade = metricas_globais.get("ociosidade_cpu_percent", 0)
    
    
    num_processos = len(processos_terminados)
    media_turnaround = 0
    media_espera = 0

    if num_processos > 0:
        soma_turnaround = sum((p.turnaround if p.turnaround is not None else 0) + 1 for p in processos_terminados)
        soma_espera = sum(p.tempo_espera if p.tempo_espera is not None else 0 for p in processos_terminados)
            
        media_turnaround = soma_turnaround / num_processos
        media_espera = soma_espera / num_processos

    resumo = {
        "Tempo Total de Simulação": f"{tempo_total:.2f} u.t.",
        "Tempo Total de Ociosidade": f"{tempo_ocioso:.2f} u.t.",
        "Total de Trocas de Contexto": total_trocas_contexto,
        "Taxa de Throughput": f"{throughput:.4f} processos/u.t.",
        "% de Ociosidade da CPU": f"{percent_ociosidade:.2f}%",
        "Tempo Médio de Turnaround": f"{media_turnaround:.2f} u.t.", 
        "Tempo Médio de Espera": f"{media_espera:.2f} u.t."
    }
    
    return resumo