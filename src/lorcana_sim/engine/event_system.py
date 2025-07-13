"""Event system for triggered abilities and game state changes."""

from enum import Enum
from typing import Dict, Any, List, TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..models.game.game_state import GameState
    from ..models.cards.character_card import CharacterCard
    from ..models.cards.action_card import ActionCard
    from .step_system import StepProgressionEngine, GameStep


class GameEvent(Enum):
    """Types of game events that can trigger abilities."""
    # Character events
    CHARACTER_QUESTS = "character_quests"
    CHARACTER_CHALLENGES = "character_challenges"
    CHARACTER_TAKES_DAMAGE = "character_takes_damage"
    CHARACTER_DEALS_DAMAGE = "character_deals_damage"
    CHARACTER_PLAYED = "character_played"
    CHARACTER_BANISHED = "character_banished"
    CHARACTER_ENTERS_PLAY = "character_enters_play"  # More general than played
    CHARACTER_LEAVES_PLAY = "character_leaves_play"  # More general than banished
    
    # Action/Song events
    ACTION_PLAYED = "action_played"  # Action card played for ink cost
    SONG_PLAYED = "song_played"      # Same as ACTION_PLAYED but for songs specifically
    SONG_SUNG = "song_sung"          # Song sung by Singer ability
    
    # Turn structure events
    TURN_BEGINS = "turn_begins"
    TURN_ENDS = "turn_ends"
    PHASE_BEGINS = "phase_begins"
    PHASE_ENDS = "phase_ends"
    READY_STEP = "ready_step"
    SET_STEP = "set_step"
    DRAW_STEP = "draw_step"
    MAIN_PHASE_BEGINS = "main_phase_begins"
    
    # Resource events
    CARD_DRAWN = "card_drawn"
    INK_PLAYED = "ink_played"
    LORE_GAINED = "lore_gained"
    
    # Item events
    ITEM_PLAYED = "item_played"
    
    # Game state events
    GAME_BEGINS = "game_begins"
    GAME_ENDS = "game_ends"


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
    """Manages game events and composable abilities."""
    
    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state
        self._composable_listeners: Dict[GameEvent, List[Any]] = {}  # For composable abilities
        self.step_engine: Optional['StepProgressionEngine'] = None
        self.event_interceptors: List[Callable[[EventContext], bool]] = []
        self._paused_events: List[EventContext] = []
    
    def register_composable_ability(self, ability: Any) -> None:
        """Register a composable ability with the event manager."""
        # Get events this ability should listen to based on its keyword
        relevant_events = self._get_relevant_events_for_ability(ability)
        
        for event in relevant_events:
            if event not in self._composable_listeners:
                self._composable_listeners[event] = []
            self._composable_listeners[event].append(ability)
    
    def _get_relevant_events_for_ability(self, ability) -> list:
        """Determine which events an ability should listen to based on its type."""
        # Check if the ability has specific event requirements
        if hasattr(ability, 'keyword'):
            keyword = ability.keyword
            if keyword == 'Rush':
                return []  # Rush doesn't need to listen to any events - it affects move validation
            elif keyword == 'Support':
                return [GameEvent.CHARACTER_QUESTS]
            elif keyword == 'Resist':
                return [GameEvent.CHARACTER_TAKES_DAMAGE]
            elif keyword == 'Singer':
                return [GameEvent.SONG_SUNG]
            elif keyword == 'Evasive':
                return []  # Evasive affects move validation, not events
            elif keyword == 'Bodyguard':
                return []  # Bodyguard affects move validation, not events
        
        # For composable abilities, check the name property
        if hasattr(ability, 'name'):
            name = ability.name.lower()
            if 'rush' in name:
                return [GameEvent.CHARACTER_ENTERS_PLAY]  # Rush triggers when character enters play
            elif 'support' in name:
                return [GameEvent.CHARACTER_QUESTS]  # Support triggers when character quests
            elif 'resist' in name:
                return [GameEvent.CHARACTER_TAKES_DAMAGE]  # Resist triggers on damage
            elif 'singer' in name:
                return [GameEvent.SONG_SUNG]  # Singer triggers on song events
            elif 'evasive' in name:
                return [GameEvent.CHARACTER_CHALLENGES]  # Evasive triggers on challenge attempts
            elif 'bodyguard' in name:
                return [GameEvent.CHARACTER_CHALLENGES]  # Bodyguard triggers on challenges (to redirect them)
            elif 'ward' in name:
                return [GameEvent.CHARACTER_TAKES_DAMAGE]  # Ward triggers on targeting attempts
        
        # Fallback - return empty list for unknown abilities to prevent spurious triggers
        return []
    
    def unregister_composable_ability(self, ability: Any) -> None:
        """Unregister a composable ability from the event manager."""
        for event_list in self._composable_listeners.values():
            if ability in event_list:
                event_list.remove(ability)

    def set_step_engine(self, step_engine: 'StepProgressionEngine') -> None:
        """Set the step progression engine for step-by-step execution."""
        self.step_engine = step_engine
    
    def add_event_interceptor(self, interceptor: Callable[[EventContext], bool]) -> None:
        """Add an event interceptor that can pause/modify event processing."""
        self.event_interceptors.append(interceptor)
    
    def remove_event_interceptor(self, interceptor: Callable[[EventContext], bool]) -> None:
        """Remove an event interceptor."""
        if interceptor in self.event_interceptors:
            self.event_interceptors.remove(interceptor)
    
    def trigger_event(self, event_context: EventContext) -> List[str]:
        """Trigger an event and execute all listening composable abilities."""
        # Check interceptors first - they can pause/modify event processing
        for interceptor in self.event_interceptors:
            try:
                should_continue = interceptor(event_context)
                if not should_continue:
                    # Event was intercepted and should be paused
                    self._paused_events.append(event_context)
                    return [f"Event {event_context.event_type.value} intercepted and paused"]
            except Exception as e:
                # Interceptor error - log but continue
                pass
        
        return self._execute_event(event_context)
    
    def _execute_event(self, event_context: EventContext) -> List[str]:
        """Execute an event (internal method)."""
        results = []
        
        # Trigger composable abilities
        composable_abilities = self._composable_listeners.get(event_context.event_type, [])
        
        for ability in composable_abilities:
            try:
                # If we have a step engine, we might need to create steps for abilities
                if self.step_engine and hasattr(ability, 'requires_steps') and ability.requires_steps():
                    steps = ability.create_execution_steps(event_context)
                    if steps:
                        self.step_engine.queue_steps(steps)
                        results.append(f"Queued steps for ability: {ability.name}")
                else:
                    # Execute immediately for simple abilities
                    ability.handle_event(event_context)
                    results.append(f"Triggered composable ability: {ability.name}")
            except Exception as e:
                results.append(f"Error executing composable ability {ability}: {str(e)}")
        
        return results
    
    def resume_paused_events(self) -> List[str]:
        """Resume processing of paused events."""
        results = []
        paused_events = self._paused_events.copy()
        self._paused_events.clear()
        
        for event_context in paused_events:
            event_results = self._execute_event(event_context)
            results.extend(event_results)
        
        return results
    
    def get_paused_events(self) -> List[EventContext]:
        """Get list of currently paused events."""
        return self._paused_events.copy()
    
    def clear_paused_events(self) -> None:
        """Clear all paused events."""
        self._paused_events.clear()
    
    def rebuild_listeners(self):
        """Rebuild the composable ability listener registry from current game state."""
        self._composable_listeners.clear()
        
        # Register all composable abilities from characters in play
        for player in self.game_state.players:
            for character in player.characters_in_play:
                character.register_composable_abilities(self)