from typing import List
import sys

# Tenta importar a classe Processo do módulo 'processo'
# O 'try/except' ajuda a manter a flexibilidade
try:
    from .processo import Processo
except ImportError:
    # Permite que o script seja testado isoladamente (se 'processo.py' estiver na mesma pasta)
    try:
        from processo import Processo
    except ImportError:
        # Se falhar, define uma classe 'stub' para evitar erros de tipo
        # Isso é útil para testes, mas o 'main.py' não deve chegar aqui.
        print("Aviso: Classe 'Processo' não encontrada.", file=sys.stderr)
        class Processo: pass 

def imprimir_tabela_final(processos_terminados: List[Processo]):
    """
    Imprime a tabela final de métricas individuais por processo,
    conforme especificado em[cite: 53].
    """
    if not processos_terminados:
        print("Nenhum processo foi concluído.")
        return
        
    # Ordena os processos por ID (P1, P2, ...) para uma exibição consistente
    processos_terminados.sort(key=lambda p: p.id)

    # --- Imprimir Cabeçalho ---
    # [cite: 53] "chegada, execucao, deadline, prioridade, inicio(s), termino, espera, turnaround, deadline_ok?"
    # Adicionamos 'ID' para clareza
    header = (
        f"{'ID':<5} | {'Chegada':>8} | {'Execução':>8} | {'Deadline':>8} | {'Priorid.':>8} | "
        f"{'Início':>8} | {'Término':>8} | {'Turnaround':>10} | {'Espera':>8} | {'D. OK?':>7}"
    )
    print(header)
    print("-" * len(header))

    # --- Imprimir Linhas de Processos ---
    for p in processos_terminados:
        # Calcula as métricas individuais [cite: 40, 41, 43]
        turnaround = p.termino - p.chegada
        espera = turnaround - p.execucao
        
        # Verifica se o deadline foi cumprido [cite: 38, 53]
        deadline_ok_str = "Sim" if p.termino <= p.deadline else "Não"
        
        # Formata a linha da tabela
        row = (
            f"{p.id:<5} | {p.chegada:>8.1f} | {p.execucao:>8.1f} | {p.deadline:>8.1f} | {p.prioridade:>8} | "
            f"{p.tempo_inicio:>8.1f} | {p.termino:>8.1f} | {turnaround:>10.1f} | {espera:>8.1f} | {deadline_ok_str:>7}"
        )
        print(row)

def imprimir_resumo_quantitativo(
    processos_terminados: List[Processo], 
    tempo_total: float, 
    tempo_ocioso: float, 
    total_trocas_contexto: int
):
    """
    Calcula e imprime as métricas globais do simulador,
    conforme especificado em[cite: 54].
    """
    num_processos = len(processos_terminados)

    if num_processos == 0:
        print("Nenhuma métrica global para calcular (0 processos terminados).")
        return

    # --- Calcular Médias [cite: 54] ---
    soma_turnaround = 0
    soma_espera = 0
    
    for p in processos_terminados:
        turnaround = p.termino - p.chegada
        espera = turnaround - p.execucao
        soma_turnaround += turnaround
        soma_espera += espera
        
    media_turnaround = soma_turnaround / num_processos
    media_espera = soma_espera / num_processos

    # --- Calcular Throughput [cite: 54] ---
    # Processos concluídos por unidade de tempo
    throughput = num_processos / tempo_total if tempo_total > 0 else 0
    
    # --- Calcular % Ociosidade [cite: 54] ---
    percent_ociosidade = (tempo_ocioso / tempo_total) * 100 if tempo_total > 0 else 0

    # --- Imprimir Resultados ---
    print(f"{'Tempo Total de Simulação:':<25} {tempo_total:.2f} u.t.")
    print(f"{'Tempo Total de Ociosidade:':<25} {tempo_ocioso:.2f} u.t.")
    print(f"{'Total de Trocas de Contexto:':<25} {total_trocas_contexto}")
    print("-" * 40)
    print(f"{'Taxa de Throughput:':<25} {throughput:.4f} processos/u.t.")
    print(f"{'% de Ociosidade da CPU:':<25} {percent_ociosidade:.2f}%")
    print(f"{'Tempo Médio de Turnaround:':<25} {media_turnaround:.2f} u.t.")
    print(f"{'Tempo Médio de Espera:':<25} {media_espera:.2f} u.t.")