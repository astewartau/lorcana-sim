"""TALE OF THE FIFTH SPIRIT - When you play this character, if an opponent has an exerted character in play, gain 1 lore."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GAIN_LORE, ConditionalEffect
from ...target_selectors import CONTROLLER
from ...triggers import when_enters_play


def _opponent_has_exerted_condition(character: Any, context: dict) -> bool:
    """Check if any opponent has an exerted character in play."""
    if not hasattr(character, 'controller') or not context.get('game_state'):
        return False
    
    game_state = context['game_state']
    controller = character.controller
    
    # Check for exerted characters controlled by opponents
    for player in game_state.players:
        if player != controller:  # Opponent
            for char in player.characters_in_play:
                if hasattr(char, 'exerted') and char.exerted:
                    return True
    
    return False


@register_named_ability("TALE OF THE FIFTH SPIRIT")
def create_tale_of_the_fifth_spirit(character: Any, ability_data: dict):
    """TALE OF THE FIFTH SPIRIT - When you play this character, if an opponent has an exerted character in play, gain 1 lore.
    
    Implementation: When this character enters play, if any opponent has an exerted character, gain 1 lore.
    """
    return quick_ability(
        "TALE OF THE FIFTH SPIRIT",
        character,
        when_enters_play(character),
        CONTROLLER,
        ConditionalEffect(
            condition=_opponent_has_exerted_condition,
            effect=GAIN_LORE(1)
        )
    )