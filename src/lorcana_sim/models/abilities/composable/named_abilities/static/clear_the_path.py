"""CLEAR THE PATH - For each exerted character opponents have in play, you pay 1 ⬡ less to play this character."""

from typing import Any, Dict
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import DynamicCostModification
from ...target_selectors import SELF
from ...triggers import when_character_exerts, when_character_readies, when_enters_play, when_any_enters_play, when_leaves_play, when_any_leaves_play, or_conditions


def _calculate_cost_reduction_condition(character):
    """Create a condition function that calculates cost reduction based on opponent exerted characters."""
    def condition(target: Any, context: Dict[str, Any]) -> bool:
        """Always return True - the cost modifier will calculate the actual reduction dynamically."""
        return True
    return condition


def _calculate_exerted_opponents(character):
    """Create a dynamic cost calculation function for CLEAR THE PATH."""
    def cost_calculator(target: Any, context: Dict[str, Any]) -> int:
        """Calculate cost reduction based on number of exerted opponent characters."""
        game_state = context.get('game_state')
        if not game_state or not hasattr(character, 'controller'):
            return 0
        
        controller = character.controller
        exerted_count = 0
        
        # Count exerted characters opponents control
        for player in game_state.players:
            if player != controller:  # Opponent
                for char in player.characters_in_play:
                    if hasattr(char, 'exerted') and char.exerted:
                        exerted_count += 1
        
        # Return negative value for cost reduction
        return -exerted_count
    
    return cost_calculator


@register_named_ability("CLEAR THE PATH")
def create_clear_the_path(character: Any, ability_data: dict):
    """CLEAR THE PATH - For each exerted character opponents have in play, you pay 1 ⬡ less to play this character.
    
    Implementation: Dynamic cost modification based on opponents' exerted character count.
    """
    
    # Create dynamic cost modification that recalculates based on board state
    cost_modifier_effect = DynamicCostModification(
        cost_modifier=_calculate_exerted_opponents(character),  # Dynamic calculation function
        condition=_calculate_cost_reduction_condition(character),  # Always active
        applies_to="self"
    )
    
    # Evaluate when exertion states change or characters enter/leave play
    evaluation_trigger = or_conditions(
        when_character_exerts(),     # Any character becomes exerted
        when_character_readies(),    # Any character becomes readied
        when_any_enters_play(),      # Any character enters play  
        when_any_leaves_play(),      # Any character leaves play
        when_enters_play(character)  # This character enters play (initial setup)
    )
    
    return quick_ability(
        "CLEAR THE PATH",
        character,
        evaluation_trigger,
        SELF,
        cost_modifier_effect
    )