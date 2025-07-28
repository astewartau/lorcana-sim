"""Turn History and Timing System for centralized tracking of turn progression."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from ..utils.logging_config import get_game_logger

logger = get_game_logger(__name__)


@dataclass
class TurnInfo:
    """Information about a single turn."""
    turn_number: int
    player: Any
    start_time: int
    phases: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    end_time: Optional[int] = None


@dataclass
class EffectDuration:
    """Information about an effect's duration and expiration."""
    effect: Any
    duration_type: str  # 'turns', 'phases', 'until_end_of_turn', 'until_condition'
    duration_value: Any  # int for turns/phases, callable for condition
    registered_turn: int
    registered_phase: Optional[str] = None
    condition: Optional[callable] = None  # For condition-based durations


class TurnTimingComponent:
    """Centralized tracking of turn progression and timing."""
    
    def __init__(self):
        self.turn_history: List[TurnInfo] = []
        self.current_turn_info: Optional[TurnInfo] = None
        self.duration_tracking: Dict[int, EffectDuration] = {}  # effect_id -> duration_info
        self.event_counter = 0  # For generating unique timestamps
    
    def start_turn(self, turn_number: int, player: Any) -> TurnInfo:
        """Record turn start and setup timing.
        
        Args:
            turn_number: The turn number
            player: The player whose turn it is
            
        Returns:
            TurnInfo object for the new turn
        """
        # End previous turn if it exists
        if self.current_turn_info:
            self.end_turn()
        
        turn_info = TurnInfo(
            turn_number=turn_number,
            player=player,
            start_time=self._get_game_time()
        )
        
        self.turn_history.append(turn_info)
        self.current_turn_info = turn_info
        
        logger.debug(f"Started turn {turn_number} for player {player}")
        return turn_info
    
    def end_turn(self) -> Optional[TurnInfo]:
        """End the current turn.
        
        Returns:
            The completed turn info, or None if no turn was active
        """
        if self.current_turn_info:
            self.current_turn_info.end_time = self._get_game_time()
            completed_turn = self.current_turn_info
            self.current_turn_info = None
            logger.debug(f"Ended turn {completed_turn.turn_number}")
            return completed_turn
        return None
    
    def start_phase(self, phase: str) -> None:
        """Record phase start timing.
        
        Args:
            phase: Phase name (e.g., 'ready', 'draw', 'play')
        """
        if self.current_turn_info:
            self.current_turn_info.phases[phase] = {
                'start_time': self._get_game_time(),
                'events': []
            }
            logger.debug(f"Started phase {phase} in turn {self.current_turn_info.turn_number}")
    
    def end_phase(self, phase: str) -> None:
        """Record phase end timing.
        
        Args:
            phase: Phase name
        """
        if self.current_turn_info and phase in self.current_turn_info.phases:
            self.current_turn_info.phases[phase]['end_time'] = self._get_game_time()
            logger.debug(f"Ended phase {phase} in turn {self.current_turn_info.turn_number}")
    
    def record_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Record an event that occurred during the current turn/phase.
        
        Args:
            event_type: Type of event
            event_data: Additional event data
        """
        event_record = {
            'type': event_type,
            'timestamp': self._get_game_time(),
            'data': event_data
        }
        
        # Add to current turn
        if self.current_turn_info:
            self.current_turn_info.events.append(event_record)
        
        # Add to current phase if available
        if self.current_turn_info:
            current_phase = self._get_current_phase()
            if current_phase and current_phase in self.current_turn_info.phases:
                self.current_turn_info.phases[current_phase]['events'].append(event_record)
    
    def register_temporary_effect(self, effect: Any, duration_type: str, duration_value: Any, 
                                 condition: Optional[callable] = None) -> int:
        """Register effects that expire after specific time periods.
        
        Args:
            effect: The effect object
            duration_type: Type of duration ('turns', 'phases', 'until_end_of_turn', 'until_condition')
            duration_value: Duration value (int for turns/phases, None for end_of_turn)
            condition: Optional condition function for 'until_condition' type
            
        Returns:
            Effect ID for tracking
        """
        effect_id = id(effect)
        current_turn = len(self.turn_history)
        current_phase = self._get_current_phase()
        
        duration_info = EffectDuration(
            effect=effect,
            duration_type=duration_type,
            duration_value=duration_value,
            registered_turn=current_turn,
            registered_phase=current_phase,
            condition=condition
        )
        
        self.duration_tracking[effect_id] = duration_info
        logger.debug(f"Registered temporary effect {effect} with duration {duration_type}:{duration_value}")
        return effect_id
    
    def unregister_temporary_effect(self, effect_id: int) -> bool:
        """Unregister a temporary effect.
        
        Args:
            effect_id: ID of the effect to unregister
            
        Returns:
            True if effect was found and removed, False otherwise
        """
        if effect_id in self.duration_tracking:
            effect_info = self.duration_tracking.pop(effect_id)
            logger.debug(f"Unregistered temporary effect {effect_info.effect}")
            return True
        return False
    
    def get_expired_effects(self, current_turn: Optional[int] = None, 
                           current_phase: Optional[str] = None,
                           game_state: Optional[Any] = None) -> List[Any]:
        """Get effects that should expire based on current timing.
        
        Args:
            current_turn: Current turn number (defaults to latest)
            current_phase: Current phase (defaults to current)
            game_state: Game state for condition evaluation
            
        Returns:
            List of effects that should expire
        """
        if current_turn is None:
            current_turn = len(self.turn_history)
        if current_phase is None:
            current_phase = self._get_current_phase()
        
        expired = []
        expired_ids = []
        
        for effect_id, info in self.duration_tracking.items():
            if self._should_expire(info, current_turn, current_phase, game_state):
                expired.append(info.effect)
                expired_ids.append(effect_id)
        
        # Remove expired effects from tracking
        for effect_id in expired_ids:
            del self.duration_tracking[effect_id]
            logger.debug(f"Effect {effect_id} expired and removed from tracking")
        
        return expired
    
    def check_and_queue_expired_effects(self, action_queue: Any, game_state: Any) -> int:
        """Check for expired effects and queue them for execution.
        
        Args:
            action_queue: Action queue to add expired effects to
            game_state: Current game state
            
        Returns:
            Number of effects queued for expiration
        """
        expired_effects = self.get_expired_effects(game_state=game_state)
        
        if expired_effects:
            from ..models.abilities.composable.effects import TemporaryEffectCleanup
            from ..engine.action_queue import ActionPriority
            
            # Queue cleanup effects
            for effect in expired_effects:
                cleanup_effect = TemporaryEffectCleanup(effect)
                action_queue.enqueue(
                    effect=cleanup_effect,
                    target=getattr(effect, 'target', None),
                    context={'game_state': game_state, 'reason': 'duration_expired'},
                    priority=ActionPriority.CLEANUP,
                    source_description=f"⏰ Effect expired: {effect}"
                )
            
            logger.debug(f"Queued {len(expired_effects)} expired effects for cleanup")
        
        return len(expired_effects)
    
    def register_effect_with_auto_cleanup(self, effect: Any, duration_type: str, 
                                         duration_value: Any, action_queue: Any,
                                         condition: Optional[callable] = None) -> int:
        """Register a temporary effect with automatic cleanup queuing.
        
        Args:
            effect: The effect to register
            duration_type: Type of duration
            duration_value: Duration value
            action_queue: Action queue for cleanup scheduling
            condition: Optional condition for expiration
            
        Returns:
            Effect ID for tracking
        """
        effect_id = self.register_temporary_effect(effect, duration_type, duration_value, condition)
        
        # Store action queue reference for later cleanup
        if not hasattr(self, '_action_queue_ref'):
            self._action_queue_ref = action_queue
        
        return effect_id
    
    def get_turn_count(self) -> int:
        """Get the total number of completed turns."""
        return len(self.turn_history)
    
    def get_current_turn_number(self) -> Optional[int]:
        """Get the current turn number."""
        return self.current_turn_info.turn_number if self.current_turn_info else None
    
    def get_turn_info(self, turn_number: int) -> Optional[TurnInfo]:
        """Get information about a specific turn.
        
        Args:
            turn_number: Turn number to retrieve
            
        Returns:
            TurnInfo if found, None otherwise
        """
        for turn_info in self.turn_history:
            if turn_info.turn_number == turn_number:
                return turn_info
        return None
    
    def get_recent_turns(self, count: int = 5) -> List[TurnInfo]:
        """Get the most recent turn information.
        
        Args:
            count: Number of recent turns to return
            
        Returns:
            List of recent TurnInfo objects
        """
        return self.turn_history[-count:] if count > 0 else []
    
    def clear_history(self) -> None:
        """Clear all turn history and timing data."""
        self.turn_history.clear()
        self.current_turn_info = None
        self.duration_tracking.clear()
        self.event_counter = 0
        logger.debug("Cleared all turn timing history")
    
    def _get_game_time(self) -> int:
        """Get current game time (event counter)."""
        self.event_counter += 1
        return self.event_counter
    
    def _get_current_phase(self) -> Optional[str]:
        """Get the current phase name."""
        if not self.current_turn_info:
            return None
        
        # Find the most recently started phase that hasn't ended
        latest_phase = None
        latest_time = -1
        
        for phase_name, phase_info in self.current_turn_info.phases.items():
            start_time = phase_info.get('start_time', 0)
            end_time = phase_info.get('end_time')
            
            # If phase hasn't ended and started more recently than our current candidate
            if end_time is None and start_time > latest_time:
                latest_phase = phase_name
                latest_time = start_time
        
        return latest_phase
    
    def _should_expire(self, effect_info: EffectDuration, current_turn: int, current_phase: str, 
                       game_state: Optional[Any] = None) -> bool:
        """Check if effect should expire.
        
        Args:
            effect_info: Effect duration information
            current_turn: Current turn number
            current_phase: Current phase
            game_state: Game state for condition evaluation
            
        Returns:
            True if effect should expire
        """
        if effect_info.duration_type == 'until_end_of_turn':
            # Expires when we move to a different turn
            return current_turn > effect_info.registered_turn
        
        elif effect_info.duration_type == 'turns':
            # Expires after specified number of turns
            return current_turn >= effect_info.registered_turn + effect_info.duration_value
        
        elif effect_info.duration_type == 'phases':
            # Expires after specified number of phases (more complex)
            # This would need to count phases across turns
            # For now, simplified implementation
            return current_turn > effect_info.registered_turn
        
        elif effect_info.duration_type == 'until_condition':
            # Expires when condition becomes true
            if effect_info.condition:
                try:
                    return effect_info.condition()
                except Exception as e:
                    logger.warning(f"Error evaluating condition for effect expiration: {e}")
                    return False
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get timing statistics for analysis.
        
        Returns:
            Dictionary with timing statistics
        """
        if not self.turn_history:
            return {'turns': 0, 'total_time': 0, 'avg_turn_time': 0}
        
        total_time = 0
        completed_turns = 0
        
        for turn_info in self.turn_history:
            if turn_info.end_time:
                turn_duration = turn_info.end_time - turn_info.start_time
                total_time += turn_duration
                completed_turns += 1
        
        avg_turn_time = total_time / completed_turns if completed_turns > 0 else 0
        
        return {
            'turns': len(self.turn_history),
            'completed_turns': completed_turns,
            'total_time': total_time,
            'avg_turn_time': avg_turn_time,
            'active_temporary_effects': len(self.duration_tracking),
            'current_turn': self.current_turn_info.turn_number if self.current_turn_info else None
        }