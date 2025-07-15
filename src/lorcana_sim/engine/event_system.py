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
    CARD_DISCARDED = "card_discarded"
    INK_PLAYED = "ink_played"
    LORE_GAINED = "lore_gained"
    
    # Item events
    ITEM_PLAYED = "item_played"
    
    # Game state events
    GAME_BEGINS = "game_begins"
    GAME_ENDS = "game_ends"
    
    # Named ability specific events
    CHARACTER_BANISHED_IN_CHALLENGE = "character_banished_in_challenge"
    CHALLENGE_DECLARED = "challenge_declared"
    CHALLENGE_RESOLVED = "challenge_resolved"
    CARD_RETURNED_TO_HAND = "card_returned_to_hand"
    CHARACTER_READIED = "character_readied"
    CHARACTER_EXERTS = "character_exerts"
    CHARACTER_MOVES_TO_LOCATION = "character_moves_to_location"
    ABILITY_ACTIVATED = "ability_activated"
    ABILITY_TRIGGERED = "ability_triggered"
    DECK_MANIPULATED = "deck_manipulated"
    CARD_REVEALED = "card_revealed"
    EFFECT_APPLIED = "effect_applied"
    EFFECT_EXPIRED = "effect_expired"
    
    # New effect-specific events
    STAT_MODIFIED = "stat_modified"
    CHARACTER_EXERTED = "character_exerted"
    EFFECT_PREVENTED = "effect_prevented"
    DAMAGE_MODIFIED = "damage_modified"
    TARGET_CHANGED = "target_changed"
    PROPERTY_GRANTED = "property_granted"
    SHIFT_ACTIVATED = "shift_activated"
    CHALLENGER_ACTIVATED = "challenger_activated"
    CHARACTER_VANISHED = "character_vanished"
    RECKLESS_ACTIVATED = "reckless_activated"
    SING_TOGETHER_ACTIVATED = "sing_together_activated"
    BODYGUARD_ACTIVATED = "bodyguard_activated"
    SUPPORT_ACTIVATED = "support_activated"
    COST_MODIFIED = "cost_modified"
    PLAYED_FROM_DISCARD = "played_from_discard"
    LIBRARY_SEARCHED = "library_searched"
    SINGING_PREVENTED = "singing_prevented"
    SINGING_COST_MODIFIED = "singing_cost_modified"
    DAMAGE_REMOVED = "damage_removed"
    DECK_LOOKED_AT = "deck_looked_at"


@dataclass
class EventContext:
    """Context information for game events."""
    event_type: GameEvent
    source: Any = None  # The card/character that caused the event
    target: Any = None  # The target of the event (if any)
    player: Any = None  # The player who controls the source
    game_state: 'GameState' = None
    additional_data: Dict[str, Any] = None
    
    # Enhanced context for named abilities
    banishment_cause: Optional[str] = None  # "challenge", "ability", etc.
    turn_phase: Optional[str] = None
    ability_source: Optional[Any] = None  # Which ability caused this event
    damage_amount: Optional[int] = None  # For damage-related events
    cards_revealed: Optional[List[Any]] = None  # For deck manipulation events
    
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
        # For composable abilities, get events from the ability's listeners
        if hasattr(ability, 'listeners'):
            # Get all events that any listener in this ability cares about
            relevant_events = set()
            for listener in ability.listeners:
                if hasattr(listener, 'relevant_events'):
                    listener_events = listener.relevant_events()
                    relevant_events.update(listener_events)
                
            # If no relevant events found, the ability doesn't need event registration
            if not relevant_events:
                print(f"DEBUG: No relevant events for ability {ability.name}, listeners: {len(ability.listeners)}")
                return
            
            print(f"DEBUG: Registering ability {ability.name} for events: {relevant_events}")
        else:
            # For non-composable abilities, they must implement get_relevant_events() method
            if hasattr(ability, 'get_relevant_events'):
                relevant_events = set(ability.get_relevant_events())
            else:
                raise ValueError(f"Ability '{getattr(ability, 'name', ability)}' must implement get_relevant_events() method")
        
        for event in relevant_events:
            if event not in self._composable_listeners:
                self._composable_listeners[event] = []
            self._composable_listeners[event].append(ability)
    
    
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
                    # Execute immediately for simple abilities - only log if something actually triggered
                    triggered = False
                    for listener in ability.listeners:
                        if listener.should_trigger(event_context):
                            triggered = True
                            break
                    
                    if triggered:
                        ability.handle_event(event_context)
                        # Get effect details for more informative output
                        effect_details = []
                        for listener in ability.listeners:
                            if listener.should_trigger(event_context):
                                effect_details.append(str(listener.effect))
                        
                        if effect_details:
                            results.append(f"Triggered {ability.name}: {', '.join(effect_details)}")
                        else:
                            results.append(f"Triggered composable ability: {ability.name}")
            except Exception as e:
                results.append(f"Error executing composable ability {ability}: {str(e)}")
        
        # Evaluate passive abilities after event processing
        passive_results = self._evaluate_passive_abilities()
        results.extend(passive_results)
        
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
    
    def _evaluate_passive_abilities(self) -> List[str]:
        """Evaluate all passive abilities and return any state changes."""
        results = []
        
        # Check if we have any passive abilities registered
        if not hasattr(self, 'passive_abilities'):
            return results
        
        for passive_ability in self.passive_abilities:
            try:
                change_message = passive_ability.evaluate_condition(self.game_state)
                if change_message:
                    results.append(change_message)
            except Exception as e:
                results.append(f"Error evaluating passive ability {passive_ability}: {str(e)}")
        
        return results
    
    def rebuild_listeners(self):
        """Rebuild the composable ability listener registry from current game state."""
        self._composable_listeners.clear()
        
        # Register all composable abilities from characters in play
        for player in self.game_state.players:
            for character in player.characters_in_play:
                character.register_composable_abilities(self)