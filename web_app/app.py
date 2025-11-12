import streamlit as st
import sys
import os

# --- Configuração de Caminho (Path) ---
# Adiciona o diretório raiz ao path do Python para que 
# possamos importar o pacote 'src'.
# Isso é crucial para o Streamlit encontrar seus módulos.
DIRETORIO_ATUAL = os.path.dirname(__file__)
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, '..'))
sys.path.append(DIRETORIO_RAIZ)
# --- Fim da Configuração de Caminho ---

# Tenta importar os módulos do 'src'
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
    # Importa as funções refatoradas
    from src.visualizacao import gerar_gantt
    from src.metricas import gerar_dataframe_metricas, gerar_dict_resumo

except ImportError as e:
    st.error(f"Erro ao importar módulos do 'src': {e}")
    st.error("Verifique se a estrutura de pastas está correta e se 'src/__init__.py' existe.")
    st.stop() # Impede a execução do app se os módulos não forem encontrados

# --- UI (Interface do Usuário) ---

st.set_page_config(layout="wide") # Usa a página inteira
st.title('Simulador de Escalonamento de Processos ⚙️')

# --- 1. Configurações Globais ---
st.subheader('1. Configurações Globais da Simulação')

# Organiza as configurações globais em colunas
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

st.markdown("---") # Linha divisória

# --- 2. Configuração dos Processos (As 6 Boxes) ---
st.subheader('2. Definição dos Processos')

processos_input = []
num_processos = 6 # Seu requisito de 6 boxes

# Cria 6 abas (P1 a P6)
tab_nomes = [f'Processo {i+1}' for i in range(num_processos)]
tabs = st.tabs(tab_nomes)

# Valores padrão para os 3 primeiros processos (para facilitar o teste)
defaults = [
    {'chegada': 0, 'execucao': 5, 'deadline': 8, 'prioridade': 2}, # P1
    {'chegada': 1, 'execucao': 4, 'deadline': 12, 'prioridade': 1}, # P2
    {'chegada': 3, 'execucao': 2, 'deadline': 20, 'prioridade': 3}, # P3
    {'chegada': 5, 'execucao': 6, 'deadline': 22, 'prioridade': 1}, # P4
    {'chegada': 6, 'execucao': 3, 'deadline': 15, 'prioridade': 2}, # P5
    {'chegada': 8, 'execucao': 4, 'deadline': 25, 'prioridade': 3}, # P6
]

for i, tab in enumerate(tabs):
    with tab:
        id_proc = f'P{i+1}'
        
        # O checkbox "Ativar" decide se este processo será enviado para a simulação
        ativar_processo = st.checkbox(
            f'Ativar Processo {id_proc}', 
            value=(i < 3) # Ativa os 3 primeiros por padrão
        )
        
        # Usa colunas para organizar os inputs
        col1, col2, col3, col4 = st.columns(4)
        
        # Pega os valores padrão ou usa valores genéricos
        default_val = defaults[i] if i < len(defaults) else {'chegada': i*2, 'execucao': 5, 'deadline': 20, 'prioridade': 1}
        
        chegada = col1.number_input(f'Tempo de Chegada ({id_proc})', 
                                    min_value=0, value=default_val['chegada'], key=f'ch_{i}')
        execucao = col2.number_input(f'Tempo de Execução ({id_proc})', 
                                     min_value=1, value=default_val['execucao'], key=f'ex_{i}')
        # Renomeamos a label para "Deadline (Relativo)" para ficar claro na UI
        deadline = col3.number_input(f'Deadline (Relativo) ({id_proc})', 
                                      min_value=1, value=default_val['deadline'], key=f'dl_{i}')
        prioridade = col4.number_input(f'Prioridade ({id_proc})', 
                                        min_value=1, value=default_val['prioridade'], key=f'pr_{i}')
        
        # Se o processo estiver ativado, adiciona seus dados à lista
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

# --- 3. Execução (Passo 4 do Plano) e 4. Resultados (Passo 5) ---
st.subheader('3. Executar Simulação e Ver Resultados')

# O botão que inicia tudo
if st.button('Executar Simulação', type="primary"):
    
    if not processos_input:
        st.error("Erro: Nenhum processo foi ativado. Por favor, ative pelo menos um processo.")
    else:
        with st.spinner('Simulando...'):
            try:
                # 1. Criar Processos
                # Esta linha agora recebe o deadline já somado (relativo -> absoluto)
                lista_processos = [Processo(**p) for p in processos_input]
                
                # 2. Criar Escalonador (Lógica copiada do main.py)
                algoritmos_map = {
                    "FIFO": EscalonadorFIFO, "SJF": EscalonadorSJF, "RR": EscalonadorRoundRobin,
                    "EDF": EscalonadorEDF, "CFS": EscalonadorCFSSim
                }
                escalonador_class = algoritmos_map[algoritmo_nome]
                escalonador = escalonador_class()

                # 3. Instanciar e Executar o Simulador
                simulador = Simulador(
                    processos=lista_processos,
                    escalonador=escalonador,
                    sobrecarga_contexto=sobrecarga_contexto,
                    quantum=quantum
                )
                
                resultados = simulador.executar()

                # 4. Pegar os resultados
                log_ticks = resultados['log_gantt']
                processos_finalizados = resultados['processos_terminados']
                metricas_globais = resultados['metricas_globais']

                # --- 5. Exibir os Resultados ---
                
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
                # Imprime o traceback completo no console para debugging
                import traceback
                traceback.print_exc()