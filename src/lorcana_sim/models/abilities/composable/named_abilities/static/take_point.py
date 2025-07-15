"""TAKE POINT - While a damaged character is in play, this character gets +2 ¤."""

from typing import Any
from ..registry import register_named_ability


def _has_damaged_character_in_play(game_state) -> bool:
    """Check if any character is damaged."""
    if not game_state:
        return False
    
    # Check all characters from all players
    for player in game_state.players:
        if hasattr(player, 'characters_in_play'):
            for char in player.characters_in_play:
                if hasattr(char, 'damage') and char.damage > 0:
                    return True
    
    return False


class TakePointPassiveAbility:
    """Passive ability that continuously applies +2 strength while damaged characters exist."""
    
    def __init__(self, character):
        self.character = character
        self.name = "TAKE POINT"
        self.is_active = False
    
    def evaluate_condition(self, game_state):
        """Check if the condition is met and update strength accordingly."""
        condition_met = _has_damaged_character_in_play(game_state)
        
        if condition_met and not self.is_active:
            # Apply +2 strength bonus
            self.character.strength += 2
            self.is_active = True
            return f"TAKE POINT activated (+2 strength)"
            
        elif not condition_met and self.is_active:
            # Remove +2 strength bonus
            self.character.strength -= 2
            self.is_active = False
            return f"TAKE POINT deactivated (-2 strength)"
        
        # No change
        return None
    
    def register_with_event_manager(self, event_manager):
        """Register this passive ability to be evaluated on relevant events."""
        # Add this ability to a list of passive abilities that need evaluation
        if not hasattr(event_manager, 'passive_abilities'):
            event_manager.passive_abilities = []
        event_manager.passive_abilities.append(self)
    
    def unregister_from_event_manager(self, event_manager):
        """Unregister this passive ability from the event manager."""
        if hasattr(event_manager, 'passive_abilities') and self in event_manager.passive_abilities:
            event_manager.passive_abilities.remove(self)
    
    def get_relevant_events(self):
        """Return events this passive ability cares about."""
        # Passive abilities don't need specific events since they're evaluated after all events
        return []
    
    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"


@register_named_ability("TAKE POINT")
def create_take_point(character: Any, ability_data: dict):
    """TAKE POINT - While a damaged character is in play, this character gets +2 ¤.
    
    Implementation: True passive ability that continuously monitors board state.
    """
    return TakePointPassiveAbility(character)