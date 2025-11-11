from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorRoundRobin(EscalonadorBase):
    """
    Implementa o escalonador Round-Robin (RR).

    Esta estratégia trata a fila de prontos como uma fila circular (FIFO).
    Os processos são adicionados ao final da fila e o próximo a ser
    executado é removido do início.

    A lógica de preempção por 'quantum' é gerenciada pelo Simulador,
    que então devolve o processo para esta fila usando 'adicionar_processo'.
    """

    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        """
        Adiciona um processo ao FINAL da fila de prontos.

        Args:
            processo (Processo): O processo que está entrando na fila
                                (seja por chegada ou preempção).
            tempo_atual (int): O tempo de simulação atual (não utilizado pelo RR).
        """
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """
        Remove e retorna o primeiro processo da fila (o mais antigo).

        Returns:
            Optional[Processo]: O próximo processo a ser executado,
                                ou None se a fila estiver vazia.
        """
        if self.fila_prontos:
            return self.fila_prontos.pop(0)
        return None
