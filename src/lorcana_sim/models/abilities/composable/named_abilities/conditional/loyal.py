"""LOYAL - This character costs 1 ink less to play if you have a character named [X] in play."""

from typing import Any
from ..registry import register_named_ability
from ...conditional_effects import ConditionalEffect, ActivationZone, ConditionType
from ...cost_modification import create_ink_reduction_modifier, create_controller_only_filter
from ...condition_evaluator import create_character_present_condition


@register_named_ability("LOYAL")
def create_loyal(character: Any, ability_data: dict):
    """LOYAL - Character costs 1 less if specific character is in play.
    
    This creates a cost modifier that activates when the required character is present.
    The required character name should be specified in ability_data['loyal_to'].
    """
    
    # Get the character this ability is loyal to
    loyal_to_name = ability_data.get('loyal_to', 'Unknown')
    
    def apply_cost_reduction(game_state, source_card):
        """Apply the cost reduction by activating the cost modifier."""
        # Find and activate the cost modifier for this character
        modifiers = game_state.cost_modification_manager.get_modifiers_by_source(source_card)
        for modifier in modifiers:
            if modifier.modifier_id == f"loyal_{id(source_card)}":
                modifier.activate()
        
        return {
            'type': 'cost_modifier_applied',
            'modifier': 'LOYAL cost reduction',
            'target': source_card.name,
            'loyal_to': loyal_to_name
        }
    
    def remove_cost_reduction(game_state, source_card):
        """Remove the cost reduction by deactivating the cost modifier."""
        # Find and deactivate the cost modifier for this character
        modifiers = game_state.cost_modification_manager.get_modifiers_by_source(source_card)
        for modifier in modifiers:
            if modifier.modifier_id == f"loyal_{id(source_card)}":
                modifier.deactivate()
    
    # Create the cost modifier
    cost_modifier = create_ink_reduction_modifier(
        modifier_id=f"loyal_{id(character)}",
        source_card=character,
        reduction_amount=1,
        applies_to_filter=lambda card, gs: card == character,  # Only applies to this character
        condition_func=create_character_present_condition(loyal_to_name, controller_only=True),
        priority=50  # Medium priority
    )
    
    # Create the conditional effect that manages the cost modifier
    loyal_effect = ConditionalEffect(
        effect_id=f"loyal_effect_{id(character)}",
        source_card=character,
        activation_zones={ActivationZone.HAND, ActivationZone.PLAY},  # Active in hand and play
        priority=50,
        condition_type=ConditionType.ZONE_BASED,
        condition_func=create_character_present_condition(loyal_to_name, controller_only=True),
        effect_func=apply_cost_reduction,
        removal_func=remove_cost_reduction
    )
    
    # Register the cost modifier with the character
    character.metadata[f'loyal_cost_modifier'] = cost_modifier
    
    # Add the conditional effect to the character
    character.add_conditional_effect(loyal_effect)
    
    # Return None since this ability works through conditional effects
    return None