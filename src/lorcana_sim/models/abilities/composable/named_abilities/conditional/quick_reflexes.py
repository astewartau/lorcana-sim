"""QUICK REFLEXES - Evasive (Only characters with Evasive can challenge this character.)
But only during the controller's turn.
"""

from typing import Any
from ..registry import register_named_ability
from ...conditional_effects import ConditionalEffect, ActivationZone, ConditionType
from ...condition_evaluator import create_turn_based_condition


@register_named_ability("QUICK REFLEXES CONDITIONAL")
def create_quick_reflexes_conditional(character: Any, ability_data: dict):
    """QUICK REFLEXES - Evasive during controller's turn only.
    
    This is a conditional effect that applies/removes Evasive based on whose turn it is.
    """
    
    def apply_evasive_effect(game_state, source_card):
        """Apply the Evasive effect."""
        source_card.metadata['has_evasive'] = True
        return {
            'description': 'QUICK REFLEXES: gained Evasive during controller\'s turn',
            'ability': 'Evasive',
            'reason': 'QUICK REFLEXES'
        }
    
    def remove_evasive_effect(game_state, source_card):
        """Remove the Evasive effect."""
        source_card.metadata.pop('has_evasive', None)
    
    # Create the conditional effect
    quick_reflexes_effect = ConditionalEffect(
        effect_id=f"quick_reflexes_{id(character)}",
        source_card=character,
        activation_zones={ActivationZone.PLAY},  # Only active when character is in play
        priority=100,  # High priority for keyword abilities
        condition_type=ConditionType.TURN_BASED,
        condition_func=create_turn_based_condition(during_controllers_turn=True),
        effect_func=apply_evasive_effect,
        removal_func=remove_evasive_effect
    )
    
    # Add the conditional effect to the character
    character.add_conditional_effect(quick_reflexes_effect)
    
    # Return None since this ability works through conditional effects
    return None