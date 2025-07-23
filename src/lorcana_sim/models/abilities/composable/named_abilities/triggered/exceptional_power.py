"""EXCEPTIONAL POWER - When you play this character, exert all opposing characters."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import ExertCharacter
from ...target_selectors import CharacterSelector, and_filters
from ...triggers import when_enters_play


def opposing_character_filter(character: Any, context: dict) -> bool:
    """Filter for opposing characters."""
    ability_owner = context.get('ability_owner')
    if ability_owner and hasattr(ability_owner, 'controller'):
        return character.controller != ability_owner.controller
    return False


# Create selector for all opposing characters
ALL_OPPOSING_CHARACTERS = CharacterSelector(opposing_character_filter, count=999)


@register_named_ability("EXCEPTIONAL POWER")
def create_exceptional_power(character: Any, ability_data: dict):
    """EXCEPTIONAL POWER - When you play this character, exert all opposing characters.
    
    Implementation: When this character enters play, exert all opposing characters.
    """
    return quick_ability(
        "EXCEPTIONAL POWER",
        character,
        when_enters_play(character),
        ALL_OPPOSING_CHARACTERS,
        ExertCharacter()
    )