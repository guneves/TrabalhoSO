"""
Exemplo:

from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorFIFO(EscalonadorBase):
    
    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        if self.fila_prontos:
            return self.fila_prontos.pop(0)
        return None
"""