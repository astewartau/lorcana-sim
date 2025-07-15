"""LOYAL - If you have a character named Gaston in play, you pay 1 ⬢ less to play this character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import CostReductionEffect
from ...target_selectors import SELF
from ...triggers import when_character_name_enters_play, when_character_name_leaves_play, or_conditions


def _loyal_condition(character: Any, context: dict) -> bool:
    """Check if controller has a character named Gaston in play."""
    if not hasattr(character, 'controller') or not context.get('game_state'):
        return False
    
    game_state = context['game_state']
    controller = character.controller
    
    # Check for Gaston
    for player in game_state.players:
        if player == controller:
            for char in player.characters_in_play:
                if hasattr(char, 'name') and 'Gaston' in char.name:
                    return True
    
    return False


@register_named_ability("LOYAL")
def create_loyal(character: Any, ability_data: dict):
    """LOYAL - If you have a character named Gaston in play, you pay 1 ⬢ less to play this character.
    
    Implementation: When Gaston enters or leaves play, adjust this character's cost.
    """
    return quick_ability(
        "LOYAL",
        character,
        or_conditions(
            when_character_name_enters_play("Gaston", character.controller),
            when_character_name_leaves_play("Gaston", character.controller)
        ),
        SELF,
        CostReductionEffect(
            amount=1,
            condition_func=_loyal_condition
        )
    )