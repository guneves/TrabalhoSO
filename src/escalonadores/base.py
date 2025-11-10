from abc import ABC, abstractmethod
from typing import List, Optional

from ..processo import Processo 

class EscalonadorBase(ABC):
    
    def __init__(self):
        self.fila_prontos: List[Processo] = []

    @abstractmethod
    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        pass

    @abstractmethod
    def proximo_processo(self) -> Optional[Processo]:
        pass

    def verificar_preempcao(self, processo_atual: Processo, processo_novo: Processo, tempo_atual: int) -> bool:
        return False