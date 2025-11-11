from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorFIFO(EscalonadorBase):
    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        """
        Adiciona um processo ao final da fila de prontos.

        Args:
            processo (Processo)
            tempo_atual (int)
        """
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """
        Remove e retorna o primeiro processo da fila (first out).

        Returns:
            Optional[Processo]
        """
        if self.fila_prontos:
            return self.fila_prontos.pop(0)
        return None
    