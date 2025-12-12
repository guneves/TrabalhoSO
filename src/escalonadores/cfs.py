import math
from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorCFSSim(EscalonadorBase):
    def _calcular_peso(self, prioridade: int) -> float:
        """
        (prioridade-1) pois o PDF diz 1=maior prioridade,
        o que corresponde ao peso base de 1.25^0 = 1 (se 1 fosse 0)
        """
        return math.pow(1.25, (prioridade - 1))

    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        '''
        Docstring for adicionar_processo
        
        :param self: Esse método pertence à classe EscalonadorCFSSim
        :param processo:
        :type processo: Processo
        :param tempo_atual: Description
        :type tempo_atual: int
        '''
        if processo.vruntime == 0:
            processo.vruntime = float(tempo_atual)
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        if not self.fila_prontos:
            return None

        processo_escolhido = min(self.fila_prontos, key=lambda p: p.vruntime)
        
        self.fila_prontos.remove(processo_escolhido)
        
        return processo_escolhido

    def verificar_preempcao(self, processo_atual: Processo, 
                             processo_novo: Processo, 
                             tempo_atual: int) -> bool:
        if processo_novo.vruntime == 0:
             processo_novo.vruntime = float(tempo_atual)

        return processo_novo.vruntime < processo_atual.vruntime

    def atualizar_vruntime_processo_executando(self, processo: Processo, delta_t: int = 1):
        if processo is None:
            return
            
        peso = self._calcular_peso(processo.prioridade)
        
        processo.vruntime += delta_t * peso