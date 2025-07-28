"""QUICK REFLEXES - During your turn, this character gains Evasive. (They can challenge characters with Evasive.)"""

from typing import Any, Dict
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...target_selectors import SELF
from ...triggers import when_turn_begins, when_turn_ends, when_enters_play, or_conditions
from ...effects import StatefulConditionalEffect, GrantProperty, RemoveProperty


@register_named_ability("QUICK REFLEXES")
def create_quick_reflexes(character: Any, ability_data: dict):
    """QUICK REFLEXES - During your turn, this character gains Evasive."""
    
    def is_controllers_turn(target: Any, context: Dict[str, Any]) -> bool:
        """Check if it's the controller's turn."""
        game_state = context.get('game_state')
        if not game_state or not hasattr(target, 'controller'):
            return False
        return game_state.current_player == target.controller
    
    # Multiple evaluation points
    evaluation_trigger = or_conditions(
        when_turn_begins(),           # Re-evaluate on any turn start
        when_turn_ends(),             # Re-evaluate on any turn end
        when_enters_play(character)   # Evaluate immediately when played
    )
    
    # Conditional effect that grants/removes Evasive
    quick_reflexes_effect = StatefulConditionalEffect(
        condition=is_controllers_turn,
        true_effect=GrantProperty('has_evasive', True),
        false_effect=RemoveProperty('has_evasive'),
        state_key=f'quick_reflexes_{id(character)}'
    )
    
    return quick_ability(
        "QUICK REFLEXES",
        character,
        evaluation_trigger,
        SELF,
        quick_reflexes_effect
    )