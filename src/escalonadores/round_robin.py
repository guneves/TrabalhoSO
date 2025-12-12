from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorRoundRobin(EscalonadorBase):
    """
    Implementa o escalonador Round-Robin (RR).
    """

    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        """
        Adiciona um processo ao FINAL da fila de prontos,
        registrando o momento exato de entrada para desempate.
        """
        processo._tick_entrada_fila = tempo_atual 
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """
        Remove e retorna o próximo processo. Desempate final: Quem tem o menor tick real.

        Returns:
            Optional[Processo]: O próximo processo a ser executado.
        """
        if not self.fila_prontos:
            return None

        processo_escolhido = min(
            self.fila_prontos,
            key=lambda p: (
                getattr(p, '_tick_entrada_fila', 0) - (1 if p.tempo_primeira_execucao is None else 0),
                1 if p.tempo_primeira_execucao is not None else 0,
                getattr(p, '_tick_entrada_fila', 0)
            )
        )
        
        self.fila_prontos.remove(processo_escolhido)
        return processo_escolhido