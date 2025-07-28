"""TAKE POINT - While a damaged character is in play, this character gets +2 ¤."""

from typing import Any, Dict
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import StatefulConditionalEffect, ModifyStat, NoEffect
from ...target_selectors import SELF
from ...triggers import when_any_takes_damage, when_banished, when_enters_play, or_conditions


def _has_damaged_character_in_play(target: Any, context: Dict[str, Any]) -> bool:
    """Check if any character is damaged."""
    game_state = context.get('game_state')
    if not game_state:
        return False
    
    # Check all characters from all players
    for player in game_state.players:
        if hasattr(player, 'characters_in_play'):
            for char in player.characters_in_play:
                if hasattr(char, 'damage') and char.damage > 0:
                    return True
    
    return False


@register_named_ability("TAKE POINT")
def create_take_point(character: Any, ability_data: dict):
    """TAKE POINT - While a damaged character is in play, this character gets +2 ¤.
    
    Implementation: Stateful conditional effect that grants +2 strength while any character is damaged.
    """
    
    # Create conditional effect that modifies strength
    conditional_effect = StatefulConditionalEffect(
        condition=_has_damaged_character_in_play,
        true_effect=ModifyStat('strength', 2),  # Grant +2 strength when condition met
        false_effect=ModifyStat('strength', -2), # Remove +2 strength when condition not met  
        state_key=f'take_point_{id(character)}'
    )
    
    # Evaluate the condition when:
    # 1. Any character takes damage (damage state changes)
    # 2. Any character is banished (might have been damaged)
    # 3. When this character enters play (initial evaluation)
    evaluation_trigger = or_conditions(
        when_any_takes_damage(),        # Any character taking damage
        when_banished(None),            # Any character leaving play
        when_enters_play(character)     # This character entering play
    )
    
    return quick_ability(
        "TAKE POINT",
        character,
        evaluation_trigger,
        SELF,  # Apply to this character only
        conditional_effect
    )