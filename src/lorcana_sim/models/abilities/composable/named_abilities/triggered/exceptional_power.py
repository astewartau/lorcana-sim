"""EXCEPTIONAL POWER - When you play this character, exert all opposing characters."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import ExertCharacter
from ...target_selectors import ALL_OPPONENTS
from ...triggers import when_enters_play


@register_named_ability("EXCEPTIONAL POWER")
def create_exceptional_power(character: Any, ability_data: dict):
    """EXCEPTIONAL POWER - When you play this character, exert all opposing characters.
    
    Implementation: When this character enters play, exert all opposing characters.
    """
    return quick_ability(
        "EXCEPTIONAL POWER",
        character,
        when_enters_play(character),
        ALL_OPPONENTS,
        ExertCharacter()
    )