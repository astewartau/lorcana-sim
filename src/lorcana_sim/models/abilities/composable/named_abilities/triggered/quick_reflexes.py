"""QUICK REFLEXES - During your turn, this character gains Evasive. (They can challenge characters with Evasive.)"""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...target_selectors import SELF
from ...triggers import when_turn_begins, when_turn_ends, or_conditions


@register_named_ability("QUICK REFLEXES")
def create_quick_reflexes(character: Any, ability_data: dict):
    """QUICK REFLEXES - During your turn, this character gains Evasive.
    
    Implementation: Uses turn-based triggers to grant/remove Evasive.
    """
    
    class QuickReflexesEffect:
        """Effect that grants Evasive during controller's turn."""
        
        def apply(self, target: Any, context: dict) -> Any:
            game_state = context.get('game_state')
            if not game_state or not hasattr(target, 'controller'):
                return target
            
            # Check if it's the controller's turn
            if hasattr(game_state, 'current_player') and game_state.current_player == target.controller:
                # Grant Evasive
                if not hasattr(target, 'metadata'):
                    target.metadata = {}
                target.metadata['has_evasive'] = True
            else:
                # Remove Evasive if not controller's turn
                if hasattr(target, 'metadata') and 'has_evasive' in target.metadata:
                    target.metadata.pop('has_evasive', None)
            
            return target
        
        def get_events(self, target: Any, context: dict, result: Any) -> list:
            return []
        
        def __str__(self) -> str:
            return "gain Evasive during your turn"
    
    return quick_ability(
        "QUICK REFLEXES",
        character,
        or_conditions(
            when_turn_begins(character.controller),
            when_turn_ends(character.controller)
        ),
        SELF,
        QuickReflexesEffect()
    )