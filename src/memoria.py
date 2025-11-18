# memoria.py
from typing import List, Dict, Optional, Any, Tuple
import random
import math
import sys

try:
    from .processo import Processo
except ImportError:
    try:
        from processo import Processo
    except ImportError:
        print("Aviso: Classe 'Processo' não encontrada.", file=sys.stderr)
        class Processo: pass

# --- Constantes do Modelo Simplificado (Definidas no PDF) ---
TAMANHO_FRAME = 4 
TAMANHO_RAM_KB = 200 
NUM_FRAMES = math.ceil(TAMANHO_RAM_KB / TAMANHO_FRAME) # 50 frames de 4 KB

# --- Estruturas de Dados ---

class Frame:
    """Representa um frame físico na RAM."""
    def __init__(self, indice: int):
        self.indice = indice
        self.ocupado = False
        self.processo_id: Optional[str] = None
        self.numero_pagina: Optional[int] = None
        # Para políticas de substituição
        self.tempo_ultimo_uso: int = 0  # Para LRU
        self.tempo_chegada: int = 0      # Para FIFO

class GerenciadorMemoria:
    """
    Gerencia a alocação de frames e a política de substituição.
    Suporta FIFO ou LRU.
    """
    
    def __init__(self, politica: str = "FIFO", seed: int = 42):
        self.politica = politica.upper()
        self.frames: List[Frame] = [Frame(i) for i in range(NUM_FRAMES)]
        
        # Tabela de Páginas Invertida: Mapeia (ProcessoID, NumeroPagina) -> Frame
        self.tabela_invertida: Dict[Tuple[str, int], int] = {} 
        self.random = random.Random(seed)
        
        # Métrica
        self.total_page_faults: int = 0
        
        # print(f"Gerenciador de Memória iniciado. Frames: {NUM_FRAMES}. Política: {self.politica}")

    def gerar_requisicao_pagina(self, processo: Processo, tempo_atual: int) -> int:
        """
        Simula a geração de uma requisição de página. 
        
        1. Sorteia uma página (de 0 a Num_paginas - 1) do processo.
        2. Verifica se a página está na RAM.
        3. Se não estiver (Page Fault), aloca ou substitui.
        
        Retorna:
            0: Page Hit (Página na RAM)
            1: Page Fault (Página não está na RAM)
        """
        if processo.num_paginas == 0:
            return 0 # Não há páginas para gerenciar

        # 1. Sorteia uma página (o seed garante determinismo [cite: 32])
        pagina_requisicao = self.random.randint(0, processo.num_paginas - 1)
        
        chave_pagina = (processo.id, pagina_requisicao)
        
        # 2. Verifica se a página está na RAM (Page Hit)
        if chave_pagina in self.tabela_invertida:
            frame_indice = self.tabela_invertida[chave_pagina]
            frame = self.frames[frame_indice]
            
            # Atualiza LRU (se aplicável)
            if self.politica == "LRU":
                frame.tempo_ultimo_uso = tempo_atual
                
            return 0 # Page Hit

        # 3. Page Fault
        self.total_page_faults += 1
        processo.page_faults += 1 # Contagem total de page faults por processo [cite: 110]
        
        # Tenta alocar um frame livre
        frame_livre = next((f for f in self.frames if not f.ocupado), None)
        
        if frame_livre:
            # Alocação (Frame Vazio)
            self._alocar_frame(frame_livre, processo.id, pagina_requisicao, tempo_atual)
            return 1 # Page Fault

        # 4. Substituição (Não há frame livre)
        frame_substituir = self._escolher_frame_para_substituicao()
        
        # Remove a página antiga da Tabela Invertida
        chave_antiga = (frame_substituir.processo_id, frame_substituir.numero_pagina)
        if chave_antiga in self.tabela_invertida:
            del self.tabela_invertida[chave_antiga]
            
        # Aloca o novo frame
        self._alocar_frame(frame_substituir, processo.id, pagina_requisicao, tempo_atual)
        
        return 1 # Page Fault
        
    def _alocar_frame(self, frame: Frame, pid: str, pagina_num: int, tempo_atual: int):
        """Preenche os dados de um frame e o mapeia na Tabela Invertida."""
        frame.ocupado = True
        frame.processo_id = pid
        frame.numero_pagina = pagina_num
        frame.tempo_chegada = tempo_atual
        frame.tempo_ultimo_uso = tempo_atual
        
        self.tabela_invertida[(pid, pagina_num)] = frame.indice

    def _escolher_frame_para_substituicao(self) -> Frame:
        """
        Implementa a política de substituição (FIFO ou LRU).
        """
        if self.politica == "FIFO":
            # Escolhe o frame que chegou há mais tempo
            return min(self.frames, key=lambda f: f.tempo_chegada)
            
        elif self.politica == "LRU":
            # Escolhe o frame que foi usado há mais tempo
            return min(self.frames, key=lambda f: f.tempo_ultimo_uso)
            
        # Fallback
        return self.frames[0]

    def obter_status_memoria_para_visualizacao(self) -> Dict[str, Any]:
        """
        Retorna o estado da memória para ser plotado.
        """
        status = {
            "frames_ram": [
                {
                    "indice": f.indice, 
                    "ocupado": f.ocupado, 
                    "processo_id": f.processo_id, 
                    "pagina_num": f.numero_pagina
                } for f in self.frames
            ],
            "tabela_invertida": [
                {"pid": pid, "pagina": num, "frame": frame_idx}
                for (pid, num), frame_idx in self.tabela_invertida.items()
            ],
            "total_page_faults": self.total_page_faults
        }
        return status