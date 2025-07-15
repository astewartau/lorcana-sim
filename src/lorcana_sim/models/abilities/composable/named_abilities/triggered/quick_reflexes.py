"""QUICK REFLEXES - During your turn, this character gains Evasive. (They can challenge characters with Evasive.)"""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...target_selectors import SELF
from ...triggers import or_conditions, when_turn_starts, when_turn_ends


class QuickReflexesEffect:
    """Effect that grants Evasive during controller's turn."""
    
    def apply(self, target: Any, context: dict) -> Any:
        game_state = context.get('game_state')
        if (hasattr(target, 'controller') and 
            hasattr(game_state, 'current_player') and 
            target.controller == game_state.current_player):
            # Grant Evasive during controller's turn
            if hasattr(target, 'metadata'):
                target.metadata['has_evasive'] = True
            else:
                target.metadata = {'has_evasive': True}
        else:
            # Remove Evasive when not controller's turn
            if hasattr(target, 'metadata') and 'has_evasive' in target.metadata:
                del target.metadata['has_evasive']
        return target
    
    def __str__(self) -> str:
        return "gain Evasive during your turn"


@register_named_ability("QUICK REFLEXES")
def create_quick_reflexes(character: Any, ability_data: dict):
    """QUICK REFLEXES - During your turn, this character gains Evasive.
    
    Implementation: Triggers on every turn change to update Evasive status.
    """
    return quick_ability(
        "QUICK REFLEXES",
        character,
        or_conditions(
            when_turn_starts(),
            when_turn_ends()
        ),
        SELF,
        QuickReflexesEffect()
    )