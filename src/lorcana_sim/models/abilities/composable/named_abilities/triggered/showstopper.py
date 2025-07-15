"""SHOWSTOPPER - When you play this character, if you have a location in play, each opponent loses 1 lore."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import ConditionalEffect
from ...target_selectors import ALL_OPPONENTS
from ...triggers import when_enters_play


def _has_location_condition(character: Any, context: dict) -> bool:
    """Check if controller has a location in play."""
    if not hasattr(character, 'controller') or not context.get('game_state'):
        return False
    
    game_state = context['game_state']
    controller = character.controller
    
    # Check for any locations
    if hasattr(controller, 'locations_in_play'):
        return len(controller.locations_in_play) > 0
    
    return False


class LoseLoreEffect:
    """Effect that makes a player lose lore."""
    
    def __init__(self, amount: int):
        self.amount = amount
    
    def apply(self, target: Any, context: dict) -> Any:
        if hasattr(target, 'lore'):
            target.lore = max(0, target.lore - self.amount)
        return target
    
    def __str__(self) -> str:
        return f"lose {self.amount} lore"


@register_named_ability("SHOWSTOPPER")
def create_showstopper(character: Any, ability_data: dict):
    """SHOWSTOPPER - When you play this character, if you have a location in play, each opponent loses 1 lore.
    
    Implementation: When this character enters play, if you have a location, each opponent loses 1 lore.
    """
    return quick_ability(
        "SHOWSTOPPER",
        character,
        when_enters_play(character),
        ALL_OPPONENTS,
        ConditionalEffect(
            condition=_has_location_condition,
            effect=LoseLoreEffect(1)
        )
    )