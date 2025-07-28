"""Automatic Effect Registry System for event-driven game engine infrastructure."""

from typing import List, Dict, Any, Callable, Optional, Tuple
from ..utils.logging_config import get_game_logger

logger = get_game_logger(__name__)


class AutomaticEffectRegistry:
    """Registry for effects that should trigger automatically at specific times."""
    
    def __init__(self):
        self.start_of_turn_effects: List[Tuple[Any, Optional[Callable]]] = []
        self.end_of_turn_effects: List[Tuple[Any, Optional[Callable]]] = []
        self.phase_start_effects: Dict[str, List[Tuple[Any, Optional[Callable]]]] = {}
        self.phase_end_effects: Dict[str, List[Tuple[Any, Optional[Callable]]]] = {}
        self.conditional_triggers: List[Tuple[List[str], Any, Callable]] = []
    
    def register_start_of_turn(self, effect: Any, condition: Optional[Callable] = None):
        """Register effect to trigger at start of any turn.
        
        Args:
            effect: The effect to execute
            condition: Optional condition function that must return True for effect to trigger
        """
        self.start_of_turn_effects.append((effect, condition))
        logger.debug(f"Registered start-of-turn effect: {effect}")
    
    def register_end_of_turn(self, effect: Any, condition: Optional[Callable] = None):
        """Register effect to trigger at end of any turn.
        
        Args:
            effect: The effect to execute
            condition: Optional condition function that must return True for effect to trigger
        """
        self.end_of_turn_effects.append((effect, condition))
        logger.debug(f"Registered end-of-turn effect: {effect}")
    
    def register_phase_start(self, phase: str, effect: Any, condition: Optional[Callable] = None):
        """Register effect to trigger at start of specific phase.
        
        Args:
            phase: Phase name (e.g., 'ready', 'draw', 'play')
            effect: The effect to execute
            condition: Optional condition function that must return True for effect to trigger
        """
        if phase not in self.phase_start_effects:
            self.phase_start_effects[phase] = []
        self.phase_start_effects[phase].append((effect, condition))
        logger.debug(f"Registered phase-start effect for {phase}: {effect}")
    
    def register_phase_end(self, phase: str, effect: Any, condition: Optional[Callable] = None):
        """Register effect to trigger at end of specific phase.
        
        Args:
            phase: Phase name (e.g., 'ready', 'draw', 'play')
            effect: The effect to execute
            condition: Optional condition function that must return True for effect to trigger
        """
        if phase not in self.phase_end_effects:
            self.phase_end_effects[phase] = []
        self.phase_end_effects[phase].append((effect, condition))
        logger.debug(f"Registered phase-end effect for {phase}: {effect}")
    
    def register_conditional_trigger(self, trigger_events: List[str], effect: Any, condition: Callable):
        """Register effect to trigger on specific events when condition is met.
        
        Args:
            trigger_events: List of event names that should trigger evaluation
            effect: The effect to execute when condition is met
            condition: Condition function that determines if effect should execute
        """
        self.conditional_triggers.append((trigger_events, effect, condition))
        logger.debug(f"Registered conditional trigger for events {trigger_events}: {effect}")
    
    def get_automatic_effects(self, trigger_type: str, context: Dict[str, Any]) -> List[Any]:
        """Get all automatic effects that should trigger for a specific trigger type.
        
        Args:
            trigger_type: Type of trigger ('start_of_turn', 'end_of_turn', 'phase_start_X', 'phase_end_X')
            context: Context information including game_state, player, phase, etc.
            
        Returns:
            List of effects that should be queued
        """
        effects_to_queue = []
        
        if trigger_type == 'start_of_turn':
            for effect, condition in self.start_of_turn_effects:
                if not condition or condition(context):
                    effects_to_queue.append(effect)
                    logger.debug(f"Queuing start-of-turn effect: {effect}")
        
        elif trigger_type == 'end_of_turn':
            for effect, condition in self.end_of_turn_effects:
                if not condition or condition(context):
                    effects_to_queue.append(effect)
                    logger.debug(f"Queuing end-of-turn effect: {effect}")
        
        elif trigger_type.startswith('phase_start_'):
            phase = trigger_type.replace('phase_start_', '')
            for effect, condition in self.phase_start_effects.get(phase, []):
                if not condition or condition(context):
                    effects_to_queue.append(effect)
                    logger.debug(f"Queuing phase-start effect for {phase}: {effect}")
        
        elif trigger_type.startswith('phase_end_'):
            phase = trigger_type.replace('phase_end_', '')
            for effect, condition in self.phase_end_effects.get(phase, []):
                if not condition or condition(context):
                    effects_to_queue.append(effect)
                    logger.debug(f"Queuing phase-end effect for {phase}: {effect}")
        
        return effects_to_queue
    
    def get_conditional_effects(self, event_name: str, context: Dict[str, Any]) -> List[Any]:
        """Get conditional effects that should trigger for a specific event.
        
        Args:
            event_name: Name of the event that occurred
            context: Context information for condition evaluation
            
        Returns:
            List of effects that should be queued
        """
        effects_to_queue = []
        
        for trigger_events, effect, condition in self.conditional_triggers:
            if event_name in trigger_events:
                try:
                    if condition(context):
                        effects_to_queue.append(effect)
                        logger.debug(f"Queuing conditional effect for event {event_name}: {effect}")
                except Exception as e:
                    logger.warning(f"Error evaluating condition for conditional effect: {e}")
        
        return effects_to_queue
    
    def clear_all(self):
        """Clear all registered effects."""
        self.start_of_turn_effects.clear()
        self.end_of_turn_effects.clear()
        self.phase_start_effects.clear()
        self.phase_end_effects.clear()
        self.conditional_triggers.clear()
        logger.debug("Cleared all automatic effect registrations")
    
    def get_registration_count(self) -> Dict[str, int]:
        """Get count of registered effects for debugging."""
        return {
            'start_of_turn': len(self.start_of_turn_effects),
            'end_of_turn': len(self.end_of_turn_effects),
            'phase_start': sum(len(effects) for effects in self.phase_start_effects.values()),
            'phase_end': sum(len(effects) for effects in self.phase_end_effects.values()),
            'conditional': len(self.conditional_triggers)
        }