import math
from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorCFSSim(EscalonadorBase):
    """
    Implementa o escalonador "Completely Fair Scheduler" Simplificado (CFS-Sim).

    Esta estratégia é preemptiva e baseada em justiça,
    utilizando um "tempo virtual" (vruntime).

    Regras do PDF:
    1. Processos novos recebem vruntime = tempo_atual.
    2. O processo com o *menor* vruntime é escolhido.
    3. vruntime é atualizado com base no tempo de execução e prioridade.
    4. Preempção ocorre se um processo na fila tem vruntime menor que o atual.
    """

    def _calcular_peso(self, prioridade: int) -> float:
        """
        Calcula o peso (w) de um processo com base em sua prioridade.
        Fórmula: w(prioridade) = 1.25^(prioridade-1)
        [cite: 79]
        """
        # (prioridade-1) pois o PDF diz 1=maior prioridade,
        # o que corresponde ao peso base de 1.25^0 = 1 (se 1 fosse 0)
        # Vamos seguir a fórmula literalmente.
        return math.pow(1.25, (prioridade - 1))

    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        """
        Adiciona um processo à fila de prontos.

        Se for um processo novo (vruntime==0), seu vruntime inicial
        é definido como o tempo_atual.
        [cite: 81, 94]

        Args:
            processo (Processo): O processo a ser adicionado.
            tempo_atual (int): O tempo de simulação atual.
        """
        # Se o vruntime é 0, é um processo "novo" chegando ao escalonador.
        # Damos a ele o "piso" de vruntime atual.
        if processo.vruntime == 0:
            # Regra: vruntime = tempo_atual
            processo.vruntime = float(tempo_atual)
            
            # (Otimização: se t=0, vruntime=0. Se vários chegam em t=0,
            # todos têm vruntime=0, o que é justo.
            # Se um processo chega em t=10, ele começa com vruntime=10.)

        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """
        Encontra, remove e retorna o processo com o *menor vruntime*.
        [cite: 83, 96]
        Returns:
            Optional[Processo]: O processo selecionado ou None se
                                a fila estiver vazia.
        """
        if not self.fila_prontos:
            return None

        # "O próximo processo a executar é o de menor vruntime" [cite: 83]
        processo_escolhido = min(self.fila_prontos, key=lambda p: p.vruntime)
        
        self.fila_prontos.remove(processo_escolhido)
        
        return processo_escolhido

    def verificar_preempcao(self, processo_atual: Processo, 
                             processo_novo: Processo, 
                             tempo_atual: int) -> bool:
        """
        Verifica se o processo 'novo' que acabou de chegar deve
        preemptar o processo 'atual' em execução.

        Regra: Preempção ocorre se o vruntime do novo for menor.
        [cite: 85]
        """
        
        # Garante que o vruntime do novo processo foi setado
        # (caso 'adicionar_processo' ainda não tenha sido chamado para ele)
        if processo_novo.vruntime == 0:
             processo_novo.vruntime = float(tempo_atual)

        return processo_novo.vruntime < processo_atual.vruntime

    # --- MÉTODO NOVO (Necessário para o Simulador) ---
    
    def atualizar_vruntime_processo_executando(self, processo: Processo, delta_t: int = 1):
        """
        ATUALIZA O VRUNTIME DO PROCESSO QUE ESTÁ NA CPU.
        
        Esta função *deve* ser chamada pelo Simulador a cada tick
        que o processo passa em execução.
        
        vruntime = vruntime + Δt * w(prioridade)
        [cite: 77]
        """
        if processo is None:
            return
            
        peso = self._calcular_peso(processo.prioridade)
        
        # Neste simulador, delta_t é sempre 1 (1 tick)
        processo.vruntime += delta_t * peso