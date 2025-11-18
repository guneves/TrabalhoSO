# app.py
import streamlit as st
import sys
import os

DIRETORIO_ATUAL = os.path.dirname(__file__)
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, '..'))
sys.path.append(DIRETORIO_RAIZ)

try:
    from src.processo import Processo
    from src.simulador import Simulador
    from src.escalonadores import (
        EscalonadorBase,
        EscalonadorFIFO,
        EscalonadorSJF,
        EscalonadorRoundRobin,
        EscalonadorEDF,
        EscalonadorCFSSim
    )
    # Importa as novas funções de visualização
    from src.visualizacao import (
        gerar_gantt, 
        gerar_visualizacao_memoria_ram, 
        gerar_visualizacao_tabela_invertida,
        gerar_visualizacao_disco # <-- Adicionado
    ) 
    from src.metricas import gerar_dataframe_metricas, gerar_dict_resumo
    from src.memoria import GerenciadorMemoria 

except ImportError as e:
    st.error(f"Erro ao importar módulos do 'src': {e}")
    st.error("Verifique se a estrutura de pastas está correta e se 'src/__init__.py' existe.")
    st.stop()


st.set_page_config(layout="wide")
st.title('Simulador de Escalonamento de Processos')

st.subheader('Configurações Globais da Simulação')

col_alg, col_q, col_s = st.columns(3)

with col_alg:
    algoritmo_nome = st.selectbox(
        'Escolha o Algoritmo:',
        ('FIFO', 'SJF', 'RR', 'EDF', 'CFS')
    )

with col_q:
    quantum = st.number_input(
        'Quantum (u.t.)', 
        min_value=1, 
        value=2,
        help="Usado por todos os algoritmos preemptivos (RR, EDF, CFS)."
    )

with col_s:
    sobrecarga_contexto = st.number_input(
        'Sobrecarga de Contexto (u.t.)', 
        min_value=0, 
        value=1,
        help="Custo aplicado em cada preempção."
    )

st.markdown("---")

# --- BÔNUS: CONFIGURAÇÕES DE MEMÓRIA VIRTUAL ---
st.subheader('Configurações de Memória Virtual (Bônus)')
col_mem_ativar, col_mem_politica, col_mem_custo, col_mem_seed = st.columns(4)

with col_mem_ativar:
    ativar_memoria = st.checkbox('Ativar Gerência de Memória Virtual', value=False)
    
with col_mem_politica:
    politica_memoria = st.selectbox(
        'Política de Substituição:',
        ('FIFO', 'LRU'),
        disabled=not ativar_memoria
    )
    
with col_mem_custo:
    custo_disco = st.number_input(
        'Custo de Page Fault (u.t.)', 
        min_value=0, 
        value=3,
        help="Custo aplicado quando ocorre um Page Fault (custo_disco no PDF).",
        disabled=not ativar_memoria
    )
    
with col_mem_seed:
    seed_memoria = st.number_input(
        'Seed para Sorteio de Páginas', 
        min_value=1, 
        value=42,
        help="Garante determinismo na requisição de páginas.",
        disabled=not ativar_memoria
    )
    
st.markdown("---")


st.subheader('Definição dos Processos')

processos_input = []
num_processos = 6 

tab_nomes = [f'Processo {i+1}' for i in range(num_processos)]
tabs = st.tabs(tab_nomes)

# Defaults com 'num_paginas'
defaults = [
   {'chegada': 0, 'execucao': 4, 'deadline': 7, 'prioridade': 2, 'num_paginas': 6}, # P1
   {'chegada': 2, 'execucao': 2, 'deadline': 5, 'prioridade': 1, 'num_paginas': 4}, # P2
   {'chegada': 4, 'execucao': 1, 'deadline': 8, 'prioridade': 3, 'num_paginas': 3}, # P3
   {'chegada': 6, 'execucao': 3, 'deadline': 10, 'prioridade': 1, 'num_paginas': 5}, # P4
   {'chegada': 8, 'execucao': 3, 'deadline': 15, 'prioridade': 2, 'num_paginas': 2}, # P5
   {'chegada': 10, 'execucao': 4, 'deadline': 25, 'prioridade': 3, 'num_paginas': 7}, # P6
]

