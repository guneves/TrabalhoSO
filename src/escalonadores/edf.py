from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorEDF(EscalonadorBase):
    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        """
        Args:
            processo (Processo): O processo que chegou.
            tempo_atual (int): O tempo de simulação atual.
        """
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """
        Encontra, remove e retorna o processo com o menor deadline absoluto.
        Critérios de Desempate: Menor Deadline, Processo ainda não iniciado, FIFO

        Returns:
            Optional[Processo]: O processo selecionado ou None se
                                a fila estiver vazia.
        """
        if not self.fila_prontos:
            return None

        processo_escolhido = min( #!
            self.fila_prontos, #!
            key=lambda p: (p.deadline, 1 if p.tempo_primeira_execucao is not None else 0, p.chegada) #!
        ) #!
        
        self.fila_prontos.remove(processo_escolhido)
        
        return processo_escolhido

    def verificar_preempcao(self, processo_atual: Processo, 
                             processo_novo: Processo, 
                             tempo_atual: int) -> bool:
        """
        Args:
            processo_atual (Processo): O processo na CPU.
            processo_novo (Processo): O processo que acabou de chegar.
            tempo_atual (int): O tempo de simulação atual.

        Returns:
            bool: True se a preempção deve ocorrer, False caso contrário.
        """
        return processo_novo.deadline <= processo_atual.deadline #!