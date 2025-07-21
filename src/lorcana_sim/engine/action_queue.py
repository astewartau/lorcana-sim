"""Action queue system for executing effects and emitting events atomically."""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import uuid

from ..models.abilities.composable.effects import Effect
from .event_system import GameEvent, EventContext, GameEventManager
from ..utils.logging_config import get_game_logger

logger = get_game_logger(__name__)

class ActionPriority(Enum):
    """Priority levels for action execution."""
    IMMEDIATE = 0  # Must execute before anything else (e.g., replacement effects)
    HIGH = 1       # High priority actions
    NORMAL = 2     # Standard actions
    LOW = 3        # Low priority actions
    CLEANUP = 4    # Cleanup actions that happen after everything else


@dataclass
class QueuedAction:
    """Represents a single action in the queue."""
    action_id: str
    effect: Effect
    target: Any
    context: Dict[str, Any]
    priority: ActionPriority = ActionPriority.NORMAL
    source_description: str = ""  # Human-readable source of this action
    waiting_for_choice: Optional[str] = None  # Choice ID this action is waiting for
    
    def __post_init__(self):
        if not self.action_id:
            self.action_id = str(uuid.uuid4())


@dataclass
class ActionResult:
    """Result of executing an action."""
    action_id: str
    success: bool
    result: Any
    events_emitted: List[Dict[str, Any]]
    error: Optional[str] = None
    queued_action: Optional[QueuedAction] = None  # Store the action for deferred execution


