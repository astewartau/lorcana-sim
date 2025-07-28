"""Static named abilities - abilities that provide ongoing effects."""

from .voiceless import *
from .loyal import *
from .clear_the_path import *
from .take_point import *
from .phenomenal_showman import *
from .sinister_plot import *
from .quick_reflexes import *

__all__ = [
    'create_voiceless',
    'create_loyal',
    'create_clear_the_path',
    'create_take_point',
    'create_phenomenal_showman',
    'create_sinister_plot',
    'create_quick_reflexes'
]