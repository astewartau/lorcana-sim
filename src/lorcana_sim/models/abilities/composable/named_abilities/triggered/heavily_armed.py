"""HEAVILY ARMED - Whenever you draw a card, this character gains Challenger +1 this turn. (They get +1 ¤ while challenging.)"""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import ChallengerEffect
from ...target_selectors import SELF
from ...triggers import when_card_drawn


@register_named_ability("HEAVILY ARMED")
def create_heavily_armed(character: Any, ability_data: dict):
    """HEAVILY ARMED - Whenever you draw a card, this character gains Challenger +1 this turn.
    
    Implementation: When controller draws a card, this character gains Challenger +1 until end of turn.
    """
    # Create temporary challenger effect that lasts until end of turn
    temporary_challenger = ChallengerEffect(1, "until_end_of_turn")
    
    return quick_ability(
        "HEAVILY ARMED",
        character,
        when_card_drawn(character),  # Pass character instead of character.controller for late binding
        SELF,
        temporary_challenger
    )