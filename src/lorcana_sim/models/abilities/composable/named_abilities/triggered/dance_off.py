"""DANCE-OFF - Whenever this character or one of your characters named Mickey Mouse challenges another character, gain 1 lore."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GainLoreEffect
from ...target_selectors import CONTROLLER
from ...triggers import when_challenges, when_event, or_conditions
from ......engine.event_system import GameEvent


def mickey_mouse_challenges(character: Any):
    """Trigger when any Mickey Mouse controlled by the same player challenges."""
    def mickey_filter(challenger, event_context):
        # Check if challenger is controlled by same player and is named Mickey Mouse
        return (challenger.controller == character.controller and 
                hasattr(challenger, 'name') and 'Mickey Mouse' in challenger.name)
    
    return when_event(GameEvent.CHARACTER_CHALLENGES, 
                     source_filter=mickey_filter)


@register_named_ability("DANCE-OFF")
def create_dance_off(character: Any, ability_data: dict):
    """DANCE-OFF - Whenever this character or one of your characters named Mickey Mouse challenges another character, gain 1 lore.
    
    Implementation: When this character or any Mickey Mouse character challenges, gain 1 lore.
    Uses quick_ability since CONTROLLER doesn't require user choices.
    """
    
    # Use or_conditions to trigger on either self challenges or Mickey Mouse challenges
    return quick_ability(
        name="DANCE-OFF",
        character=character,
        trigger_condition=or_conditions(
            when_challenges(character),
            mickey_mouse_challenges(character)
        ),
        target_selector=CONTROLLER,
        effect=GainLoreEffect(1)
    )