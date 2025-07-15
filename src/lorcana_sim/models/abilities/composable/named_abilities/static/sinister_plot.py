"""SINISTER PLOT - This character gets +1 ◇ for each other Villain character you have in play."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import ConditionalStatBonus
from ...target_selectors import SELF
from ...triggers import when_character_type_enters_play, when_character_type_leaves_play, or_conditions


def _sinister_plot_condition(character: Any, context: dict) -> bool:
    """Count other Villain characters controlled by same player."""
    if not hasattr(character, 'controller') or not context.get('game_state'):
        return False
    
    game_state = context['game_state']
    controller = character.controller
    
    # Count other Villain characters
    villain_count = 0
    for player in game_state.players:
        if player == controller:
            for char in player.characters_in_play:
                if (char != character and 
                    hasattr(char, 'subtypes') and 
                    'Villain' in char.subtypes):
                    villain_count += 1
    
    # Apply +1 ◇ for each other Villain
    if hasattr(character, 'base_willpower'):
        character.willpower = character.base_willpower + villain_count
    
    return villain_count > 0


@register_named_ability("SINISTER PLOT")
def create_sinister_plot(character: Any, ability_data: dict):
    """SINISTER PLOT - This character gets +1 ◇ for each other Villain character you have in play.
    
    Implementation: When any Villain enters or leaves play, recalculate this character's willpower.
    """
    return quick_ability(
        "SINISTER PLOT",
        character,
        or_conditions(
            when_character_type_enters_play("Villain", character.controller),
            when_character_type_leaves_play("Villain", character.controller)
        ),
        SELF,
        ConditionalStatBonus(
            willpower=0,  # Dynamic based on condition
            condition_func=_sinister_plot_condition
        )
    )