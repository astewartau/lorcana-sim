"""LOYAL - If you have a character named Gaston in play, you pay 1 ⬢ less to play this character."""

from typing import Any, Dict
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import DynamicCostModification
from ...target_selectors import SELF
from ...triggers import when_enters_play, when_leaves_play, or_conditions


def _has_gaston_in_play_condition(character):
    """Create a condition function that checks if player has a Gaston character in play."""
    def condition(target: Any, context: Dict[str, Any]) -> bool:
        """Check if the character's controller has a Gaston in play."""
        game_state = context.get('game_state')
        if not game_state or not hasattr(character, 'controller'):
            return False
        
        controller = character.controller
        
        # Check for any character with "Gaston" in the name
        for char in controller.characters_in_play:
            if hasattr(char, 'name') and 'Gaston' in char.name:
                return True
        
        return False
    
    return condition


def _calculate_gaston_cost_reduction(character):
    """Create a dynamic cost calculation function for LOYAL."""
    def cost_calculator(target: Any, context: Dict[str, Any]) -> int:
        """Calculate cost reduction: -1 if Gaston is in play, 0 otherwise."""
        game_state = context.get('game_state')
        if not game_state or not hasattr(character, 'controller'):
            return 0
        
        controller = character.controller
        
        # Check for any character with "Gaston" in the name
        for char in controller.characters_in_play:
            if hasattr(char, 'name') and 'Gaston' in char.name:
                return -1  # Negative value for cost reduction
        
        return 0  # No reduction if no Gaston found
    
    return cost_calculator


@register_named_ability("LOYAL")
def create_loyal(character: Any, ability_data: dict):
    """LOYAL - If you have a character named Gaston in play, you pay 1 ⬢ less to play this character.
    
    Implementation: Dynamic cost modification based on presence of Gaston characters.
    """
    
    # Create dynamic cost modification that checks for Gaston
    cost_modifier_effect = DynamicCostModification(
        cost_modifier=_calculate_gaston_cost_reduction(character),  # Dynamic calculation function
        condition=_has_gaston_in_play_condition(character),  # Check for Gaston presence
        applies_to="self"
    )
    
    # Evaluate when characters enter or leave play (Gaston state changes)
    evaluation_trigger = or_conditions(
        when_enters_play(None),         # Any character enters play (could be Gaston)
        when_leaves_play(None),         # Any character leaves play (could be Gaston)
        when_enters_play(character)     # This character enters play (initial setup)
    )
    
    return quick_ability(
        "LOYAL",
        character,
        evaluation_trigger,
        SELF,
        cost_modifier_effect
    )