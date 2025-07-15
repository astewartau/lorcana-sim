"""RECURRING GUST - When this character is banished in a challenge, return this card to your hand."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import RETURN_TO_HAND
from ...target_selectors import SELF
from ...triggers import when_banished_in_challenge


@register_named_ability("RECURRING GUST")
def create_recurring_gust(character: Any, ability_data: dict):
    """RECURRING GUST - When this character is banished in a challenge, return this card to your hand.
    
    Implementation: When this character is banished in a challenge, return to hand.
    """
    return quick_ability(
        "RECURRING GUST",
        character,
        when_banished_in_challenge(character),
        SELF,
        RETURN_TO_HAND
    )