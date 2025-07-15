"""CLEAR THE PATH - For each exerted character opponents have in play, you pay 1 ⬡ less to play this character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import CostReductionEffect
from ...target_selectors import SELF
from ...triggers import when_any_enters_play, when_leaves_play, or_conditions


def _clear_the_path_condition(character: Any, context: dict) -> bool:
    """Check for cost reduction based on opponents' exerted characters."""
    if not hasattr(character, 'controller') or not context.get('game_state'):
        return False
    
    game_state = context['game_state']
    controller = character.controller
    
    # Count exerted characters opponents control
    exerted_count = 0
    for player in game_state.players:
        if player != controller:  # Opponent
            for char in player.characters_in_play:
                if hasattr(char, 'is_exerted') and char.is_exerted:
                    exerted_count += 1
    
    # Store the reduction amount for the effect
    character._clear_the_path_reduction = exerted_count
    return exerted_count > 0


@register_named_ability("CLEAR THE PATH")
def create_clear_the_path(character: Any, ability_data: dict):
    """CLEAR THE PATH - For each exerted character opponents have in play, you pay 1 ⬡ less to play this character.
    
    Implementation: Monitor for any changes to character exertion state and adjust cost accordingly.
    """
    return quick_ability(
        "CLEAR THE PATH",
        character,
        or_conditions(
            when_any_enters_play(),
            when_leaves_play(None)
        ),
        SELF,
        CostReductionEffect(
            amount=lambda char, ctx: getattr(char, '_clear_the_path_reduction', 0),
            condition_func=_clear_the_path_condition
        )
    )