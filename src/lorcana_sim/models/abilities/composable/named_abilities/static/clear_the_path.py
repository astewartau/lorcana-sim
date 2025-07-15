"""CLEAR THE PATH - For each exerted character opponents have in play, you pay 1 ⬡ less to play this character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import CostModification
from ...target_selectors import SELF
from ...triggers import when_any_enters_play, when_leaves_play, or_conditions


class ClearThePathEffect:
    """Dynamic cost reduction based on opponents' exerted characters."""
    
    def apply(self, target: Any, context: dict) -> Any:
        if not hasattr(target, 'controller') or not context.get('game_state'):
            return target
        
        game_state = context['game_state']
        controller = target.controller
        
        # Count exerted characters opponents control
        exerted_count = 0
        for player in game_state.players:
            if player != controller:  # Opponent
                for char in player.characters_in_play:
                    if hasattr(char, 'exerted') and char.exerted:
                        exerted_count += 1
        
        # Apply cost reduction equal to number of exerted opponents
        if exerted_count > 0:
            cost_reduction = CostModification(cost_change=-exerted_count)
            cost_reduction.apply(target, context)
        
        return target
    
    def get_events(self, target: Any, context: dict, result: Any) -> list:
        return []
    
    def __str__(self) -> str:
        return "reduce cost by 1 for each exerted opponent character"


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
        ClearThePathEffect()
    )