"""Named ability implementations for Lorcana cards."""

from .registry import NamedAbilityRegistry, register_named_ability
from .static import *
from .triggered import *
from .activated import *
from .conditional import *

__all__ = [
    'NamedAbilityRegistry',
    'register_named_ability'
]