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
    from src.visualizacao import gerar_gantt
    from src.metricas import gerar_dataframe_metricas, gerar_dict_resumo

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

st.subheader('Definição dos Processos')

processos_input = []
num_processos = 6 

tab_nomes = [f'Processo {i+1}' for i in range(num_processos)]
tabs = st.tabs(tab_nomes)

defaults = [
   {'chegada': 0, 'execucao': 4, 'deadline': 7, 'prioridade': 2}, # P1
   {'chegada': 2, 'execucao': 2, 'deadline': 5, 'prioridade': 1}, # P2
   {'chegada': 4, 'execucao': 1, 'deadline': 8, 'prioridade': 3}, # P3
   {'chegada': 6, 'execucao': 3, 'deadline': 10, 'prioridade': 1}, # P4
   {'chegada': 8, 'execucao': 3, 'deadline': 15, 'prioridade': 2}, # P5
   {'chegada': 10, 'execucao': 4, 'deadline': 25, 'prioridade': 3}, # P6
]

for i, tab in enumerate(tabs):
    with tab:
        id_proc = f'P{i+1}'
        
        ativar_processo = st.checkbox(
            f'Ativar Processo {id_proc}', 
            value=(i < 3)
        )
        
        col1, col2, col3, col4 = st.columns(4)
        
        default_val = defaults[i] if i < len(defaults) else {'chegada': i*2, 'execucao': 5, 'deadline': 20, 'prioridade': 1}
        
        chegada = col1.number_input(f'Tempo de Chegada ({id_proc})', 
                                    min_value=0, value=default_val['chegada'], key=f'ch_{i}')
        execucao = col2.number_input(f'Tempo de Execução ({id_proc})', 
                                     min_value=1, value=default_val['execucao'], key=f'ex_{i}')
        deadline = col3.number_input(f'Deadline (Relativo) ({id_proc})', 
                                      min_value=1, value=default_val['deadline'], key=f'dl_{i}')
        prioridade = col4.number_input(f'Prioridade ({id_proc})', 
                                        min_value=1, value=default_val['prioridade'], key=f'pr_{i}')
        
        if ativar_processo:
            processos_input.append({
                'id': id_proc,
                'chegada': chegada,
                'execucao': execucao,
                'deadline': chegada + deadline,
                'deadline_relativo': deadline,
                'prioridade': prioridade
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

                simulador = Simulador(
                    processos=lista_processos,
                    escalonador=escalonador,
                    sobrecarga_contexto=sobrecarga_contexto,
                    quantum=quantum
                )
                
                resultados = simulador.executar()

                log_ticks = resultados['log_gantt']
                processos_finalizados = resultados['processos_terminados']
                metricas_globais = resultados['metricas_globais']
                
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
                    st.json(dict_resumo)

            except Exception as e:
                st.error(f"Ocorreu um erro durante a simulação: {e}")
                import traceback
                traceback.print_exc()