import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Dict, Any

from .processo import Processo

CORES_MAP = {
    'execucao': 'green',     
    'sobrecarga': 'red',       
    'estouro': 'gray',       
    'ocioso': 'whitesmoke',   
    'bloqueado_mem': 'blue', 
    'esperando': '#FFBF00' 
}

def _converter_log_ticks_para_eventos(log_ticks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Função-ponte para converter o log de ticks do simulador
    em um log de eventos agrupados.
    
    Ex: [{'tick': 0, 'id': 'P1', 'status': 'executando'},
         {'tick': 1, 'id': 'P1', 'status': 'executando'}]
    
    Vira:
        [{'id': 'P1', 'inicio': 0, 'fim': 2, 'tipo': 'execucao'}]
    """
    if not log_ticks:
        return []

    eventos_agrupados = []
    evento_atual = None

    for tick_info in log_ticks:
        tick = tick_info['tick']
        id_proc = tick_info['id']
        status = tick_info['status']
        
        if status == 'executando':
            tipo = 'execucao'
        else:
            tipo = status 

        if evento_atual is None:
            evento_atual = {'id': id_proc, 'inicio': tick, 'tipo': tipo}
        
        elif id_proc != evento_atual['id'] or tipo != evento_atual['tipo']:
            evento_atual['fim'] = tick 
            eventos_agrupados.append(evento_atual)
            evento_atual = {'id': id_proc, 'inicio': tick, 'tipo': tipo}
            
    if evento_atual:
        evento_atual['fim'] = log_ticks[-1]['tick'] + 1
        eventos_agrupados.append(evento_atual)

    return eventos_agrupados


def gerar_gantt(log_ticks: List[Dict[str, Any]], 
                 processos_terminados: List[Processo], 
                 caminho_saida: str,  # <-- O argumento ainda existe, mas não é usado
                 algoritmo_nome: str):
    """
    Gera um gráfico de Gantt e RETORNA o objeto 'figura' do Matplotlib.

    Args:
        log_ticks: O log *tick-a-tick* vindo do 'simulador.py'.
        processos_terminados: A lista de objetos Processo finalizados.
        caminho_saida: (Ignorado nesta versão)
        algoritmo_nome: O nome do algoritmo (ex: 'FIFO') para o título.
    
    Returns:
        matplotlib.figure.Figure: O objeto da figura pronto para ser
                                  exibido pelo Streamlit (st.pyplot()).
    """
    
    eventos_agrupados = _converter_log_ticks_para_eventos(log_ticks)
    if not eventos_agrupados:
        print("Aviso: Nenhum evento para plotar no gráfico de Gantt.")
        # Retorna uma figura vazia em caso de falha
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'Nenhum dado para exibir.', horizontalalignment='center', verticalalignment='center')
        return fig

    fig, ax = plt.subplots(figsize=(15, 8))

    ids_processos = sorted(list(set(p.id for p in processos_terminados)), reverse=True)
    y_pos = {id_proc: i for i, id_proc in enumerate(ids_processos)}
    
    if any(e['id'] == 'CPU' for e in eventos_agrupados):
        y_pos['CPU'] = len(ids_processos)
        ids_processos.append('CPU')

    processos_map = {p.id: p for p in processos_terminados}

    max_time = 0
    for evento in eventos_agrupados:
        id_proc = evento['id']
        inicio = evento['inicio']
        fim = evento['fim']
        tipo = evento['tipo']
        
        if fim > max_time:
            max_time = fim
            
        duracao = fim - inicio
        if duracao <= 0:
            continue
            
        if id_proc in y_pos:
            pos_y_atual = y_pos[id_proc]
            cor = CORES_MAP.get(tipo, 'black') 

            if tipo == 'execucao' and \
               algoritmo_nome == 'EDF' and \
               id_proc in processos_map and \
               processos_map[id_proc].deadline_ok is False:
                
                cor = CORES_MAP['estouro']

            ax.barh(y=pos_y_atual, width=duracao, left=inicio, height=0.7,
                    color=cor, edgecolor='black', linewidth=0.5)

    for proc in processos_terminados:
        if proc.deadline is not None and proc.id in y_pos:
            deadline = proc.deadline
            pos_y_deadline = y_pos[proc.id]
            
            ax.vlines(x=deadline, ymin=pos_y_deadline - 0.4, ymax=pos_y_deadline + 0.4, 
                      colors='red', linestyles='dashed', lw=2,
                      label='Deadline' if 'deadline' not in ax.get_legend_handles_labels()[1] else "")

    legend_patches = [
        mpatches.Patch(color=CORES_MAP['execucao'], label='Execução'),
        mpatches.Patch(color=CORES_MAP['sobrecarga'], label='Sobrecarga'),
        mpatches.Patch(color=CORES_MAP['estouro'], label='Estouro de Deadline'),
        mpatches.Patch(color=CORES_MAP['ocioso'], label='CPU Ociosa', edgecolor='gray'),
        mpatches.Patch(color=CORES_MAP['esperando'], label='Em espera', edgecolor="#ff9900"),
    ]
    legend_handles = [
        *legend_patches,
        plt.Line2D([0], [0], color='red', linestyle='dashed', lw=2, label='Deadline')
    ]
    ax.legend(handles=legend_handles, loc='upper right', fontsize='small')

    ax.set_title(f"Gráfico de Gantt - Algoritmo: {algoritmo_nome}", fontsize=16)
    
    ax.set_yticks(ticks=list(y_pos.values()))
    ax.set_yticklabels(labels=list(y_pos.keys()))
    ax.set_ylabel("Processos", fontsize=12)
    
    ax.set_xlabel("Tempo (unidade de tempo)", fontsize=12)
    ax.set_xlim(0, max_time * 1.05)
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)
    
    ax.invert_yaxis() 
    plt.tight_layout()

    return fig