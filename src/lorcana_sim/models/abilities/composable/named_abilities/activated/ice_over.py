"""ICE OVER - Exert chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import EXERT
from ...target_selectors import ENEMY_CHARACTER
from ...triggers import on_activation


@register_named_ability("ICE OVER")
def create_ice_over(character: Any, ability_data: dict):
    """ICE OVER - Exert chosen opposing character.
    
    Implementation: Activated ability to exert an opposing character.
    """
    return quick_ability(
        "ICE OVER",
        character,
        on_activation(),
        ENEMY_CHARACTER,
        EXERT
    )