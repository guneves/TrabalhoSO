from typing import List, Dict, Optional, Any, Tuple
import random
import math

from .processo import Processo


TAMANHO_FRAME = 4
TAMANHO_RAM_KB = 200
NUM_FRAMES = math.ceil(TAMANHO_RAM_KB / TAMANHO_FRAME)


class Frame:
    """Representa um frame fisico na RAM."""

    def __init__(self, indice: int):
        self.indice = indice
        self.ocupado = False
        self.processo_id: Optional[str] = None
        self.numero_pagina: Optional[int] = None
        self.tempo_ultimo_uso: int = 0
        self.tempo_chegada: int = 0


class GerenciadorMemoria:
    """
    Gerencia frames de RAM, tabela invertida e substituicao FIFO/LRU.
    """

    def __init__(self, politica: str = "FIFO", seed: int = 42, num_frames: Optional[int] = None):
        politica_normalizada = politica.upper()
        if politica_normalizada not in {"FIFO", "LRU"}:
            raise ValueError("Politica de memoria invalida. Use FIFO ou LRU.")

        self.politica = politica_normalizada
        self.num_frames = max(1, int(num_frames or NUM_FRAMES))
        self.frames: List[Frame] = [Frame(i) for i in range(self.num_frames)]
        self.tabela_invertida: Dict[Tuple[str, int], int] = {}
        self.random = random.Random(seed)

        self.total_page_faults: int = 0
        self.total_page_hits: int = 0
        self.ultimo_evento: Optional[Dict[str, Any]] = None
        self.historico_requisicoes: List[Dict[str, Any]] = []
        self.paginas_disco: List[Dict[str, Any]] = []
        self.historico_swap: List[Dict[str, Any]] = []

    def gerar_requisicao_pagina(self, processo: Processo, tempo_atual: int) -> int:
        """
        Sorteia uma pagina do processo, acessa a RAM e retorna 1 em fault ou 0 em hit.
        """
        if processo.num_paginas <= 0:
            self.ultimo_evento = None
            return 0

        pagina_requisicao = self.random.randint(0, processo.num_paginas - 1)
        return self.acessar_pagina(processo, pagina_requisicao, tempo_atual)

    def acessar_pagina(self, processo: Processo, pagina_requisicao: int, tempo_atual: int) -> int:
        chave_pagina = (processo.id, pagina_requisicao)
        processo.ultima_pagina_requisitada = pagina_requisicao

        if chave_pagina in self.tabela_invertida:
            frame_indice = self.tabela_invertida[chave_pagina]
            frame = self.frames[frame_indice]
            frame.tempo_ultimo_uso = tempo_atual
            self.total_page_hits += 1
            processo.page_hits += 1

            self._registrar_evento({
                "tick": tempo_atual,
                "pid": processo.id,
                "pagina": pagina_requisicao,
                "resultado": "hit",
                "frame": frame_indice,
                "politica": self.politica,
                "substituido": None,
            })
            return 0

        self.total_page_faults += 1
        processo.page_faults += 1

        frame_livre = next((f for f in self.frames if not f.ocupado), None)
        estava_em_disco = self._pagina_esta_no_disco(processo.id, pagina_requisicao)

        if frame_livre:
            self._alocar_frame(frame_livre, processo.id, pagina_requisicao, tempo_atual)
            self._remover_pagina_disco(processo.id, pagina_requisicao)
            self._registrar_evento({
                "tick": tempo_atual,
                "pid": processo.id,
                "pagina": pagina_requisicao,
                "resultado": "fault",
                "frame": frame_livre.indice,
                "politica": self.politica,
                "substituido": None,
                "origem": "disco" if estava_em_disco else "nova",
            })
            return 1

        frame_substituir = self._escolher_frame_para_substituicao()
        substituido = self._remover_frame_da_tabela(frame_substituir, tempo_atual)

        self._alocar_frame(frame_substituir, processo.id, pagina_requisicao, tempo_atual)
        self._remover_pagina_disco(processo.id, pagina_requisicao)

        self._registrar_evento({
            "tick": tempo_atual,
            "pid": processo.id,
            "pagina": pagina_requisicao,
            "resultado": "fault",
            "frame": frame_substituir.indice,
            "politica": self.politica,
            "substituido": substituido,
            "origem": "disco" if estava_em_disco else "nova",
        })
        return 1

    def _alocar_frame(self, frame: Frame, pid: str, pagina_num: int, tempo_atual: int):
        frame.ocupado = True
        frame.processo_id = pid
        frame.numero_pagina = pagina_num
        frame.tempo_chegada = tempo_atual
        frame.tempo_ultimo_uso = tempo_atual
        self.tabela_invertida[(pid, pagina_num)] = frame.indice

    def _remover_frame_da_tabela(self, frame: Frame, tempo_atual: int) -> Optional[Dict[str, Any]]:
        if frame.processo_id is None or frame.numero_pagina is None:
            return None

        chave_antiga = (frame.processo_id, frame.numero_pagina)
        self.tabela_invertida.pop(chave_antiga, None)

        pagina_removida = {
            "pid": frame.processo_id,
            "pagina": frame.numero_pagina,
            "frame_origem": frame.indice,
            "tick": tempo_atual,
        }
        self.paginas_disco.append(pagina_removida)
        self.paginas_disco = self.paginas_disco[-40:]
        self.historico_swap.append(pagina_removida)
        self.historico_swap = self.historico_swap[-40:]
        return pagina_removida

    def _escolher_frame_para_substituicao(self) -> Frame:
        if self.politica == "FIFO":
            return min(self.frames, key=lambda f: f.tempo_chegada)

        if self.politica == "LRU":
            return min(self.frames, key=lambda f: f.tempo_ultimo_uso)

        return self.frames[0]

    def _pagina_esta_no_disco(self, pid: str, pagina: int) -> bool:
        return any(item["pid"] == pid and item["pagina"] == pagina for item in self.paginas_disco)

    def _remover_pagina_disco(self, pid: str, pagina: int):
        self.paginas_disco = [
            item for item in self.paginas_disco
            if not (item["pid"] == pid and item["pagina"] == pagina)
        ]

    def _registrar_evento(self, evento: Dict[str, Any]):
        self.ultimo_evento = evento
        self.historico_requisicoes.append(evento)
        self.historico_requisicoes = self.historico_requisicoes[-30:]

    def obter_status_memoria_para_visualizacao(self) -> Dict[str, Any]:
        frames_ram = [self._serializar_frame(frame) for frame in self.frames]
        processos_residentes = self._obter_processos_residentes()
        total_acessos = self.total_page_hits + self.total_page_faults
        taxa_fault = (self.total_page_faults / total_acessos * 100) if total_acessos else 0

        return {
            "politica": self.politica,
            "num_frames": self.num_frames,
            "frames_livres": sum(1 for f in self.frames if not f.ocupado),
            "frames_ocupados": sum(1 for f in self.frames if f.ocupado),
            "frames_ram": frames_ram,
            "tabela_invertida": [
                {"pid": pid, "pagina": num, "frame": frame_idx}
                for (pid, num), frame_idx in sorted(
                    self.tabela_invertida.items(),
                    key=lambda item: (item[1], item[0][0], item[0][1])
                )
            ],
            "processos_residentes": processos_residentes,
            "paginas_disco": list(self.paginas_disco),
            "historico_swap": list(self.historico_swap),
            "total_page_faults": self.total_page_faults,
            "total_page_hits": self.total_page_hits,
            "taxa_page_faults": taxa_fault,
            "ultima_requisicao": self.ultimo_evento,
            "historico_requisicoes": list(self.historico_requisicoes),
        }

    def _serializar_frame(self, frame: Frame) -> Dict[str, Any]:
        return {
            "indice": frame.indice,
            "ocupado": frame.ocupado,
            "processo_id": frame.processo_id,
            "pagina_num": frame.numero_pagina,
            "tempo_chegada": frame.tempo_chegada,
            "tempo_ultimo_uso": frame.tempo_ultimo_uso,
        }

    def _obter_processos_residentes(self) -> List[Dict[str, Any]]:
        por_processo: Dict[str, Dict[str, Any]] = {}
        for frame in self.frames:
            if not frame.ocupado or frame.processo_id is None or frame.numero_pagina is None:
                continue

            dados = por_processo.setdefault(
                frame.processo_id,
                {"pid": frame.processo_id, "paginas": [], "frames": []}
            )
            dados["paginas"].append(frame.numero_pagina)
            dados["frames"].append(frame.indice)

        residentes = []
        for dados in por_processo.values():
            paginas = sorted(set(dados["paginas"]))
            frames = sorted(dados["frames"])
            residentes.append({
                "pid": dados["pid"],
                "paginas": paginas,
                "frames": frames,
                "qtd_frames": len(frames),
            })

        return sorted(residentes, key=lambda item: item["pid"])
