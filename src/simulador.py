from typing import List, Optional, Dict, Any, Callable
import time

from .escalonadores import (
    EscalonadorBase,
    EscalonadorRoundRobin,
    EscalonadorEDF,
    EscalonadorCFSSim,
)
from .processo import Processo
from .memoria import GerenciadorMemoria


ALGORITMOS_PREEMPTIVOS = (EscalonadorRoundRobin, EscalonadorEDF, EscalonadorCFSSim)


class Simulador:
    """
    Motor principal da simulacao de eventos discretos.
    """

    def __init__(
        self,
        processos: List[Processo],
        escalonador: EscalonadorBase,
        sobrecarga_contexto: int,
        quantum: Optional[int] = None,
        gerenciador_memoria: Optional[GerenciadorMemoria] = None,
        custo_disco: int = 0,
    ):
        self.escalonador = escalonador
        self.sobrecarga_contexto = sobrecarga_contexto
        self.quantum = quantum
        self.gerenciador_memoria = gerenciador_memoria
        self.custo_disco = custo_disco

        self.eh_preemptivo = isinstance(self.escalonador, ALGORITMOS_PREEMPTIVOS)

        self.tempo_atual: int = 0
        self.cpu_status: str = "ocioso"
        self.evento_cpu_tick: Optional[str] = None
        self.tempo_sobrecarga_restante: int = 0
        self.processo_em_sobrecarga: Optional[Processo] = None
        self.tempo_execucao_fatia_atual: int = 0

        self.processo_executando: Optional[Processo] = None
        self.todos_processos: List[Processo] = list(processos)
        self.processos_nao_chegaram: List[Processo] = sorted(
            processos, key=lambda p: (p.chegada, p.id)
        )
        self.processos_bloqueados_memoria: List[Dict[str, Any]] = []
        self.processos_finalizados: List[Processo] = []

        self.log_gantt_ticks: List[Dict[str, Any]] = []
        self.metricas_globais: Dict[str, Any] = {
            "total_trocas_contexto": 0,
            "total_preempcoes": 0,
            "tempo_total_execucao_cpu": 0,
            "tempo_total_ocioso": 0,
            "tempo_total_sobrecarga": 0,
            "tempo_total_bloqueio_mem": 0,
            "tempo_total_page_fault_cpu": 0,
        }

    def executar(
        self,
        on_tick: Optional[Callable[[Dict[str, Any]], None]] = None,
        tick_delay: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Executa o loop principal da simulacao.
        """
        while self._tem_trabalho_pendente():
            self.evento_cpu_tick = None
            self._ids_com_evento_no_tick = set()

            self._liberar_bloqueios_memoria_concluidos()
            self._processar_chegadas()
            self._logar_processos_bloqueados_memoria()

            if self.cpu_status == "executando":
                self._processar_execucao()
            elif self.cpu_status == "sobrecarga":
                self._processar_sobrecarga()
            else:
                self._processar_ociosidade()

            self._logar_fila_prontos()

            snapshot = self._gerar_snapshot()

            if on_tick:
                on_tick(snapshot)

            if on_tick and tick_delay and tick_delay > 0:
                time.sleep(tick_delay)

            self.tempo_atual += 1

        self._calcular_metricas_globais_finais()

        return {
            "log_gantt": self.log_gantt_ticks,
            "processos_terminados": self.processos_finalizados,
            "metricas_globais": self.metricas_globais,
            "status_memoria": self._status_memoria(),
            "snapshots": [self._gerar_snapshot()],
        }

    def _tem_trabalho_pendente(self) -> bool:
        return bool(
            self.processos_nao_chegaram
            or self.escalonador.fila_prontos
            or self.processo_executando
            or self.cpu_status == "sobrecarga"
            or self.processos_bloqueados_memoria
        )

    def _processar_chegadas(self):
        while self.processos_nao_chegaram and self.processos_nao_chegaram[0].chegada <= self.tempo_atual:
            novo_processo = self.processos_nao_chegaram.pop(0)

            if isinstance(self.escalonador, EscalonadorCFSSim):
                self.escalonador.inicializar_vruntime_chegada(novo_processo, self.tempo_atual)

            self._adicionar_a_fila_prontos(novo_processo, considerar_preempcao=True)

    def _liberar_bloqueios_memoria_concluidos(self):
        ainda_bloqueados = []
        for item in self.processos_bloqueados_memoria:
            processo = item["processo"]
            if item["desbloqueio_em"] <= self.tempo_atual:
                processo.status_memoria = "resolvido"
                self._adicionar_a_fila_prontos(processo, considerar_preempcao=True)
            else:
                ainda_bloqueados.append(item)

        self.processos_bloqueados_memoria = ainda_bloqueados

    def _adicionar_a_fila_prontos(self, processo: Processo, considerar_preempcao: bool):
        processo.status = "pronto"
        self.escalonador.adicionar_processo(processo, self.tempo_atual)

        if not considerar_preempcao or not self.processo_executando:
            return

        deve_preemptar = self.escalonador.verificar_preempcao(
            self.processo_executando, processo, self.tempo_atual
        )
        if deve_preemptar:
            self.metricas_globais["total_preempcoes"] += 1
            self._iniciar_troca_contexto(
                processo_saindo=self.processo_executando,
                preemptado=True,
            )

    def _logar_fila_prontos(self):
        for processo in self.escalonador.fila_prontos:
            if processo == self.processo_em_sobrecarga:
                continue
            if processo.id in self._ids_com_evento_no_tick:
                continue
            processo.tempo_esperando_pronto += 1
            self._logar_gantt_evento(processo.id, "esperando")

    def _logar_processos_bloqueados_memoria(self):
        for item in self.processos_bloqueados_memoria:
            processo = item["processo"]
            self._logar_gantt_evento(processo.id, "bloqueado_mem")
            processo.tempo_bloqueado_memoria += 1
            self.metricas_globais["tempo_total_bloqueio_mem"] += 1

    def _preemptar_por_quantum(self):
        if not self.processo_executando:
            return

        self.metricas_globais["total_preempcoes"] += 1
        self._iniciar_troca_contexto(
            processo_saindo=self.processo_executando,
            preemptado=True,
        )

    def _finalizar_processo(self, processo: Processo):
        processo.status = "terminado"
        processo.tempo_termino = self.tempo_atual + 1
        processo.calcular_metricas_finais(custo_sobrecarga=self.sobrecarga_contexto)
        self.processos_finalizados.append(processo)

        self._iniciar_troca_contexto(processo_saindo=processo, preemptado=False)

    def _iniciar_troca_contexto(self, processo_saindo: Processo, preemptado: bool):
        if preemptado:
            processo_saindo.status = "pronto"
            processo_saindo.num_preempcoes += 1
            self.escalonador.adicionar_processo(processo_saindo, self.tempo_atual)

        self.processo_executando = None
        self.metricas_globais["total_trocas_contexto"] += 1

        if self.sobrecarga_contexto > 0 and preemptado:
            self.cpu_status = "sobrecarga"
            self.tempo_sobrecarga_restante = self.sobrecarga_contexto
            self.processo_em_sobrecarga = processo_saindo
        else:
            self.cpu_status = "ocioso"

    def _iniciar_execucao(self, processo: Processo):
        self.cpu_status = "executando"
        self.processo_executando = processo
        processo.status = "executando"
        processo.status_memoria = "acessando"
        self.tempo_execucao_fatia_atual = 0

        if processo.tempo_primeira_execucao is None:
            processo.tempo_primeira_execucao = self.tempo_atual

    def _processar_execucao(self):
        if not self.processo_executando:
            self.cpu_status = "ocioso"
            self.evento_cpu_tick = "ocioso"
            return

        processo = self.processo_executando

        if self.gerenciador_memoria and processo.num_paginas > 0:
            page_fault = self.gerenciador_memoria.gerar_requisicao_pagina(
                processo, self.tempo_atual
            )

            if page_fault == 1 and self.custo_disco > 0:
                self._bloquear_processo_por_memoria(processo)
                return

        self._logar_gantt_evento(processo.id, "executando")
        self.evento_cpu_tick = "executando"
        self.metricas_globais["tempo_total_execucao_cpu"] += 1

        if isinstance(self.escalonador, EscalonadorCFSSim):
            self.escalonador.atualizar_vruntime_processo_executando(processo, 1)

        processo.tempo_restante -= 1
        self.tempo_execucao_fatia_atual += 1

        if processo.tempo_restante == 0:
            self._finalizar_processo(processo)
            return

        if (
            self.eh_preemptivo
            and self.quantum is not None
            and self.tempo_execucao_fatia_atual >= self.quantum
        ):
            self._preemptar_por_quantum()

    def _bloquear_processo_por_memoria(self, processo: Processo):
        processo.status = "bloqueado_mem"
        processo.status_memoria = "page_fault"
        self.processo_executando = None
        self.cpu_status = "ocioso"
        self.evento_cpu_tick = "page_fault"
        self.tempo_execucao_fatia_atual = 0

        self.processos_bloqueados_memoria.append({
            "processo": processo,
            "desbloqueio_em": self.tempo_atual + max(1, self.custo_disco),
            "pagina": processo.ultima_pagina_requisitada,
        })
        self._logar_gantt_evento("CPU", "page_fault")
        self._logar_gantt_evento(processo.id, "bloqueado_mem")
        processo.tempo_bloqueado_memoria += 1
        self.metricas_globais["tempo_total_bloqueio_mem"] += 1
        self.metricas_globais["tempo_total_page_fault_cpu"] += 1

    def _processar_sobrecarga(self):
        self._logar_gantt_evento("CPU", "sobrecarga")
        self.evento_cpu_tick = "sobrecarga"
        self.metricas_globais["tempo_total_sobrecarga"] += 1
        self.tempo_sobrecarga_restante -= 1

        if self.tempo_sobrecarga_restante == 0:
            self.cpu_status = "ocioso"
            self.processo_em_sobrecarga = None

    def _processar_ociosidade(self):
        proximo_processo = self.escalonador.proximo_processo()

        if proximo_processo:
            self._iniciar_execucao(proximo_processo)
            self._processar_execucao()
            return

        self._logar_gantt_evento("CPU", "ocioso")
        self.evento_cpu_tick = "ocioso"
        self.metricas_globais["tempo_total_ocioso"] += 1

    def _logar_gantt_evento(self, id_processo: str, status: str):
        if id_processo != "CPU" and status != "esperando":
            self._ids_com_evento_no_tick.add(id_processo)

        self.log_gantt_ticks.append({
            "tick": self.tempo_atual,
            "id": id_processo,
            "status": status,
        })

    def _calcular_metricas_globais_finais(self):
        tempo_total = self.tempo_atual
        self.metricas_globais["tempo_total_simulacao"] = tempo_total

        if tempo_total == 0:
            self.metricas_globais["throughput"] = 0
            self.metricas_globais["utilizacao_cpu_percent"] = 0
            self.metricas_globais["ociosidade_cpu_percent"] = 0
            return

        tempo_execucao = self.metricas_globais["tempo_total_execucao_cpu"]
        tempo_ocioso = self.metricas_globais["tempo_total_ocioso"]

        self.metricas_globais["throughput"] = len(self.processos_finalizados) / tempo_total
        self.metricas_globais["utilizacao_cpu_percent"] = (tempo_execucao / tempo_total) * 100
        self.metricas_globais["ociosidade_cpu_percent"] = (tempo_ocioso / tempo_total) * 100

    def _status_memoria(self) -> Dict[str, Any]:
        if not self.gerenciador_memoria:
            return {}
        return self.gerenciador_memoria.obter_status_memoria_para_visualizacao()

    def _gerar_snapshot(self) -> Dict[str, Any]:
        return {
            "tick": self.tempo_atual,
            "cpu_status": self.evento_cpu_tick or self.cpu_status,
            "estado_interno_cpu": self.cpu_status,
            "processo_executando": self.processo_executando.id if self.processo_executando else None,
            "processo_executando_detalhes": (
                self._serializar_processo(self.processo_executando)
                if self.processo_executando else None
            ),
            "fila_prontos": [self._serializar_processo(p) for p in self.escalonador.fila_prontos],
            "fila_prontos_ids": [p.id for p in self.escalonador.fila_prontos],
            "processos_bloqueados_memoria": [
                {
                    **self._serializar_processo(item["processo"]),
                    "desbloqueio_em": item["desbloqueio_em"],
                    "tempo_restante_bloqueio": max(0, item["desbloqueio_em"] - self.tempo_atual),
                    "pagina": item.get("pagina"),
                }
                for item in self.processos_bloqueados_memoria
            ],
            "processos_nao_chegaram": [self._serializar_processo(p) for p in self.processos_nao_chegaram],
            "processos": [self._serializar_processo(p) for p in self.todos_processos],
            "processos_terminados": [p.id for p in self.processos_finalizados],
            "log_gantt": list(self.log_gantt_ticks),
            "metricas_globais": dict(self.metricas_globais),
            "status_memoria": self._status_memoria(),
        }

    def _serializar_processo(self, processo: Optional[Processo]) -> Dict[str, Any]:
        if processo is None:
            return {}

        return {
            "id": processo.id,
            "chegada": processo.chegada,
            "execucao": processo.execucao,
            "tempo_restante": processo.tempo_restante,
            "prioridade": processo.prioridade,
            "deadline": processo.deadline,
            "deadline_relativo": processo.deadline_relativo,
            "num_paginas": processo.num_paginas,
            "status": processo.status,
            "vruntime": processo.vruntime,
            "preempcoes": processo.num_preempcoes,
            "page_faults": processo.page_faults,
            "page_hits": processo.page_hits,
            "ultima_pagina_requisitada": processo.ultima_pagina_requisitada,
            "tempo_esperando_pronto": processo.tempo_esperando_pronto,
            "tempo_bloqueado_memoria": processo.tempo_bloqueado_memoria,
            "tempo_primeira_execucao": processo.tempo_primeira_execucao,
            "tempo_termino": processo.tempo_termino,
            "turnaround": processo.turnaround,
            "tempo_espera": processo.tempo_espera,
            "tempo_total_nao_executando": processo.tempo_total_nao_executando,
            "deadline_ok": processo.deadline_ok,
        }
