"""SINISTER PLOT - Characters cost 1 ink less to play if you have 3 or more Villain characters in play."""

from typing import Any
from ..registry import register_named_ability
from ...conditional_effects import ConditionalEffect, ActivationZone, ConditionType
from ...cost_modification import create_ink_reduction_modifier, create_character_type_filter, create_controller_only_filter


@register_named_ability("SINISTER PLOT")
def create_sinister_plot(character: Any, ability_data: dict):
    """SINISTER PLOT - Characters cost 1 less if you have 3+ Villain characters.
    
    This creates a cost modifier that applies to all character cards when the condition is met.
    """
    
    def villain_count_condition(game_state, source_card):
        """Check if controller has 3 or more Villain characters in play."""
        # Find the source card's controller
        controller = None
        for player in game_state.players:
            if source_card in player.characters_in_play:
                controller = player
                break
        
        if not controller:
            return False
        
        # Count Villain characters controlled by this player
        villain_count = 0
        for char in controller.characters_in_play:
            if hasattr(char, 'has_subtype') and char.has_subtype('Villain'):
                villain_count += 1
        
        return villain_count >= 3
    
    def apply_cost_reduction(game_state, source_card):
        """Apply the cost reduction by activating the cost modifier."""
        # Find and activate the cost modifier for this character
        modifiers = game_state.cost_modification_manager.get_modifiers_by_source(source_card)
        for modifier in modifiers:
            if modifier.modifier_id == f"sinister_plot_{id(source_card)}":
                modifier.activate()
        
        return {
            'type': 'cost_modifier_applied',
            'modifier': 'SINISTER PLOT cost reduction',
            'source': source_card.name,
            'description': 'Characters cost 1 less (3+ Villains in play)'
        }
    
    def remove_cost_reduction(game_state, source_card):
        """Remove the cost reduction by deactivating the cost modifier."""
        # Find and deactivate the cost modifier for this character
        modifiers = game_state.cost_modification_manager.get_modifiers_by_source(source_card)
        for modifier in modifiers:
            if modifier.modifier_id == f"sinister_plot_{id(source_card)}":
                modifier.deactivate()
    
    # Create a filter that applies to all character cards
    def all_characters_filter(card, game_state):
        """Filter that applies to all character cards."""
        return hasattr(card, 'strength') and hasattr(card, 'willpower')  # Basic character check
    
    # Create the cost modifier
    cost_modifier = create_ink_reduction_modifier(
        modifier_id=f"sinister_plot_{id(character)}",
        source_card=character,
        reduction_amount=1,
        applies_to_filter=all_characters_filter,
        condition_func=villain_count_condition,
        priority=25  # Lower priority than individual character effects
    )
    
    # Create the conditional effect that manages the cost modifier
    sinister_plot_effect = ConditionalEffect(
        effect_id=f"sinister_plot_effect_{id(character)}",
        source_card=character,
        activation_zones={ActivationZone.PLAY},  # Only active when source is in play
        priority=25,
        condition_type=ConditionType.ZONE_BASED,  # Based on characters in play
        condition_func=villain_count_condition,
        effect_func=apply_cost_reduction,
        removal_func=remove_cost_reduction
    )
    
    # Register the cost modifier with the character
    character.metadata[f'sinister_plot_cost_modifier'] = cost_modifier
    
    # Add the conditional effect to the character
    character.add_conditional_effect(sinister_plot_effect)
    
    # Return None since this ability works through conditional effects
    return None