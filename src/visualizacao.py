# visualizacao.py
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Dict, Any
import math

from .processo import Processo

CORES_MAP = {
    'execucao': 'green',     
    'sobrecarga': 'red',       
    'estouro': 'gray',       
    'ocioso': 'whitesmoke',   
    'bloqueado_mem': 'blue', 
    'esperando': '#FFBF00' 
}

# Constantes para visualização de memória
FRAMES_POR_LINHA = 8 
NUM_FRAMES = 50 


def _converter_log_ticks_para_eventos(log_ticks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Função-ponte para converter o log de ticks do simulador
    em um log de eventos agrupados.
    """
    if not log_ticks:
        return []

    eventos_agrupados = []
    evento_atual = None

    for tick_info in log_ticks:
        tick = tick_info['tick']
        id_proc = tick_info['id']
        status = tick_info['status']
        
        # Mapeamento de status para tipo de evento
        if status in ['executando', 'bloqueado_mem']:
            tipo = 'execucao' if status == 'executando' else 'bloqueado_mem'
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
                 caminho_saida: str,  
                 algoritmo_nome: str):
    """
    Gera um gráfico de Gantt e RETORNA o objeto 'figura' do Matplotlib.
    """
    
    eventos_agrupados = _converter_log_ticks_para_eventos(log_ticks)
    if not eventos_agrupados:
        print("Aviso: Nenhum evento para plotar no gráfico de Gantt.")
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

            # Lógica para cor de Estouros de Deadline
            if tipo == 'execucao' and \
               id_proc in processos_map and \
               processos_map[id_proc].deadline_ok is False:
                pass 

            ax.barh(y=pos_y_atual, width=duracao, left=inicio, height=0.7,
                    color=cor, edgecolor='black', linewidth=0.5)

    for proc in processos_terminados:
        if proc.deadline is not None and proc.id in y_pos:
            deadline = proc.deadline
            pos_y_deadline = y_pos[proc.id]
            
            # Linha vertical para o deadline
            ax.vlines(x=deadline, ymin=pos_y_deadline - 0.4, ymax=pos_y_deadline + 0.4, 
                      colors='red', linestyles='dashed', lw=2,
                      label='Deadline' if 'deadline' not in ax.get_legend_handles_labels()[1] else "")

    legend_patches = [
        mpatches.Patch(color=CORES_MAP['execucao'], label='Execução'),
        mpatches.Patch(color=CORES_MAP['sobrecarga'], label='Sobrecarga'),
        mpatches.Patch(color=CORES_MAP['ocioso'], label='CPU Ociosa', edgecolor='gray'),
        mpatches.Patch(color=CORES_MAP['bloqueado_mem'], label='Bloqueio (Page Fault)'), 
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

def gerar_visualizacao_memoria_ram(status_memoria: Dict[str, Any]):
    """
    Gera uma representação visual do estado da RAM (Matriz de Frames).
    """
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_title(f"Memória RAM ({NUM_FRAMES} Frames)")
    ax.axis('off')

    frames_data = status_memoria['frames_ram']
    
    rows = math.ceil(NUM_FRAMES / FRAMES_POR_LINHA)
    cols = FRAMES_POR_LINHA
    
    # Desenha os frames
    for i, frame in enumerate(frames_data):
        row = i // cols
        col = i % cols
        
        # Posição do retângulo do frame
        rect = plt.Rectangle((col, rows - 1 - row), 1, 1, 
                             fill=True, 
                             edgecolor='black', 
                             linewidth=1)
                             
        if frame['ocupado']:
            # Cor com base no PID
            pid_hash = sum(ord(c) for c in frame['processo_id'])
            cor = plt.cm.get_cmap('tab10')(pid_hash % 10)
            rect.set_color(cor)
            
            # Texto (Frame Index e PID:Página)
            text = f"F{frame['indice']}\n{frame['processo_id']}:p{frame['pagina_num']}"
            ax.text(col + 0.5, rows - 1 - row + 0.5, text, 
                    ha='center', va='center', fontsize=8, color='black', weight='bold')
        else:
            rect.set_color('lightgray')
            ax.text(col + 0.5, rows - 1 - row + 0.5, f"F{frame['indice']}\nLivre", 
                    ha='center', va='center', fontsize=8, color='darkgray')

        ax.add_patch(rect)
        
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect('equal', adjustable='box')
    
    return fig

def gerar_visualizacao_disco():
    """
    Gera uma representação simbólica do Disco.
    """
    fig, ax = plt.subplots(figsize=(4, 5))
    ax.set_title("Disco Rígido (Swapping)")
    ax.axis('off')
    
    # Desenha o cilindro do disco
    # Fundo do cilindro
    disk_color = '#e0e0e0'
    ax.add_patch(mpatches.Ellipse((0.5, 0.8), 0.7, 0.2, color=disk_color, edgecolor='black', linewidth=1))
    # Lateral do cilindro
    ax.plot([0.15, 0.15], [0.8, 0.2], color='black', linewidth=1)
    ax.plot([0.85, 0.85], [0.8, 0.2], color='black', linewidth=1)
    # Frente do cilindro
    ax.add_patch(mpatches.Ellipse((0.5, 0.2), 0.7, 0.2, color=disk_color, edgecolor='black', linewidth=1))
    
    ax.text(0.5, 0.5, "Páginas\nSwap", ha='center', va='center', fontsize=12, color='darkred', weight='bold')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    return fig


def gerar_visualizacao_tabela_invertida(status_memoria: Dict[str, Any]):
    """
    Gera uma representação visual da Tabela de Páginas Invertida.
    """
    fig, ax = plt.subplots(figsize=(4, 8))
    ax.set_title("Tabela de Páginas Invertida\n(Frame -> PID:Página)", fontsize=10)
    ax.axis('off')

    tabela_dados = status_memoria['tabela_invertida']
    
    # Configuração da tabela visual
    headers = ["Frame", "PID:Página", "Valid/Inv"]
    cell_text = []
    
    # Cria uma lista de mapeamentos ordenados por Frame Index
    mapeamentos = {}
    for item in tabela_dados:
        # Usa um formato conciso para caber na tabela
        mapeamentos[item['frame']] = f"{item['pid']}:p{item['pagina']}" 
    
    # Obtém todos os frames ocupados e livres até o NUM_FRAMES
    all_frames = []
    for i in range(NUM_FRAMES):
        pid_page = mapeamentos.get(i, "Livre")
        bit = 'V' if pid_page != "Livre" else 'I'
        all_frames.append([str(i), pid_page, bit])

    # Limitar a exibição para clareza (exibir os 12 primeiros)
    frames_a_exibir = 12 
    cell_text_exibir = all_frames[:frames_a_exibir]
    
    # Adicionar reticências se houver mais frames
    if NUM_FRAMES > frames_a_exibir:
        cell_text_exibir.append(["...", "...", "..."])
        cell_colors = [['w'] * 3] * frames_a_exibir + [['lightgray'] * 3]
    else:
        cell_colors = [['w'] * 3] * frames_a_exibir
        
    # Coloração: frames ocupados em cinza claro para destacar
    for i, row in enumerate(cell_text_exibir):
        if row[2] == 'V':
            # Cor azul muito claro para frame ocupado
            cell_colors[i] = ['#e6e6ff'] * 3
            
    # Cria a tabela no Matplotlib
    tabela = ax.table(cellText=cell_text_exibir, colLabels=headers, 
                      loc='center', cellLoc='center', 
                      colWidths=[0.3, 0.4, 0.3],
                      cellColours=cell_colors)

    tabela.auto_set_font_size(False)
    tabela.set_fontsize(10)
    tabela.scale(1, 1.2)
    
    # [LINHAS REMOVIDAS] Anteriormente, o código tentava usar:
    # for key, cell in tabela.get_celld().items():
    #     if key[1] == 2: # Coluna Valid/Invalid
    #         cell.set_fontweight('bold') 
    
    return fig