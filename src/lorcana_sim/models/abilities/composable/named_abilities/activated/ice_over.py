"""ICE OVER - Exert chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import EXERT
from ...target_selectors import ENEMY_CHARACTER
from ...triggers import on_activation


@register_named_ability("ICE OVER")
def create_ice_over(character: Any, ability_data: dict):
    """ICE OVER - Exert chosen opposing character.
    
    Implementation: Uses new choice-based architectural pattern for activated ability.
    """
    return (ComposableAbility("ICE OVER", character)
            .choice_effect(
                trigger_condition=on_activation(),
                target_selector=ENEMY_CHARACTER,
                effect=EXERT,
                name="ICE OVER"
            ))