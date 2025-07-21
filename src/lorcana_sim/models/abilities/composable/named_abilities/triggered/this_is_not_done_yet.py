"""THIS IS NOT DONE YET - During an opponent's turn, whenever one of your Illusion characters is banished, you may return that card to your hand."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import RETURN_TO_HAND, ConditionalEffect
from ...target_selectors import EVENT_SOURCE
from ...triggers import when_banished
from ...condition_builders import during_opponent_turn, is_illusion, same_controller


@register_named_ability("THIS IS NOT DONE YET")
def create_this_is_not_done_yet(character: Any, ability_data: dict):
    """THIS IS NOT DONE YET - During an opponent's turn, whenever one of your Illusion characters is banished, you may return that card to your hand.
    
    Implementation: Uses new choice-based architectural pattern with optional choice.
    """
    # Create the enhanced condition using the new condition builders
    condition = during_opponent_turn(character) & is_illusion() & same_controller(character)
    
    # Convert our Condition object to a function for ConditionalEffect
    def condition_func(target: Any, context: dict) -> bool:
        return condition.evaluate(target, context)
    
    # Create the complete trigger condition that includes banishment + all conditions
    def complete_trigger_condition(event_context):
        """Check if this is a banishment event during opponent's turn of an Illusion character controlled by us."""
        if not when_banished(None)(event_context):
            return False
        
        # Get the banished character from the event
        banished_character = event_context.source
        if not banished_character:
            return False
        
        # Create a context dict for the condition evaluation
        context = {
            'event_context': event_context,
            'game_state': event_context.game_state,
            'source': banished_character,
            'ability_owner': character
        }
        
        return condition_func(banished_character, context)
    
    # Since this is a "may" effect, we still need a choice even when conditions are met
    # Use EVENT_SOURCE selector with optional=True to enable the "may" behavior
    return (ComposableAbility("THIS IS NOT DONE YET", character)
            .choice_effect(
                trigger_condition=complete_trigger_condition,
                target_selector=EVENT_SOURCE,  # The banished character
                effect=RETURN_TO_HAND,
                name="THIS IS NOT DONE YET"
            ))