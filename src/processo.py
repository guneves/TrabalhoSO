# processo.py
import math
from typing import Optional

class Processo:
    """
    Representa um único processo no simulador.
    """
    
    def __init__(self, 
                 id: str, 
                 chegada: int, 
                 execucao: int, 
                 prioridade: int, 
                 deadline: int,          
                 deadline_relativo: int, 
                 num_paginas: int = 0): # <-- Adição de num_paginas
        
        self.id: str = id
        self.chegada: int = chegada
        self.execucao: int = execucao           
        self.prioridade: int = prioridade         
        self.deadline: int = deadline     
        self.deadline_relativo: int = deadline_relativo     
        self.num_paginas: int = num_paginas   

        self.tempo_restante: int = self.execucao
        self.status: str = "pronto"  
        self.vruntime: float = 0.0      
        self.num_preempcoes: int = 0    

        # Atributos de Estado de Memória (Bônus)
        self.page_faults: int = 0 
        self.status_memoria: str = "pronto" # Novo estado: "bloqueado_mem"

        self.tempo_termino: Optional[int] = None
        self.tempo_primeira_execucao: Optional[int] = None
        
        self.turnaround: Optional[int] = None
        self.tempo_espera: Optional[int] = None
        self.deadline_ok: Optional[bool] = None

    def calcular_metricas_finais(self, custo_sobrecarga: int = 0) -> None:
        """
        Calcula as métricas de desempenho do processo.
        """
        if self.tempo_termino is None:
            print(f"ERRO: Tentando calcular métricas para {self.id} que não terminou.")
            return

        self.turnaround = self.tempo_termino - self.chegada

        sobrecarga_total = self.num_preempcoes * custo_sobrecarga
        
        self.tempo_espera = (self.turnaround + 1) - self.execucao - sobrecarga_total
        
        self.deadline_ok = self.tempo_termino <= self.deadline

    def __repr__(self) -> str:
        return (f"Processo(id='{self.id}', "
                f"chegada={self.chegada}, "
                f"exec={self.execucao}, "
                f"restante={self.tempo_restante}, "
                f"deadline={self.deadline}, "
                f"status='{self.status}', "
                f"pages={self.num_paginas})")