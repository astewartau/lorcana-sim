"""MUSICAL DEBUT - When you play this character, look at the top 4 cards of your deck. 
You may reveal a song card and put it into your hand. Put the rest on the bottom of your deck in any order."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import LOOK_AT_TOP_4
from ...target_selectors import NO_TARGET
from ...triggers import when_enters_play


@register_named_ability("MUSICAL DEBUT")
def create_musical_debut(character: Any, ability_data: dict):
    """MUSICAL DEBUT - When you play this character, look at the top 4 cards of your deck.
    You may reveal a song card and put it into your hand. Put the rest on the bottom of your deck in any order.
    
    Implementation: When this character enters play, trigger deck manipulation effect.
    """
    return quick_ability(
        "MUSICAL DEBUT",
        character,
        when_enters_play(character),
        NO_TARGET,
        LOOK_AT_TOP_4
    )