"""REFRESHING BREAK - Whenever you ready this character, gain 1 lore for each 1 damage on him."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...target_selectors import CONTROLLER
from ...triggers import when_character_readies


class GainLorePerDamageEffect:
    """Effect that gains lore equal to damage on character."""
    
    def apply(self, target: Any, context: dict) -> Any:
        # Get the character that was readied (the source of the event)
        readied_character = context.get('event_context', {}).get('source')
        if not readied_character:
            # Fallback to ability owner
            readied_character = context.get('ability_owner')
        
        if readied_character and hasattr(readied_character, 'damage'):
            damage_amount = readied_character.damage
            if damage_amount > 0 and hasattr(target, 'gain_lore'):
                target.gain_lore(damage_amount)
        
        return target
    
    def __str__(self) -> str:
        return "gain 1 lore per damage"


@register_named_ability("REFRESHING BREAK")
def create_refreshing_break(character: Any, ability_data: dict):
    """REFRESHING BREAK - Whenever you ready this character, gain 1 lore for each 1 damage on him.
    
    Implementation: When this character readies, gain lore equal to damage on this character.
    """
    return quick_ability(
        "REFRESHING BREAK",
        character,
        when_character_readies(character),
        CONTROLLER,
        GainLorePerDamageEffect()
    )