"""TURNING TIDES - When you play this character, you may move up to 2 damage counters from chosen character to chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import Effect
from ...target_selectors import CharacterSelector
from ...triggers import when_enters_play


class TurningTidesEffect(Effect):
    """Effect that handles the two-choice sequence for TURNING TIDES."""
    
    def apply(self, target: Any, context: dict) -> Any:
        game_state = context.get('game_state')
        action_queue = context.get('action_queue')
        
        if not game_state or not action_queue:
            return target
        
        # Create a complex effect that will queue two sequential choices:
        # 1. Choose source character (any character with damage)
        # 2. Choose target opposing character
        
        # For simplicity, we'll implement a basic version that just affects the first available characters
        # In a full implementation, this would need a more sophisticated multi-choice system
        
        # Find a character with damage to move from
        source_chars = []
        for player in game_state.players:
            for char in player.characters_in_play:
                if hasattr(char, 'damage') and char.damage > 0:
                    source_chars.append(char)
        
        # Find opposing characters to move damage to
        ability_owner = context.get('ability_owner')
        if not ability_owner:
            return target
            
        target_chars = []
        for player in game_state.players:
            if player != ability_owner.controller:
                target_chars.extend(player.characters_in_play)
        
        # Simple implementation: move damage from first available source to first available target
        if source_chars and target_chars:
            source_char = source_chars[0]
            target_char = target_chars[0]
            
            # Move up to 2 damage
            damage_to_move = min(2, source_char.damage)
            if damage_to_move > 0:
                source_char.damage = max(0, source_char.damage - damage_to_move)
                target_char.damage += damage_to_move
        
        return target
    
    def __str__(self) -> str:
        return "move up to 2 damage between characters"


@register_named_ability("TURNING TIDES")
def create_turning_tides(character: Any, ability_data: dict):
    """TURNING TIDES - When you play this character, you may move up to 2 damage counters from chosen character to chosen opposing character.
    
    Implementation: Uses new architectural pattern with custom multi-choice effect.
    Note: This is a simplified implementation. A full implementation would need sequential choice handling.
    """
    return (ComposableAbility("TURNING TIDES", character)
            .choice_effect(
                trigger_condition=when_enters_play(character),
                target_selector=CharacterSelector(lambda c, ctx: False),  # No direct target needed
                effect=TurningTidesEffect(),
                name="TURNING TIDES"
            ))