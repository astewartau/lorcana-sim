"""Event system for triggered abilities and game state changes."""

from enum import Enum
from typing import Dict, Any, List, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..models.game.game_state import GameState
    from ..models.abilities.base_ability import BaseAbility
    from ..models.cards.character_card import CharacterCard
    from ..models.cards.action_card import ActionCard


class GameEvent(Enum):
    """Types of game events that can trigger abilities."""
    CHARACTER_QUESTS = "character_quests"
    CHARACTER_CHALLENGES = "character_challenges"
    CHARACTER_TAKES_DAMAGE = "character_takes_damage"
    CHARACTER_DEALS_DAMAGE = "character_deals_damage"
    CHARACTER_PLAYED = "character_played"
    CHARACTER_DESTROYED = "character_destroyed"
    SONG_PLAYED = "song_played"
    SONG_SUNG = "song_sung"
    TURN_BEGINS = "turn_begins"
    TURN_ENDS = "turn_ends"
    PHASE_CHANGES = "phase_changes"


@dataclass
class EventContext:
    """Context information for game events."""
    event_type: GameEvent
    source: Any = None  # The card/character that caused the event
    target: Any = None  # The target of the event (if any)
    player: Any = None  # The player who controls the source
    game_state: 'GameState' = None
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


class GameEventManager:
    """Manages game events and triggered abilities."""
    
    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state
        self._event_listeners: Dict[GameEvent, List['BaseAbility']] = {}
        
    def register_triggered_ability(self, ability: 'BaseAbility'):
        """Register an ability that listens for certain events."""
        trigger_events = ability.get_trigger_events()
        for event in trigger_events:
            if event not in self._event_listeners:
                self._event_listeners[event] = []
            self._event_listeners[event].append(ability)
    
    def unregister_triggered_ability(self, ability: 'BaseAbility'):
        """Unregister an ability (e.g., when character is destroyed)."""
        for event_list in self._event_listeners.values():
            if ability in event_list:
                event_list.remove(ability)
    
    def trigger_event(self, event_context: EventContext) -> List[str]:
        """Trigger an event and execute all listening abilities."""
        results = []
        
        # Get all abilities that listen for this event type
        listening_abilities = self._event_listeners.get(event_context.event_type, [])
        
        for ability in listening_abilities:
            # Check if this specific ability should trigger for this event
            if ability.should_trigger(event_context):
                try:
                    result = ability.execute_trigger(event_context)
                    if result:
                        results.append(result)
                except Exception as e:
                    results.append(f"Error executing {ability}: {str(e)}")
        
        return results
    
    def rebuild_listeners(self):
        """Rebuild the event listener registry from current game state."""
        self._event_listeners.clear()
        
        # Register all abilities from characters in play
        for player in self.game_state.players:
            for character in player.characters_in_play:
                for ability in character.abilities:
                    if hasattr(ability, 'get_trigger_events') and ability.get_trigger_events():
                        self.register_triggered_ability(ability)