"""THIS IS NOT DONE YET - During an opponent's turn, whenever one of your Illusion characters is banished, you may return that card to your hand."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import RETURN_TO_HAND
from ...target_selectors import EVENT_SOURCE
from ...triggers import when_banished
from ...condition_builders import during_opponent_turn, is_illusion, same_controller
from ......engine.choice_system import may_effect


@register_named_ability("THIS IS NOT DONE YET")
def create_this_is_not_done_yet(character: Any, ability_data: dict):
    """THIS IS NOT DONE YET - During an opponent's turn, whenever one of your Illusion characters is banished, you may return that card to your hand.
    
    Implementation: Uses new choice system for "may" effect and enhanced conditions for complex trigger.
    """
    # Create the enhanced condition using the new condition builders
    condition = during_opponent_turn(character) & is_illusion() & same_controller(character)
    
    # Create the "may" choice effect
    choice_effect = may_effect(
        prompt="Return this Illusion character to your hand?",
        effect=RETURN_TO_HAND,
        ability_name="THIS IS NOT DONE YET"
    )
    
    # Use the existing ConditionalEffect but with our enhanced condition and choice effect
    from ...effects import ConditionalEffect
    
    # Convert our Condition object to a function for ConditionalEffect
    def condition_func(target: Any, context: dict) -> bool:
        return condition.evaluate(target, context)
    
    return quick_ability(
        "THIS IS NOT DONE YET",
        character,
        when_banished(None),  # Any character being banished
        EVENT_SOURCE,  # The banished character
        ConditionalEffect(
            condition=condition_func,
            effect=choice_effect
        )
    )