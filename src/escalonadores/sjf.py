# src/escalonadores/sjf.py

from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorSJF(EscalonadorBase):
    """
    Implementa o escalonador Shortest Job First (SJF) não preemptivo. 
    Quando a CPU fica ociosa, ela seleciona o processo da fila de prontos que tem o menor tempo de
    execução 
    Não sobrescreve 'verificar_preempcao'.
    """

    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        """
        Adiciona um processo ao final da fila de prontos.
        Não é necessário ordenar na inserção.

        Args:
            processo (Processo): O processo que chegou.
            tempo_atual (int): O tempo de simulação atual.
        """
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """
        Encontra, remove e retorna o processo com o menor tempo
        de execução *total* (p.execucao) da fila de prontos.

        Returns:
            Optional[Processo]: O processo selecionado ou None se
                                a fila estiver vazia.
        """
        if not self.fila_prontos:
            return None

        processo_escolhido = min(self.fila_prontos, key=lambda p: p.execucao)
        
        self.fila_prontos.remove(processo_escolhido)
        
        return processo_escolhido