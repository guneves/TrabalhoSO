from typing import List, Dict, Any
import sys

# Tenta importar a classe Processo do módulo 'processo'
try:
    from .processo import Processo
except ImportError:
    try:
        from processo import Processo
    except ImportError:
        print("Aviso: Classe 'Processo' não encontrada.", file=sys.stderr)
        class Processo: pass 

def imprimir_tabela_final(processos_terminados: List[Processo]):
    """
    Imprime a tabela final de métricas individuais por processo,
    lendo os valores pré-calculados pelo simulador.
    """
    if not processos_terminados:
        print("Nenhum processo foi concluído.")
        return
        
    processos_terminados.sort(key=lambda p: p.id)

    # --- Imprimir Cabeçalho ---
    header = (
        f"{'ID':<5} | {'Chegada':>8} | {'Execução':>8} | {'Deadline':>8} | {'Priorid.':>8} | "
        f"{'Início':>8} | {'Término':>8} | {'Turnaround':>10} | {'Espera':>8} | {'D. OK?':>7}"
    )
    print(header)
    print("-" * len(header))

    # --- Imprimir Linhas de Processos ---
    for p in processos_terminados:
        
        # --- CORREÇÃO 2 e 3 ---
        # Lemos os valores que o simulador.py já calculou
        # durante a simulação (em _finalizar_processo)
        turnaround = p.turnaround if p.turnaround is not None else 0
        espera = p.tempo_espera if p.tempo_espera is not None else 0
        deadline_ok_str = "Sim" if p.deadline_ok else "Não"
        
        # --- CORREÇÃO 1 ---
        # Usamos o nome correto do atributo definido no simulador.py
        inicio = p.tempo_primeira_execucao if p.tempo_primeira_execucao is not None else -1
        
        # Formata a linha da tabela
        row = (
            f"{p.id:<5} | {p.chegada:>8} | {p.execucao:>8} | {p.deadline:>8} | {p.prioridade:>8} | "
            f"{inicio:>8} | {p.tempo_termino:>8} | {turnaround:>10} | {espera:>8} | {deadline_ok_str:>7}"
        )
        print(row)

def imprimir_resumo_quantitativo(
    metricas_globais: Dict[str, Any],
    processos_terminados: List[Processo]
):
    """
    Calcula e imprime as métricas globais do simulador.
    
    Lê as métricas de tempo e throughput do dicionário 'metricas_globais'
    e calcula as médias de turnaround/espera usando a lista 'processos_terminados'.
    """
    
    # --- CORREÇÃO 1: Lendo dados do dicionário 'metricas_globais' ---
    tempo_total = metricas_globais.get("tempo_total_simulacao", 0)
    tempo_ocioso = metricas_globais.get("tempo_total_ocioso", 0)
    total_trocas_contexto = metricas_globais.get("total_trocas_contexto", 0)
    throughput = metricas_globais.get("throughput", 0)
    percent_ociosidade = metricas_globais.get("ociosidade_cpu_percent", 0)
    
    
    # --- Calcular Médias (usando a lista de processos) ---
    num_processos = len(processos_terminados)
    media_turnaround = 0
    media_espera = 0

    if num_processos > 0:
        soma_turnaround = 0
        soma_espera = 0
        
        for p in processos_terminados:
            # --- CORREÇÃO 3: Lendo valores pré-calculados ---
            soma_turnaround += p.turnaround if p.turnaround is not None else 0
            soma_espera += p.tempo_espera if p.tempo_espera is not None else 0
            
        media_turnaround = soma_turnaround / num_processos
        media_espera = soma_espera / num_processos

    # --- Imprimir Resultados ---
    print(f"{'Tempo Total de Simulação:':<25} {tempo_total:.2f} u.t.")
    print(f"{'Tempo Total de Ociosidade:':<25} {tempo_ocioso:.2f} u.t.")
    print(f"{'Total de Trocas de Contexto:':<25} {total_trocas_contexto}")
    print("-" * 40)
    print(f"{'Taxa de Throughput:':<25} {throughput:.4f} processos/u.t.")
    print(f"{'% de Ociosidade da CPU:':<25} {percent_ociosidade:.2f}%")
    print(f"{'Tempo Médio de Turnaround:':<25} {media_turnaround:.2f} u.t.")
    print(f"{'Tempo Médio de Espera:':<25} {media_espera:.2f} u.t.")