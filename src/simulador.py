from typing import List, Optional, Dict, Any, Tuple
from .escalonadores import (
    EscalonadorBase, 
    EscalonadorRoundRobin, 
    EscalonadorEDF, 
    EscalonadorCFSSim
)
from .processo import Processo

ALGORITMOS_PREEMPTIVOS = (EscalonadorRoundRobin, EscalonadorEDF, EscalonadorCFSSim)

class Simulador:
    """
    Motor principal da simulação de eventos discretos.

    Gerencia o tempo, o estado da CPU, o ciclo de vida dos processos e
    a coleta de dados, delegando as decisões de escalonamento para
    um objeto 'EscalonadorBase'.
    """

    def __init__(self,
                 processos: List[Processo],
                 escalonador: EscalonadorBase,
                 sobrecarga_contexto: int,
                 quantum: Optional[int] = None):
        """
        Inicializa o simulador.

        Args:
            processos (List[Processo]): A lista de todos os processos 
                                          a serem simulados.
            escalonador (EscalonadorBase): A instância do algoritmo de 
                                           escalonamento a ser usada.
            sobrecarga_contexto (int): O custo (em ticks) de cada 
                                       troca de contexto.
            quantum (Optional[int]): A fatia de tempo máxima para 
                                     algoritmos preemptivos.
        """
        self.escalonador = escalonador
        self.sobrecarga_contexto = sobrecarga_contexto
        self.quantum = quantum
        
        self.eh_preemptivo = isinstance(self.escalonador, ALGORITMOS_PREEMPTIVOS)

        self.tempo_atual: int = 0
        self.cpu_status: str = "ocioso"  # "ocioso", "executando", "sobrecarga"
        self.tempo_sobrecarga_restante: int = 0
        self.tempo_execucao_fatia_atual: int = 0

        self.processo_executando: Optional[Processo] = None
        self.processos_nao_chegaram: List[Processo] = sorted(
            processos, key=lambda p: p.chegada
        )
        self.processos_finalizados: List[Processo] = []

        self.log_gantt_ticks: List[Dict[str, Any]] = []
        self.metricas_globais: Dict[str, Any] = {
            "total_trocas_contexto": 0,
            "total_preempcoes": 0,
            "tempo_total_ocioso": 0,
            "tempo_total_sobrecarga": 0,
        }

    def executar(self) -> Dict[str, Any]:
        """
        Inicia e executa o loop principal da simulação.

        O loop continua "tick" por "tick" até que não haja mais processos
        para chegar, nem na fila de prontos, e nem em execução.

        Returns:
            Dict[str, Any]: Um dicionário contendo os resultados da 
                            simulação ('log_gantt', 'processos_terminados', 
                            'metricas_globais').
        """
        
        while (self.processos_nao_chegaram or
               self.escalonador.fila_prontos or
               self.processo_executando or
               self.cpu_status == "sobrecarga"):

            self._processar_chegadas()

            if self.cpu_status == "executando":
                self._processar_execucao()
            elif self.cpu_status == "sobrecarga":
                self._processar_sobrecarga()
            elif self.cpu_status == "ocioso":
                self._processar_ociosidade()
            
            for processo_pronto in self.escalonador.fila_prontos:
                self._logar_gantt_evento(processo_pronto.id, "esperando")
            self.tempo_atual += 1
        
        self._calcular_metricas_globais_finais()

        return {
            "log_gantt": self.log_gantt_ticks,
            "processos_terminados": self.processos_finalizados,
            "metricas_globais": self.metricas_globais
        }


    def _processar_chegadas(self):
        """
        Verifica se novos processos chegaram no tempo_atual.
        Se sim, os adiciona ao escalonador e verifica preempção por evento.
        """
        while self.processos_nao_chegaram and \
              self.processos_nao_chegaram[0].chegada <= self.tempo_atual:
            
            novo_processo = self.processos_nao_chegaram.pop(0)
            novo_processo.status = "pronto"
            
            deve_preemptar = False
            if self.processo_executando:
                deve_preemptar = self.escalonador.verificar_preempcao(
                    self.processo_executando, novo_processo, self.tempo_atual
                ) 

            self.escalonador.adicionar_processo(novo_processo, self.tempo_atual)

            if deve_preemptar:
                # Preempção por evento (ex: EDF, CFS)
                self.metricas_globais["total_preempcoes"] += 1
                self._iniciar_troca_contexto(processo_saindo=self.processo_executando, 
                                            preemptado=True)

    def _preemptar_por_quantum(self):
        """
        Força a preempção do processo atual por estouro de quantum.
        O processo é devolvido à fila de prontos e uma troca de
        contexto é iniciada.
        """
        if not self.processo_executando:
            return

        self.metricas_globais["total_preempcoes"] += 1
        self._iniciar_troca_contexto(processo_saindo=self.processo_executando, 
                                    preemptado=True)

    def _finalizar_processo(self, processo: Processo):
        """
        Processo terminou sua execução. Calcula métricas, libera a CPU
        e inicia uma troca (sem sobrecarga) para buscar o próximo.
        """
        processo.status = "terminado"
        processo.tempo_termino = self.tempo_atual
        processo.calcular_metricas_finais()
        
        self.processos_finalizados.append(processo)
        
        # Inicia a troca, marcando 'preemptado=False'
        # para que *não* haja sobrecarga.
        self._iniciar_troca_contexto(processo_saindo=processo, 
                                    preemptado=False)

    def _iniciar_troca_contexto(self, processo_saindo: Processo, preemptado: bool):
        """
        Inicia o estado de sobrecarga (se aplicável) ou ociosidade.

        Args:
            processo_saindo (Processo): O processo que estava na CPU.
            preemptado (bool): True se a troca foi por preempção (quantum/evento),
                               False se foi por término normal do processo.
        """
        
        if preemptado:
            # Se foi preempção, devolve o processo para a fila
            processo_saindo.status = "pronto"
            self.escalonador.adicionar_processo(processo_saindo, self.tempo_atual)

        self.processo_executando = None
        self.metricas_globais["total_trocas_contexto"] += 1
        
        # --- CORREÇÃO PRINCIPAL ---
        # Só aplica sobrecarga se:
        # 1. O custo de sobrecarga é > 0
        # 2. A troca foi causada por PREEMPÇÃO (Quantum ou Evento).
        #
        # Algoritmos não preemptivos (FIFO, SJF) sempre terminarão
        # com 'preemptado=False', pulando a sobrecarga.
        
        if self.sobrecarga_contexto > 0 and preemptado:
            self.cpu_status = "sobrecarga"
            self.tempo_sobrecarga_restante = self.sobrecarga_contexto
        else:
            # Se não há custo ou se o processo terminou normalmente,
            # a CPU fica ociosa e pronta para buscar o próximo.
            self.cpu_status = "ocioso"

    def _iniciar_execucao(self, processo: Processo):
        """
        Transição de 'ocioso' para 'executando'.
        """
        self.cpu_status = "executando"
        self.processo_executando = processo
        self.processo_executando.status = "executando"
        self.tempo_execucao_fatia_atual = 0

        if processo.tempo_primeira_execucao is None:
            processo.tempo_primeira_execucao = self.tempo_atual


    def _processar_execucao(self):
        """
        Estado 1: CPU está executando um processo.
        Verifica término ou preempção por quantum.
        """
        if not self.processo_executando:
            self.cpu_status = "ocioso"
            return
            
        processo = self.processo_executando
        
        self._logar_gantt_evento(processo.id, "executando")

        # Lógica Específica do CFS-Sim
        if isinstance(self.escalonador, EscalonadorCFSSim):
            self.escalonador.atualizar_vruntime_processo_executando(processo, 1)

        processo.tempo_restante -= 1
        self.tempo_execucao_fatia_atual += 1

        if processo.tempo_restante == 0:
            self._finalizar_processo(processo)
            return

        #Verificar Fim de Quantum (REGRA GLOBAL PREEMPTIVA)
        if (self.eh_preemptivo and
            self.quantum is not None and
            self.tempo_execucao_fatia_atual >= self.quantum):
            
            self._preemptar_por_quantum()

    def _processar_sobrecarga(self):
        """
        Estado 2: CPU está em troca de contexto (preemptiva).
        Apenas conta o tempo.
        """
        self._logar_gantt_evento("CPU", "sobrecarga")
        self.metricas_globais["tempo_total_sobrecarga"] += 1
        
        self.tempo_sobrecarga_restante -= 1

        if self.tempo_sobrecarga_restante == 0:
            self.cpu_status = "ocioso"

    def _processar_ociosidade(self):
        """
        Estado 3: CPU está ociosa, tenta buscar um novo processo.
        """
        proximo_processo = self.escalonador.proximo_processo()

        if proximo_processo:
            self._iniciar_execucao(proximo_processo)
            
            # Processa o primeiro tick imediatamente
            self._processar_execucao()
        
        else:
            self._logar_gantt_evento("CPU", "ocioso")
            self.metricas_globais["tempo_total_ocioso"] += 1


    def _logar_gantt_evento(self, id_processo: str, status: str):
        """Adiciona uma entrada ao log de ticks para o Gantt."""
        self.log_gantt_ticks.append({
            "tick": self.tempo_atual,
            "id": id_processo,
            "status": status
        })

    def _calcular_metricas_globais_finais(self):
        """Calcula métricas globais ao término da simulação."""
        tempo_total = self.tempo_atual
        if tempo_total == 0:
            self.metricas_globais["throughput"] = 0
            self.metricas_globais["utilizacao_cpu_percent"] = 0
            return

        self.metricas_globais["throughput"] = len(self.processos_finalizados) / tempo_total
        
        tempo_executando = (tempo_total - 
                            self.metricas_globais["tempo_total_ocioso"] - 
                            self.metricas_globais["tempo_total_sobrecarga"])

        if tempo_total > 0:
            self.metricas_globais["utilizacao_cpu_percent"] = (tempo_executando / tempo_total) * 100
            self.metricas_globais["ociosidade_cpu_percent"] = (
                self.metricas_globais["tempo_total_ocioso"] / tempo_total
            ) * 100
        else:
            self.metricas_globais["utilizacao_cpu_percent"] = 0
            self.metricas_globais["ociosidade_cpu_percent"] = 0
            
        self.metricas_globais["tempo_total_simulacao"] = tempo_total