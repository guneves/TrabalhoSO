# src/escalonadores/cfs.py
import math
from typing import Optional

from .base import EscalonadorBase
from ..processo import Processo

class EscalonadorCFSSim(EscalonadorBase):
    
    def _calcular_peso(self, prioridade: int) -> float:
        """
        Calcula o peso baseado na prioridade.
        Prioridade menor (ex: 1) = Peso menor = vruntime cresce devagar (Bom).
        Prioridade maior (ex: 3) = Peso maior = vruntime cresce rápido (Ruim).
        Formula: 1.25^(prioridade - 1)
        """
        # (prioridade-1) pois 1 é a base. Se prioridade for 1, expoente é 0 => Peso 1.
        return math.pow(1.25, (prioridade - 1))

    def inicializar_vruntime_chegada(self, processo: Processo, tempo_atual: int):
        """
        Define o vruntime inicial para um processo que acabou de chegar.
        Se é a primeira vez dele, vruntime = tempo atual.
        Isso evita que processos novos entrem com vruntime 0 e furem a fila de todos.
        """
        if processo.vruntime == 0:
            processo.vruntime = float(tempo_atual)

    def adicionar_processo(self, processo: Processo, tempo_atual: int):
        """
        Adiciona o processo à lista de prontos. 
        O vruntime já deve ter sido inicializado pelo método acima ou preservado de execuções anteriores.
        """
        # Segurança extra: caso o método de inicialização não tenha sido chamado
        if processo.vruntime == 0:
            processo.vruntime = float(tempo_atual)
            
        self.fila_prontos.append(processo)

    def proximo_processo(self) -> Optional[Processo]:
        """
        Retorna o processo com o MENOR vruntime (a "Esquerda" da árvore Rubro-Negra simulada).
        """
        if not self.fila_prontos:
            return None

        # A essência do CFS: O próximo é quem tem o menor tempo virtual de execução
        processo_escolhido = min(self.fila_prontos, key=lambda p: p.vruntime)
        
        self.fila_prontos.remove(processo_escolhido)
        
        return processo_escolhido

    def verificar_preempcao(self, processo_atual: Processo, 
                             processo_novo: Processo, 
                             tempo_atual: int) -> bool:
        """
        Verifica se o novo processo tem um vruntime menor que o atual.
        Isso acontece se um processo bloqueado volta ou se um novo chega com vruntime ajustado.
        """
        # Garante que o novo processo tenha vruntime definido para a comparação
        if processo_novo.vruntime == 0:
             processo_novo.vruntime = float(tempo_atual)

        # Se o novo processo "sofreu" menos (menor vruntime), ele deve executar.
        return processo_novo.vruntime < processo_atual.vruntime

    def atualizar_vruntime_processo_executando(self, processo: Processo, delta_t: int = 1):
        """
        Penaliza o processo que está rodando, aumentando seu vruntime.
        Quanto menor a prioridade (número maior), maior o peso, e mais rápido o vruntime sobe.
        """
        if processo is None:
            return
            
        peso = self._calcular_peso(processo.prioridade)
        
        # vruntime = tempo_real * peso
        processo.vruntime += delta_t * peso