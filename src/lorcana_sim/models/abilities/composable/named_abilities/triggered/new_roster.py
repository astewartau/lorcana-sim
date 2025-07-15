"""NEW ROSTER - Once per turn, when this character moves to a location, gain 2 lore."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GAIN_LORE, ConditionalEffect
from ...target_selectors import CONTROLLER
from ...triggers import when_moves_to_location


@register_named_ability("NEW ROSTER")
def create_new_roster(character: Any, ability_data: dict):
    """NEW ROSTER - Once per turn, when this character moves to a location, gain 2 lore.
    
    Implementation: When this character moves to a location, gain 2 lore (once per turn).
    """
    # Add once-per-turn tracking
    character._new_roster_used_this_turn = False
    
    def once_per_turn_condition(character: Any, context: dict) -> bool:
        """Check if ability hasn't been used this turn."""
        if getattr(character, '_new_roster_used_this_turn', False):
            return False
        character._new_roster_used_this_turn = True
        return True
    
    return quick_ability(
        "NEW ROSTER",
        character,
        when_moves_to_location(character),
        CONTROLLER,
        ConditionalEffect(
            condition=once_per_turn_condition,
            effect=GAIN_LORE(2)
        )
    )