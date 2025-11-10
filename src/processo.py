# src/processo.py
import math
from typing import Optional

class Processo:
    """
    Representa um único processo no simulador.

    Esta classe armazena todos os atributos definidos no documento do trabalho,
    incluindo:
    1. Atributos de Entrada: Lidos do JSON (id, chegada, execucao, etc.)
    2. Atributos de Estado: Usados pelo simulador (tempo_restante, status, etc.)
    3. Atributos de Métrica: Calculados ao final da simulação (turnaround, etc.)
    """
    
    def __init__(self, 
                 id: str, 
                 chegada: int, 
                 execucao: int, 
                 prioridade: int, 
                 deadline: int, 
                 num_paginas: int = 0):
        
        self.id: str = id
        self.chegada: int = chegada
        self.execucao: int = execucao           
        self.prioridade: int = prioridade         
        self.deadline: int = deadline          
        self.num_paginas: int = num_paginas   

        self.tempo_restante: int = self.execucao
        self.status: str = "pronto"  
        self.vruntime: float = 0.0          

        self.tempo_termino: Optional[int] = None
        self.tempo_primeira_execucao: Optional[int] = None
        
        self.turnaround: Optional[int] = None
        self.tempo_espera: Optional[int] = None
        self.deadline_ok: Optional[bool] = None

    def calcular_metricas_finais(self):
        """
        Calcula as métricas de desempenho do processo.
        Deve ser chamado pelo simulador *após* o processo terminar.
        """
        if self.tempo_termino is None:
            print(f"ERRO: Tentando calcular métricas para {self.id} que não terminou.")
            return

        #TURNAROUND = TEMPO_DE_TÉRMINO - TEMPO_DE_CHEGADA !!!
        self.turnaround = self.tempo_termino - self.chegada
        
        #TEMPO_DE_ESPERA = TURNAROUND - TEMPO_DE_EXECUÇÃO !!!
        self.tempo_espera = self.turnaround - self.execucao
        
        #VERIFICA SE ATENDEU O DEADLINE
        self.deadline_ok = self.tempo_termino <= self.deadline

    def __repr__(self) -> str:
        """Representação em string para facilitar."""
        return (f"Processo(id='{self.id}', "
                f"chegada={self.chegada}, "
                f"exec={self.execucao}, "
                f"restante={self.tempo_restante}, "
                f"deadline={self.deadline}, "
                f"status='{self.status}')")