for i, tab in enumerate(tabs):
    with tab:
        id_proc = f'P{i+1}'
        
        ativar_processo = st.checkbox(
            f'Ativar Processo {id_proc}', 
            value=(i < 3)
        )
        
        col1, col2, col3, col4, col5 = st.columns(5) # 5 colunas agora
        
        default_val = defaults[i] if i < len(defaults) else {'chegada': i*2, 'execucao': 5, 'deadline': 20, 'prioridade': 1, 'num_paginas': 0}
        
        chegada = col1.number_input(f'Tempo de Chegada ({id_proc})', 
                                    min_value=0, value=default_val['chegada'], key=f'ch_{i}')
        execucao = col2.number_input(f'Tempo de Execução ({id_proc})', 
                                     min_value=1, value=default_val['execucao'], key=f'ex_{i}')
        deadline = col3.number_input(f'Deadline (Relativo) ({id_proc})', 
                                      min_value=1, value=default_val['deadline'], key=f'dl_{i}')
        prioridade = col4.number_input(f'Prioridade ({id_proc})', 
                                        min_value=1, value=default_val['prioridade'], key=f'pr_{i}')
        
        num_paginas = col5.number_input(f'Nº Páginas (0-10) ({id_proc})', 
                                        min_value=0, max_value=10, 
                                        value=default_val['num_paginas'] if ativar_memoria else 0, 
                                        key=f'np_{i}', disabled=not ativar_memoria)
        
        if ativar_processo:
            processos_input.append({
                'id': id_proc,
                'chegada': chegada,
                'execucao': execucao,
                'deadline': chegada + deadline,
                'deadline_relativo': deadline,
                'prioridade': prioridade,
                'num_paginas': num_paginas
            })

st.markdown("---")

st.subheader('Executar Simulação e Ver Resultados')

if st.button('Executar Simulação', type="primary"):
    
    if not processos_input:
        st.error("Erro: Nenhum processo foi ativado. Por favor, ative pelo menos um processo.")
    else:
        with st.spinner('Simulando...'):
            try:
                lista_processos = [Processo(**p) for p in processos_input]
                
                algoritmos_map = {
                    "FIFO": EscalonadorFIFO, "SJF": EscalonadorSJF, "RR": EscalonadorRoundRobin,
                    "EDF": EscalonadorEDF, "CFS": EscalonadorCFSSim
                }
                escalonador_class = algoritmos_map[algoritmo_nome]
                escalonador = escalonador_class()
                
                # Inicializa o Gerenciador de Memória se estiver ativo
                gerenciador_memoria = None
                if ativar_memoria:
                    gerenciador_memoria = GerenciadorMemoria(politica=politica_memoria, seed=seed_memoria)

                simulador = Simulador(
                    processos=lista_processos,
                    escalonador=escalonador,
                    sobrecarga_contexto=sobrecarga_contexto,
                    quantum=quantum,
                    gerenciador_memoria=gerenciador_memoria,
                    custo_disco=custo_disco if ativar_memoria else 0
                )
                
                resultados = simulador.executar()

                log_ticks = resultados['log_gantt']
                processos_finalizados = resultados['processos_terminados']
                metricas_globais = resultados['metricas_globais']
                status_memoria = resultados.get('status_memoria', {}) 

                
                # Exibir Gantt
                st.header("Gráfico de Gantt")
                figura_gantt = gerar_gantt(log_ticks, processos_finalizados, "", algoritmo_nome)
                st.pyplot(figura_gantt)
                
                # Exibir Tabela e Resumo lado a lado
                col_tabela, col_resumo = st.columns(2)
                
                with col_tabela:
                    st.header("Tabela Final de Processos")
                    df_metricas = gerar_dataframe_metricas(processos_finalizados)
                    st.dataframe(df_metricas, hide_index=True)
                
                with col_resumo:
                    st.header("Resumo Quantitativo")
                    dict_resumo = gerar_dict_resumo(metricas_globais, processos_finalizados)
                    # Adiciona métricas de memória ao resumo
                    if ativar_memoria and gerenciador_memoria:
                        dict_resumo["Total de Page Faults (Global)"] = status_memoria.get("total_page_faults", 0)
                        dict_resumo["Política de Substituição"] = politica_memoria
                    st.json(dict_resumo)
                    
                # Exibir Visualizações de Memória se ativas
                if ativar_memoria and status_memoria:
                    st.header("Visualização de Memória Virtual (Bônus)")
                    col_ram, col_disco, col_tabela_paginas = st.columns(3) # 3 colunas agora
                    
                    with col_ram:
                        st.subheader("Memória RAM (Frames)")
                        figura_ram = gerar_visualizacao_memoria_ram(status_memoria)
                        st.pyplot(figura_ram)
                        
                    with col_disco:
                        st.subheader("Disco")
                        figura_disco = gerar_visualizacao_disco() # <-- Novo
                        st.pyplot(figura_disco)
                        
                    with col_tabela_paginas:
                        st.subheader("Tabela de Páginas Invertida")
                        figura_tabela = gerar_visualizacao_tabela_invertida(status_memoria)
                        st.pyplot(figura_tabela)


            except Exception as e:
                st.error(f"Ocorreu um erro durante a simulação: {e}")
                import traceback
                traceback.print_exc()