"""TURNING TIDES - When you play this character, you may move up to 2 damage counters from chosen character to chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...target_selectors import FRIENDLY_CHARACTER, ENEMY_CHARACTER
from ...triggers import when_enters_play


class MoveDamageEffect:
    """Effect that moves damage from one character to another."""
    
    def __init__(self, max_damage: int = 2):
        self.max_damage = max_damage
    
    def apply(self, target: Any, context: dict) -> Any:
        # This would need more complex targeting system to choose source and target
        # For now, just implement a simplified version
        source_char = context.get('source_character')
        target_char = target
        
        if (source_char and target_char and 
            hasattr(source_char, 'damage') and hasattr(target_char, 'damage')):
            
            # Move up to max_damage from source to target
            damage_to_move = min(self.max_damage, source_char.damage)
            source_char.damage = max(0, source_char.damage - damage_to_move)
            target_char.damage += damage_to_move
        
        return target
    
    def __str__(self) -> str:
        return f"move up to {self.max_damage} damage"


@register_named_ability("TURNING TIDES")
def create_turning_tides(character: Any, ability_data: dict):
    """TURNING TIDES - When you play this character, you may move up to 2 damage counters from chosen character to chosen opposing character.
    
    Implementation: When this character enters play, move up to 2 damage between characters.
    """
    return quick_ability(
        "TURNING TIDES",
        character,
        when_enters_play(character),
        ENEMY_CHARACTER,  # Target to receive damage
        MoveDamageEffect(2)
    )