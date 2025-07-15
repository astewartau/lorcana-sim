"""CRYSTALLIZE - When you play this character, exert chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import EXERT
from ...target_selectors import ENEMY_CHARACTER
from ...triggers import when_enters_play


@register_named_ability("CRYSTALLIZE")
def create_crystallize(character: Any, ability_data: dict):
    """CRYSTALLIZE - When you play this character, exert chosen opposing character.
    
    Implementation: When this character enters play, choose and exert an opposing character.
    """
    return quick_ability(
        "CRYSTALLIZE",
        character,
        when_enters_play(character),
        ENEMY_CHARACTER,
        EXERT
    )