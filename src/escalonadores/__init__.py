from .base import EscalonadorBase
from .fifo import EscalonadorFIFO
from .sjf import EscalonadorSJF
from .round_robin import EscalonadorRoundRobin
from .edf import EscalonadorEDF
#from .cfs import EscalonadorCFSSim

__all__ = [
    'EscalonadorBase',
    'EscalonadorFIFO',
    'EscalonadorSJF',
    'EscalonadorRoundRobin',
    'EscalonadorEDF',
    'EscalonadorCFSSim'
]

"""
Para Imports em outros módulos:
from src.escalonadores import EscalonadorFIFO, EscalonadorSJF, EscalonadorEDF
"""