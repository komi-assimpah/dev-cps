"""
Module spatial pour la gestion de grilles 2D d'appartements.
Copié et adapté de dev_iot_omlette.
"""

from .cell import Cell
from .converter import FlatConverter
from .loader import FlatLoader

__all__ = ['Cell', 'FlatConverter', 'FlatLoader']
