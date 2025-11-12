# src/escalonadores/edf.py

from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorEDF(EscalonadorBase):
    """
    Implementa o escalonador Earliest Deadline First (EDF).

    Esta é uma estratégia preemptiva onde a prioridade é dinâmica:
    o processo com o deadline (absoluto) mais próximo é escolhido.
    """

    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        """
        Adiciona um processo à fila de prontos.
        A seleção será feita no 'proximo_processo'.

        Args:
            processo (Processo): O processo que chegou.
            tempo_atual (int): O tempo de simulação atual.
        """
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """
        Encontra, remove e retorna o processo com o menor (mais cedo)
        deadline absoluto da fila de prontos.

        Returns:
            Optional[Processo]: O processo selecionado ou None se
                                a fila estiver vazia.
        """
        if not self.fila_prontos:
            return None

        # [cite_start]Encontra o processo com o menor deadline [cite: 69]
        processo_escolhido = min(self.fila_prontos, key=lambda p: p.deadline)
        
        # Remove o processo escolhido da fila
        self.fila_prontos.remove(processo_escolhido)
        
        return processo_escolhido

    def verificar_preempcao(self, processo_atual: Processo, 
                             processo_novo: Processo, 
                             tempo_atual: int) -> bool:
        """
        Verifica se o processo 'novo' que acabou de chegar deve
        preemptar o processo 'atual' em execução.

        A regra do EDF é: preemptar se o novo processo tem um
        [cite_start]deadline mais cedo. [cite: 70]

        Args:
            processo_atual (Processo): O processo na CPU.
            processo_novo (Processo): O processo que acabou de chegar.
            tempo_atual (int): O tempo de simulação atual.

        Returns:
            bool: True se a preempção deve ocorrer, False caso contrário.
        """
        return processo_novo.deadline < processo_atual.deadline