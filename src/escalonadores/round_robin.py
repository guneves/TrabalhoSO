from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo


class EscalonadorRoundRobin(EscalonadorBase):
    """
    Implementa o escalonador Round Robin com fila circular FIFO.
    """

    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        if not self.fila_prontos:
            return None

        return self.fila_prontos.pop(0)
