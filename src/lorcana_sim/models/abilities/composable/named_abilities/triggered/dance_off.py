"""DANCE-OFF - Whenever this character or one of your characters named Mickey Mouse challenges another character, gain 1 lore."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GAIN_LORE
from ...target_selectors import CONTROLLER
from ...triggers import when_challenges, or_conditions


@register_named_ability("DANCE-OFF")
def create_dance_off(character: Any, ability_data: dict):
    """DANCE-OFF - Whenever this character or one of your characters named Mickey Mouse challenges another character, gain 1 lore.
    
    Implementation: When this character or any Mickey Mouse character challenges, gain 1 lore.
    """
    def mickey_mouse_challenge_trigger(character: Any):
        """Trigger for when any Mickey Mouse character challenges."""
        def trigger_func(event, context):
            if event.type != "character_challenges":
                return False
            
            challenger = event.data.get('challenger')
            if not challenger or not hasattr(challenger, 'controller'):
                return False
            
            # Check if challenger is controlled by same player and is named Mickey Mouse
            if (challenger.controller == character.controller and 
                hasattr(challenger, 'name') and 'Mickey Mouse' in challenger.name):
                return True
            
            return False
        return trigger_func
    
    return quick_ability(
        "DANCE-OFF",
        character,
        or_conditions(
            when_challenges(character),
            mickey_mouse_challenge_trigger(character)
        ),
        CONTROLLER,
        GAIN_LORE(1)
    )