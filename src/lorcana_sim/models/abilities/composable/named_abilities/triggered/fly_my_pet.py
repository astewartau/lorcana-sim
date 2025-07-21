"""FLY, MY PET! - When this character is banished, you may draw a card."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import DRAW_CARD
from ...target_selectors import CONTROLLER
from ...triggers import when_banished


@register_named_ability("FLY, MY PET!")
def create_fly_my_pet(character: Any, ability_data: dict):
    """FLY, MY PET! - When this character is banished, you may draw a card.
    
    Implementation: Uses new choice-based architectural pattern with optional choice.
    """
    return (ComposableAbility("FLY, MY PET!", character)
            .choice_effect(
                trigger_condition=when_banished(character),
                target_selector=CONTROLLER,
                effect=DRAW_CARD,
                name="FLY, MY PET!"
            ))