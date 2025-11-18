# simulador.py
from typing import List, Optional, Dict, Any, Tuple
from .escalonadores import (
    EscalonadorBase, 
    EscalonadorRoundRobin, 
    EscalonadorEDF, 
    EscalonadorCFSSim
)
from .processo import Processo
from .memoria import GerenciadorMemoria # <-- Adicionado

ALGORITMOS_PREEMPTIVOS = (EscalonadorRoundRobin, EscalonadorEDF, EscalonadorCFSSim)

class Simulador:
    """
    Motor principal da simulação de eventos discretos.
    """

    def __init__(self,
                 processos: List[Processo],
                 escalonador: EscalonadorBase,
                 sobrecarga_contexto: int,
                 quantum: Optional[int] = None,
                 # Parâmetros de Memória (Bônus)
                 gerenciador_memoria: Optional[GerenciadorMemoria] = None,
                 custo_disco: int = 0):
        
        self.escalonador = escalonador
        self.sobrecarga_contexto = sobrecarga_contexto
        self.quantum = quantum
        
        # Parâmetros de Memória (Bônus)
        self.gerenciador_memoria = gerenciador_memoria
        self.custo_disco = custo_disco
        self.processo_bloqueado_mem: Optional[Processo] = None
        self.tempo_bloqueio_restante: int = 0
        
        self.eh_preemptivo = isinstance(self.escalonador, ALGORITMOS_PREEMPTIVOS)

        self.tempo_atual: int = 0
        # "ocioso", "executando", "sobrecarga", "bloqueado_mem"
        self.cpu_status: str = "ocioso" 
        self.tempo_sobrecarga_restante: int = 0
        self.processo_em_sobrecarga: Optional[Processo] = None
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
            "tempo_total_bloqueio_mem": 0, # <-- Adicionado
        }

    def executar(self) -> Dict[str, Any]:
        """
        Inicia e executa o loop principal da simulação.
        """
        
        while (self.processos_nao_chegaram or
               self.escalonador.fila_prontos or
               self.processo_executando or
               self.cpu_status in ["sobrecarga", "bloqueado_mem"]): # <-- Ajustado
            
            self._processar_chegadas()

            for p in self.escalonador.fila_prontos:
                if p == self.processo_em_sobrecarga:
                    continue
                self._logar_gantt_evento(p.id, "esperando")

            if self.cpu_status == "executando":
                self._processar_execucao()
            elif self.cpu_status == "sobrecarga":
                self._processar_sobrecarga()
            elif self.cpu_status == "bloqueado_mem": # <-- Novo estado
                self._processar_bloqueio_mem()
            elif self.cpu_status == "ocioso":
                self._processar_ociosidade()
            
            self.tempo_atual += 1
        
        self._calcular_metricas_globais_finais()
        
        # Coleta dados de memória para o Streamlit
        mem_status = self.gerenciador_memoria.obter_status_memoria_para_visualizacao() if self.gerenciador_memoria else {}

        return {
            "log_gantt": self.log_gantt_ticks,
            "processos_terminados": self.processos_finalizados,
            "metricas_globais": self.metricas_globais,
            "status_memoria": mem_status # <-- Adicionado
        }


    def _processar_chegadas(self):
        """
        Verifica se novos processos chegaram no tempo_atual.
        """
        while self.processos_nao_chegaram and \
              self.processos_nao_chegaram[0].chegada <= self.tempo_atual:
            
            novo_processo = self.processos_nao_chegaram.pop(0)
            novo_processo.status = "pronto"
            
            # CFS-Sim: Inicializa vruntime para o novo processo
            if isinstance(self.escalonador, EscalonadorCFSSim):
                self.escalonador.inicializar_vruntime_chegada(novo_processo, self.tempo_atual)

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
        """
        if not self.processo_executando:
            return

        self.metricas_globais["total_preempcoes"] += 1
        self._iniciar_troca_contexto(processo_saindo=self.processo_executando, 
                                    preemptado=True)

    def _finalizar_processo(self, processo: Processo):
        """
        Processo terminou sua execução.
        """
        processo.status = "terminado"
        processo.tempo_termino = self.tempo_atual
        processo.calcular_metricas_finais(custo_sobrecarga=self.sobrecarga_contexto) 

        self.processos_finalizados.append(processo)
        
        # Inicia a troca, marcando 'preemptado=False' (sem sobrecarga)
        self._iniciar_troca_contexto(processo_saindo=processo, 
                                    preemptado=False)

    def _iniciar_troca_contexto(self, processo_saindo: Processo, preemptado: bool):
        """
        Inicia o estado de sobrecarga (se aplicável) ou ociosidade.
        """
        
        if preemptado:
            # Se foi preempção, devolve o processo para a fila
            processo_saindo.status = "pronto"
            processo_saindo.num_preempcoes += 1

            self.escalonador.adicionar_processo(processo_saindo, self.tempo_atual)

        self.processo_executando = None
        
        # Evita contar troca de contexto se o simulador estava em bloqueio de memória
        if self.cpu_status != "bloqueado_mem":
            self.metricas_globais["total_trocas_contexto"] += 1
        
        # Aplica sobrecarga apenas se a troca foi causada por PREEMPÇÃO e sobrecarga > 0
        if self.sobrecarga_contexto > 0 and preemptado:
            self.cpu_status = "sobrecarga"
            self.tempo_sobrecarga_restante = self.sobrecarga_contexto
            self.processo_em_sobrecarga = processo_saindo
        else:
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
        Verifica término, preempção por quantum E Page Fault.
        """
        if not self.processo_executando:
            self.cpu_status = "ocioso"
            return
            
        processo = self.processo_executando
        
        # --- Lógica de Page Fault (Bônus) ---
        if self.gerenciador_memoria and processo.num_paginas > 0:
            page_fault = self.gerenciador_memoria.gerar_requisicao_pagina(processo, self.tempo_atual)
            
            if page_fault == 1 and self.custo_disco > 0:
                # Page Fault ocorreu e há custo de bloqueio.
                processo.status = "bloqueado_mem"
                self.cpu_status = "bloqueado_mem"
                self.processo_bloqueado_mem = processo
                self.tempo_bloqueio_restante = self.custo_disco
                self.processo_executando = None # Libera CPU
                
                # O bloqueio é uma interrupção, não uma preempção de escalonador, mas libera CPU.
                # Não inicia troca de contexto, apenas muda o estado da CPU.
                self._logar_gantt_evento(processo.id, "bloqueado_mem")
                return # Pula o tick de execução do processo

        self._logar_gantt_evento(processo.id, "executando")

        # Lógica Específica do CFS-Sim
        if isinstance(self.escalonador, EscalonadorCFSSim):
            self.escalonador.atualizar_vruntime_processo_executando(processo, 1)

        processo.tempo_restante -= 1
        self.tempo_execucao_fatia_atual += 1

        if processo.tempo_restante == 0:
            self._finalizar_processo(processo)
            return

        # Verificar Fim de Quantum (REGRA GLOBAL PREEMPTIVA)
        if (self.eh_preemptivo and
            self.quantum is not None and
            self.tempo_execucao_fatia_atual >= self.quantum):
            
            self._preemptar_por_quantum()

    def _processar_sobrecarga(self):
        """
        Estado 2: CPU está em troca de contexto (preemptiva).
        """
        self._logar_gantt_evento("CPU", "sobrecarga")
        self.metricas_globais["tempo_total_sobrecarga"] += 1
        
        self.tempo_sobrecarga_restante -= 1

        if self.tempo_sobrecarga_restante == 0:
            self.cpu_status = "ocioso"
            self.processo_em_sobrecarga = None

    def _processar_bloqueio_mem(self):
        """
        Estado 4: Processo está bloqueado esperando I/O de disco (Page Fault).
        A CPU fica ociosa, mas o tempo conta para o bloqueio do processo.
        """
        if not self.processo_bloqueado_mem:
            self.cpu_status = "ocioso"
            return
            
        # O log de Gantt deve mostrar que a CPU está bloqueada POR um processo
        # Ocioso/Bloqueado na linha do processo, e ocioso na linha da CPU
        self._logar_gantt_evento(self.processo_bloqueado_mem.id, "bloqueado_mem")
        
        self.metricas_globais["tempo_total_bloqueio_mem"] += 1
        
        self.tempo_bloqueio_restante -= 1

        if self.tempo_bloqueio_restante == 0:
            # Bloqueio terminou, processo volta à fila de prontos
            self.processo_bloqueado_mem.status = "pronto"
            self.escalonador.adicionar_processo(self.processo_bloqueado_mem, self.tempo_atual)
            
            self.processo_bloqueado_mem = None
            self.cpu_status = "ocioso" # Volta ao estado ocioso para buscar o próximo

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
            for key in ["throughput", "utilizacao_cpu_percent", "ociosidade_cpu_percent"]:
                self.metricas_globais[key] = 0
            return

        self.metricas_globais["throughput"] = len(self.processos_finalizados) / tempo_total
        
        tempo_ocioso_e_bloqueio = (self.metricas_globais["tempo_total_ocioso"] + 
                                   self.metricas_globais["tempo_total_bloqueio_mem"])

        tempo_executando = (tempo_total - 
                            tempo_ocioso_e_bloqueio - 
                            self.metricas_globais["tempo_total_sobrecarga"])

        if tempo_total > 0:
            self.metricas_globais["utilizacao_cpu_percent"] = (tempo_executando / tempo_total) * 100
            # A ociosidade real da CPU é o tempo ocioso + tempo de bloqueio de memória (esperando I/O)
            self.metricas_globais["ociosidade_cpu_percent"] = (
                tempo_ocioso_e_bloqueio / tempo_total
            ) * 100
        else:
            self.metricas_globais["utilizacao_cpu_percent"] = 0
            self.metricas_globais["ociosidade_cpu_percent"] = 0
            
        self.metricas_globais["tempo_total_simulacao"] = tempo_total