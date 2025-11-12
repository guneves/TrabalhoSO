import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Dict, Any

# Define o mapa de cores com base nos requisitos do PDF
CORES_MAP = {
    'execucao': 'green',     # [cite: 48]
    'sobrecarga': 'red',       # [cite: 50]
    'estouro': 'gray',       # [cite: 51]
    'ocioso': 'whitesmoke',   # Cor para CPU ociosa (não especificada, mas útil)
    'bloqueado_mem': 'blue'  # (Bônus) [cite: 111]
}

def gerar_gantt(log_execucao: List[Dict[str, Any]], 
                 processos_originais: List[Dict[str, Any]], 
                 caminho_saida: str, 
                 algoritmo_nome: str):
    """
    Gera e salva um gráfico de Gantt com base no log de execução do simulador.

    Argumentos:
        log_execucao: Uma lista de eventos do simulador. 
                      Formato esperado: [{'id': 'P1', 'inicio': 0, 'fim': 2, 'tipo': 'execucao'}, ...]
        processos_originais: A lista de processos do JSON (usada para pegar deadlines e IDs).
        caminho_saida: Onde salvar o arquivo .png (ex: 'out/gantt.png').
        algoritmo_nome: O nome do algoritmo (ex: 'FIFO') para o título.
    """
    
    # --- 1. Configurar Figura e Eixos ---
    fig, ax = plt.subplots(figsize=(15, 8)) # Tamanho (largura, altura) em polegadas

    # --- 2. Mapear IDs de Processos para o Eixo Y ---
    # Pega todos os IDs únicos dos processos originais
    ids_processos = sorted(list(set(p['id'] for p in processos_originais)), reverse=True)
    
    # Mapeia cada ID para uma posição Y (ex: 'P1': 0, 'P2': 1)
    y_pos = {id_proc: i for i, id_proc in enumerate(ids_processos)}
    
    # Adiciona uma "linha" para a CPU Ociosa, se houver
    if any(e['id'] == 'CPU_Ociosa' for e in log_execucao):
        y_pos['CPU_Ociosa'] = len(ids_processos)
        ids_processos.append('CPU_Ociosa') # Adiciona ao final

    # --- 3. Plotar as Barras de Execução (Eventos do Log) ---
    max_time = 0 # Para sabermos o limite do gráfico
    for evento in log_execucao:
        id_proc = evento['id']
        inicio = evento['inicio']
        fim = evento['fim']
        tipo = evento['tipo']
        
        if fim > max_time:
            max_time = fim
        
        # Ignora eventos com duração zero (podem ocorrer em preempções)
        if fim <= inicio:
            continue
            
        duracao = fim - inicio
        
        # Pega a posição Y e a cor correspondente
        if id_proc in y_pos:
            pos_y_atual = y_pos[id_proc]
            cor = CORES_MAP.get(tipo, 'black') # 'black' se for um tipo desconhecido
            
            # Desenha a barra horizontal
            ax.barh(
                y=pos_y_atual,     # Posição Y (qual processo)
                width=duracao,     # Comprimento da barra (duração)
                left=inicio,       # Onde a barra começa (tempo)
                height=0.7,        # Espessura da barra
                color=cor,
                edgecolor='black', # Contorno da barra
                linewidth=0.5
            )

    # --- 4. Plotar as Linhas de Deadline ---
    for proc in processos_originais:
        if 'deadline' in proc and proc['id'] in y_pos:
            deadline = proc['deadline']
            pos_y_deadline = y_pos[proc['id']]
            
            # [cite_start]Desenha uma linha vertical tracejada vermelha [cite: 52]
            ax.vlines(
                x=deadline, 
                ymin=pos_y_deadline - 0.4, 
                ymax=pos_y_deadline + 0.4, 
                colors='red', 
                linestyles='dashed', 
                lw=2,
                label='Deadline Absoluto' if 'deadline' not in ax.get_legend_handles_labels()[1] else ""
            )

    # --- 5. Configurar Legenda e Rótulos ---
    
    # Cria "patches" (amostras de cor) para a legenda
    legend_patches = [
        [cite_start]mpatches.Patch(color='green', label='Execução'),         # [cite: 48]
        [cite_start]mpatches.Patch(color='red', label='Sobrecarga'),         # [cite: 50]
        [cite_start]mpatches.Patch(color='gray', label='Estouro de Deadline'), # [cite: 51]
        mpatches.Patch(color='whitesmoke', label='CPU Ociosa', edgecolor='gray'),
    ]
    # Adiciona a linha de deadline à legenda
    legend_handles = [
        *legend_patches,
        [cite_start]plt.Line2D([0], [0], color='red', linestyle='dashed', lw=2, label='Deadline') # [cite: 52]
    ]

    ax.legend(handles=legend_handles, loc='upper right', fontsize='small')

    # --- 6. Formatar o Gráfico ---
    ax.set_title(f"Gráfico de Gantt - Algoritmo: {algoritmo_nome}", fontsize=16)
    
    # Configura o eixo Y (Processos)
    ax.set_yticks(ticks=list(y_pos.values()))
    ax.set_yticklabels(labels=list(y_pos.keys()))
    ax.set_ylabel("Processos", fontsize=12)
    
    # Configura o eixo X (Tempo)
    ax.set_xlabel("Tempo (unidade de tempo)", fontsize=12)
    ax.set_xlim(0, max_time * 1.05) # Limite X um pouco além do tempo final
    ax.grid(True, axis='x', linestyle='--', alpha=0.7) # Grade vertical
    
    # Inverte o eixo Y para que P1 (ou o de menor ID) fique no topo
    ax.invert_yaxis() 
    
    # Garante que tudo caiba na imagem
    plt.tight_layout()

    # --- 7. Salvar o Arquivo ---
    try:
        plt.savefig(caminho_saida)
    except Exception as e:
        print(f"Erro ao salvar o gráfico em '{caminho_saida}': {e}")
    finally:
        # Fecha a figura para liberar memória
        plt.close(fig)