class ActionQueue:
    """Manages the queue of pending actions and their execution."""
    
    def __init__(self, event_manager: GameEventManager):
        self.event_manager = event_manager
        self._queue: deque[QueuedAction] = deque()
        self._paused = False
        self._execution_history: List[ActionResult] = []
        self._current_action: Optional[QueuedAction] = None
        self._waiting_actions: Dict[str, QueuedAction] = {}  # Actions waiting for choice resolution
        
    def enqueue(self, effect: Effect, target: Any, context: Dict[str, Any], 
                priority: ActionPriority = ActionPriority.NORMAL,
                source_description: str = "") -> str:
        """
        Add an action to the queue.
        
        Returns:
            The action ID for tracking
        """
        action = QueuedAction(
            action_id=str(uuid.uuid4()),
            effect=effect,
            target=target,
            context=context,
            priority=priority,
            source_description=source_description
        )
        
        from ..models.abilities.composable.effects import AbilityTriggerEffect
        
        # Insert based on priority
        if priority == ActionPriority.IMMEDIATE:
            self._queue.appendleft(action)
        elif priority == ActionPriority.CLEANUP:
            self._queue.append(action)
        else:
            # For HIGH, NORMAL, LOW - insert in order
            inserted = False
            for i, existing in enumerate(self._queue):
                if existing.priority.value > priority.value:
                    # Insert before first lower priority item
                    # Convert deque to list, insert, convert back
                    queue_list = list(self._queue)
                    queue_list.insert(i, action)
                    self._queue = deque(queue_list)
                    inserted = True
                    break
            
            if not inserted:
                self._queue.append(action)
        
        return action.action_id
    
    def enqueue_multiple(self, actions: List[tuple]) -> List[str]:
        """
        Enqueue multiple actions at once.
        
        Args:
            actions: List of (effect, target, context, priority, source_description) tuples
            
        Returns:
            List of action IDs
        """
        action_ids = []
        for action_data in actions:
            effect, target, context = action_data[:3]
            priority = action_data[3] if len(action_data) > 3 else ActionPriority.NORMAL
            source_desc = action_data[4] if len(action_data) > 4 else ""
            
            action_id = self.enqueue(effect, target, context, priority, source_desc)
            action_ids.append(action_id)
        
        return action_ids
    
    def has_pending_actions(self) -> bool:
        """Check if there are actions waiting to be executed."""
        return len(self._queue) > 0
    
    def peek_next_action(self) -> Optional[QueuedAction]:
        """Look at the next action without removing it from the queue."""
        return self._queue[0] if self._queue else None
    
    def process_next_action(self, apply_effect: bool = True) -> Optional[ActionResult]:
        """
        Process the next action in the queue.
        
        Args:
            apply_effect: If True, apply the effect immediately. If False, just prepare it.
        
        Returns:
            ActionResult if an action was processed, None if queue is empty
        """
        if self._paused or not self._queue:
            return None
        
        action = self._queue.popleft()
        self._current_action = action
        
        # Check if this is a composite effect that needs splitting
        if not apply_effect and self._is_composite_effect(action.effect):
            return self._process_composite_effect(action)
        
        # Only execute the effect if requested
        result = None
        if apply_effect:
            result = action.effect.apply(action.target, action.context)
            
            # Check if this is a TargetedEffect that returned unchanged target (choice pending)
            from ..models.abilities.composable.effects import TargetedEffect
            if isinstance(action.effect, TargetedEffect) and result == action.target:
                # Choice might be pending - check if choice manager has pending choices
                choice_manager = action.context.get('choice_manager')
                if choice_manager and choice_manager.is_game_paused():
                    # Put the action back at the front of the queue for later processing
                    self._queue.appendleft(action)
                    self._current_action = None
                    # Pause the queue
                    self._paused = True
                    # Return None to indicate processing was paused
                    return None
        
        # Get events that this effect declares (preview mode if not applied)
        events = []
        if hasattr(action.effect, 'get_events'):
            # For preview, pass the target as the result since effect wasn't applied
            preview_result = result if apply_effect else action.target
            events = action.effect.get_events(action.target, action.context, preview_result)
        
        # Only emit events if the effect was actually applied
        emitted_events = []
        if apply_effect:
            for event_data in events:
                # Create EventContext from event data
                event_type = event_data.get('type')
                if isinstance(event_type, str):
                    # Convert string to GameEvent enum if needed
                    event_type = GameEvent(event_type)
            
                event_context = EventContext(
                    event_type=event_type,
                    source=event_data.get('source', action.target),
                    target=event_data.get('target'),
                    player=event_data.get('player'),
                    game_state=action.context.get('game_state'),
                    additional_data=event_data.get('additional_data', {})
                )
                
                # Trigger the event
                self.event_manager.trigger_event(event_context)
                emitted_events.append(event_data)
            
            # Also collect events in game_state.choice_events for choice-triggered effects
            game_state = action.context.get('game_state')
            if game_state and hasattr(game_state, 'choice_events'):
                game_state.choice_events.extend(events)
        else:
            # For deferred effects, store the events to be processed later
            game_state = action.context.get('game_state')
            if game_state and hasattr(game_state, 'choice_events'):
                game_state.choice_events.extend(events)
        
        # Create result
        action_result = ActionResult(
            action_id=action.action_id,
            success=True,
            result=result,
            events_emitted=emitted_events,
            queued_action=action  # Always store action for message creation
        )
        
        self._execution_history.append(action_result)
        self._current_action = None
            
        return action_result
    
    def process_all_actions(self) -> List[ActionResult]:
        """
        Process all pending actions in order.
        
        Returns:
            List of all action results
        """
        results = []
        while self.has_pending_actions() and not self._paused:
            result = self.process_next_action()
            if result:
                results.append(result)
        
        return results
    
    def pause(self):
        """Pause action processing."""
        self._paused = True
    
    def resume(self):
        """Resume action processing."""
        self._paused = False
    
    def resume_after_choice(self):
        """Resume action processing after a choice has been resolved."""
        self._paused = False
        # The paused action should be at the front of the queue and can now be processed
    
    def is_paused(self) -> bool:
        """Check if the queue is paused."""
        return self._paused
    
    def clear(self):
        """Clear all pending actions."""
        self._queue.clear()
        self._current_action = None
    
    def get_pending_count(self) -> int:
        """Get the number of pending actions."""
        return len(self._queue)
    
    def get_pending_actions(self) -> List[QueuedAction]:
        """Get a copy of all pending actions."""
        return list(self._queue)
    
    def _is_composite_effect(self, effect) -> bool:
        """Check if an effect is a composite effect."""
        from ..models.abilities.composable.effects import CompositeEffect
        
        # Check if it's directly a composite effect
        if isinstance(effect, CompositeEffect):
            return True
        
        # No wrapper effects anymore
            
        return False
    
    def _process_composite_effect(self, composite_action: QueuedAction) -> Optional[ActionResult]:
        """Process a composite effect by splitting it into individual actions."""
        from ..models.abilities.composable.effects import CompositeEffect
        
        # Extract the actual composite effect
        composite_effect = composite_action.effect
        if isinstance(composite_effect, CompositeEffect):
            actual_composite = composite_effect
        else:
            return None
        
        # Split the composite effect into individual actions
        
        # Split the composite effect into individual actions
        sub_actions = []
        for sub_effect in actual_composite.effects:
            sub_action = QueuedAction(
                action_id=f"{composite_action.action_id}_sub_{len(sub_actions)}",
                effect=sub_effect,
                target=composite_action.target,
                context=composite_action.context.copy(),
                priority=composite_action.priority,
                source_description=f"{composite_action.source_description} (sub-effect)"
            )
            sub_actions.append(sub_action)
            # Create sub-action for this effect
        
        # Insert sub-actions at the front of the queue (in reverse order so they execute in correct order)
        for sub_action in reversed(sub_actions):
            self._queue.appendleft(sub_action)
        
        # Process the first sub-action immediately
        if sub_actions:
            return self.process_next_action(apply_effect=False)
        
        return None
    
    def get_execution_history(self, limit: int = 10) -> List[ActionResult]:
        """Get recent execution history."""
        return self._execution_history[-limit:]
    
    def remove_action(self, action_id: str) -> bool:
        """
        Remove a specific action from the queue.
        
        Returns:
            True if action was found and removed
        """
        for i, action in enumerate(self._queue):
            if action.action_id == action_id:
                del self._queue[i]
                return True
        return False
    
    def create_message_for_action(self, action: QueuedAction, result: ActionResult) -> Dict[str, Any]:
        """
        Create a standardized message for an executed action.
        
        This can be used by the game engine to create GameMessage objects.
        """
        return {
            'action_id': action.action_id,
            'effect_type': type(action.effect).__name__,
            'effect_description': str(action.effect),
            'target': getattr(action.target, 'name', str(action.target)),
            'source': action.source_description,
            'success': result.success,
            'error': result.error,
            'events_emitted': result.events_emitted
        }
    
    def enqueue_waiting_for_choice(self, effect: Effect, choice_id: str, target: Any, 
                                   context: Dict[str, Any], priority: ActionPriority = ActionPriority.NORMAL,
                                   source_description: str = "") -> str:
        """
        Queue an effect that waits for a specific choice to be resolved.
        
        Args:
            effect: The effect to queue
            choice_id: The choice ID this effect is waiting for
            target: The target for the effect
            context: The context for the effect
            priority: The priority level for the effect
            source_description: Human-readable source description
            
        Returns:
            The action ID for tracking
        """
        action = QueuedAction(
            action_id=str(uuid.uuid4()),
            effect=effect,
            target=target,
            context=context,
            priority=priority,
            source_description=source_description,
            waiting_for_choice=choice_id
        )
        
        self._waiting_actions[choice_id] = action
        logger.debug("ActionQueue.enqueue_waiting_for_choice - stored action {action.action_id} for choice {choice_id}")
        
        return action.action_id
    
    def resolve_choice_and_continue(self, choice_id: str, selected_targets: List[Any]) -> Optional[str]:
        """
        Find waiting action and provide it with resolved targets, then queue it for execution.
        
        Args:
            choice_id: The choice ID that was resolved
            selected_targets: The targets selected by the choice resolution
            
        Returns:
            The action ID if an action was resumed, None otherwise
        """
        if choice_id in self._waiting_actions:
            action = self._waiting_actions.pop(choice_id)
            logger.debug("ActionQueue.resolve_choice_and_continue - found waiting action {action.action_id}")
            
            # Add the resolved targets to the context
            action.context['resolved_targets'] = selected_targets
            action.waiting_for_choice = None  # Clear the waiting state
            
            # Queue the action for immediate execution
            self._queue.appendleft(action)  # Use appendleft for immediate priority
            logger.debug("ActionQueue.resolve_choice_and_continue - queued action {action.action_id} for execution")
            
            return action.action_id
        else:
            logger.debug("ActionQueue.resolve_choice_and_continue - no waiting action found for choice {choice_id}")
            return None
    
    def get_waiting_actions_count(self) -> int:
        """Get the number of actions waiting for choice resolution."""
        return len(self._waiting_actions)
    
    def get_waiting_action_for_choice(self, choice_id: str) -> Optional[QueuedAction]:
        """Get the action waiting for a specific choice."""
        return self._waiting_actions.get(choice_id)