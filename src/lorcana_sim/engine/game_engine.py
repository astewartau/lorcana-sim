"""Game engine for executing actions and managing state transitions."""

from typing import Dict, Any, Tuple, Optional, List, Union
from collections import deque
from enum import Enum

# NOTE: ExecutionMode stub for compatibility after step system removal
class ExecutionMode(Enum):
    MANUAL = "manual"
    PAUSE_ON_INPUT = "pause_on_input"
from ..models.game.game_state import GameState, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card
from .move_validator import MoveValidator
from .event_system import GameEventManager, GameEvent, EventContext
from .damage_calculator import DamageCalculator, DamageType
from .action_result import ActionResult, ActionResultType
from .choice_system import GameChoiceManager, ChoiceContext
# NOTE: StepProgressionEngine and related classes removed in Phase 4
from .input_system import InputManager, PlayerInput, AbilityInputBuilder
from .state_serializer import SnapshotManager
from .game_messages import (
    GameMessage, MessageType, ActionRequiredMessage, ChoiceRequiredMessage, 
    StepExecutedMessage, GameOverMessage, LegalAction
)
from .game_moves import GameMove, ChoiceMove, InkMove, PlayMove, QuestMove, ChallengeMove, SingMove, PassMove
from .action_queue import ActionQueue, ActionPriority, QueuedAction
from .action_executor import ActionExecutor
from .execution_engine import ExecutionEngine
from .message_engine import MessageEngine
from .choice_engine import ChoiceEngine
from ..models.abilities.composable.conditional_effects import ActivationZone
from .game_event_types import GameEventType


def create_event_data(event: GameEvent, **context) -> Dict[str, Any]:
    """Create standardized event_data structure."""
    return {
        'event': event,
        'context': context
    }


class GameEngine:
    """Executes game actions and manages state transitions with step-by-step support."""
    
    def __init__(self, game_state: GameState, execution_mode: ExecutionMode):
        self.game_state = game_state
        
        # Core managers (unchanged)
        self.validator = MoveValidator(game_state)
        self.event_manager = GameEventManager(game_state)
        self.damage_calculator = DamageCalculator(game_state)
        self.choice_manager = GameChoiceManager()
        
        # Link managers to game state for ability access
        game_state.event_manager = self.event_manager
        game_state.choice_manager = self.choice_manager
        
        # Message stream components - legacy for compatibility during transition
        self.waiting_for_input = False
        self.current_choice = None
        
        # Three specialized engines
        self.execution_engine = ExecutionEngine(
            game_state, self.validator, self.event_manager, 
            self.damage_calculator, self.choice_manager, execution_mode
        )
        self.message_engine = MessageEngine(
            game_state, self.choice_manager, self.validator, self.execution_engine
        )
        self.choice_engine = ChoiceEngine(game_state, self.choice_manager, self.execution_engine)
        
        # Give event_manager access to action_queue for universal action_queue fix
        self.event_manager.execution_engine = self.execution_engine
        
        # Legacy components for compatibility
        self.input_manager = InputManager()
        self.snapshot_manager = SnapshotManager()
        
        # Set up integration
        self._setup_input_handlers()
        
        # Register all abilities from all cards in all zones at game initialization
        self.event_manager.register_all_abilities()
    
    def start_game(self):
        """Start the game by triggering the initial TURN_BEGINS event."""
        current_player = self.game_state.current_player
        turn_begin_context = EventContext(
            event_type=GameEvent.TURN_BEGINS,
            player=current_player,
            game_state=self.game_state,
            additional_data={'turn_number': self.game_state.turn_number}
        )
        self.event_manager.trigger_event(turn_begin_context)
    
    def get_last_event(self) -> Optional[Dict[str, Any]]:
        """Get the last event that occurred for inspection."""
        return self.game_state.get_last_event()
    
    def clear_last_event(self) -> None:
        """Clear the last event."""
        self.game_state.clear_last_event()
    
    def trigger_event_with_choices(self, event_context: EventContext) -> List[str]:
        """Trigger an event with choice manager included in the context."""
        # Add choice manager to the event context's additional data
        if not event_context.additional_data:
            event_context.additional_data = {}
        event_context.additional_data['choice_manager'] = self.choice_manager
        
        return self.event_manager.trigger_event(event_context)
    
    def draw_card_with_events(self, player):
        """Draw a card for a player and trigger CARD_DRAWN event."""
        card = player.draw_card()
        if card:
            # Set the last event with structured data
            source = "normal_draw"
            if self.game_state.current_phase.value == "draw":
                source = "draw_phase"
            
            self.game_state.set_last_event(
                'CARD_DRAWN',
                player=player.name,
                cards_drawn=[card],
                count=1,
                source=source,
                hand_size_after=len(player.hand),
                deck_size_after=len(player.deck)
            )
            
            # Handle zone transition: card moved from deck to hand
            zone_events = self.game_state.notify_card_zone_change(card, 'deck', 'hand')
            
            # Store zone events for later processing if any
            if zone_events and not hasattr(self, '_pending_zone_events'):
                self._pending_zone_events = []
            if zone_events:
                self._pending_zone_events.extend(zone_events)
            
            # Trigger CARD_DRAWN event
            draw_context = EventContext(
                event_type=GameEvent.CARD_DRAWN,
                source=card,
                player=player,
                game_state=self.game_state,
                action_queue=self.execution_engine.action_queue
            )
            self.event_manager.trigger_event(draw_context)
        return card
    
    def _execute_set_step(self) -> None:
        """Execute the set step (resolve start-of-turn effects)."""
        # Handle any start-of-turn triggered abilities
        self.game_state.set_step()
    
    def _execute_draw_step(self) -> None:
        """Execute the draw step (draw card with events)."""
        current_player = self.game_state.current_player
        
        # Draw card (skip on first turn for first player)
        should_draw = not (self.game_state.turn_number == 1 and 
                          self.game_state.current_player_index == 0 and 
                          not self.game_state.first_turn_draw_skipped)
        
        if should_draw:
            self.draw_card_with_events(current_player)
        elif self.game_state.turn_number == 1 and self.game_state.current_player_index == 0:
            self.game_state.first_turn_draw_skipped = True
        
        # Don't call draw_step() - we already drew the card with events above
    
    def execute_action(self, action, parameters: Dict[str, Any]) -> ActionResult:
        """Execute a game action directly - delegates to ExecutionEngine."""
        return self.execution_engine.execute_action(action, parameters)
    
    # Delegate action execution methods to maintain compatibility with any direct calls
    # =============================================================================
    # PLAYER CHOICE SYSTEM METHODS
    # =============================================================================
    
    def is_paused_for_choice(self) -> bool:
        """Check if the game is paused waiting for a player choice."""
        return self.choice_manager.is_game_paused()
    
    def get_current_choice(self) -> Optional[ChoiceContext]:
        """Get the current choice that needs player input."""
        return self.choice_manager.get_current_choice()
    
    def provide_player_choice(self, choice_id: str, selected_option: str) -> bool:
        """
        Provide a player's choice and continue game execution.
        
        Args:
        choice_id: ID of the choice being answered
            selected_option: ID of the selected option
            
        Returns:
        True if choice was valid and executed, False otherwise
        """
        return self.choice_manager.provide_choice(choice_id, selected_option)
    
    def get_choice_summary(self) -> Dict[str, Any]:
        """Get a summary of the current choice state for debugging/UI."""
        current_choice = self.get_current_choice()
        return {
            'is_paused': self.is_paused_for_choice(),
            'pending_choices': len(self.choice_manager.pending_choices),
            'current_choice': {
                'id': current_choice.choice_id if current_choice else None,
                'player': current_choice.player.name if current_choice and current_choice.player else None,
                'ability': current_choice.ability_name if current_choice else None,
                'prompt': current_choice.prompt if current_choice else None,
                'options': [opt.id for opt in current_choice.options] if current_choice else []
            } if current_choice else None
        }

    # =============================================================================
    # STEP-BY-STEP SYSTEM METHODS
    # =============================================================================
    
    
    def next_message(self, move: Optional[GameMove] = None) -> GameMessage:
        """Get the next message in the game progression - delegated to MessageEngine."""
        # Sync state with message engine
        self.message_engine.waiting_for_input = self.waiting_for_input
        self.message_engine.current_choice = self.current_choice
        
        # Delegate to MessageEngine
        result = self.message_engine.next_message(move, game_engine=self)
        
        # Sync state back
        self.waiting_for_input = self.message_engine.waiting_for_input
        self.current_choice = self.message_engine.current_choice
        
        return result
    
    
    def advance_step(self):
        """DEPRECATED: Step system removed in Phase 4."""
        raise NotImplementedError("Step system removed in Phase 4")
    
    def provide_input_for_current_step(self, input_data: Any):
        """DEPRECATED: Step system removed in Phase 4."""
        raise NotImplementedError("Step system removed in Phase 4")
    
    def get_current_step(self):
        """DEPRECATED: Step system removed in Phase 4."""
        raise NotImplementedError("Step system removed in Phase 4")
    
    def get_step_queue_status(self) -> Dict[str, Any]:
        """DEPRECATED: Step system removed in Phase 4."""
        raise NotImplementedError("Step system removed in Phase 4")
    
    def pause_execution(self) -> None:
        """DEPRECATED: Step system removed in Phase 4."""
        raise NotImplementedError("Step system removed in Phase 4")
    
    def resume_execution(self) -> None:
        """DEPRECATED: Step system removed in Phase 4."""
        raise NotImplementedError("Step system removed in Phase 4")
    
    def clear_step_queue(self) -> None:
        """DEPRECATED: Step system removed in Phase 4."""
        raise NotImplementedError("Step system removed in Phase 4")
    
    def set_execution_mode(self, mode) -> None:
        """DEPRECATED: Step system removed in Phase 4."""
        raise NotImplementedError("Step system removed in Phase 4")
    
    def register_player_input_provider(self, player_id: str, provider) -> None:
        """Register an input provider for a player."""
        self.input_manager.register_input_provider(player_id, provider)
    
    def force_evaluate_conditional_effects(self) -> None:
        """Force evaluation of all conditional effects - delegates to ExecutionEngine."""
        events = self.execution_engine.force_evaluate_conditional_effects()
        # Note: Events will be handled by on-demand message generation in new architecture
    
    def trigger_event_with_choices_and_queue(self, event_context: EventContext) -> List[str]:
        """Trigger an event with choice manager and action queue included in the context."""
        # Add choice manager and action queue to the event context's additional data
        if not event_context.additional_data:
            event_context.additional_data = {}
        event_context.additional_data['choice_manager'] = self.choice_manager
        event_context.additional_data['action_queue'] = self.execution_engine.action_queue
        
        return self.event_manager.trigger_event(event_context)
    
    # =============================================================================
    # STEP-BY-STEP INTERNAL METHODS
    # =============================================================================
    
    
    
    def _process_move(self, move: GameMove) -> None:
        """Process a player move - DEPRECATED: Will be removed in Phase 4."""
        # NOTE: This method is deprecated and will be removed
        # Direct move processing now happens in MessageEngine._process_move()
        pass
    
    def _execute_next_step(self) -> StepExecutedMessage:
        """Execute the next step and return message."""
        if not self.current_steps:
            # No steps to execute
            return StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step="no_steps"
            )
        
        # Get the next step
        step = self.current_steps.popleft()
        
        # Execute the step
        try:
            result = step.execute_fn()
            
            # Create a message based on the result
            if hasattr(result, 'success') and result.success:
                self._queue_result_message(result)
                return StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=step.step_id
                )
            else:
                return StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=f"{step.step_id}_error"
                )
        except Exception as e:
            return StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step=f"{step.step_id}_error"
            )
    
    def _process_next_queued_action(self) -> Optional[GameMessage]:
        """Process the next action from the action queue and return a message."""
            
        result = self.execution_engine.action_queue.process_next_action()
        if not result:
            return None
        
        return self._create_action_message(result)
    
    def _create_action_message(self, result) -> Optional[GameMessage]:
        """Create a message from an action result."""
        if not result:
            return None
        
        # Get the action that was just executed from the result
        executed_action = result.queued_action  # This contains the action info
        
        # Create a message based on the action result
        if result.success:
            # Store structured effect data for UI to format
            effect_data = self._extract_effect_data(executed_action, result)
            description = "Action completed"  # Fallback text
            
            message = StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step=f"action_{result.action_id}",
                deferred_action=result.queued_action  # Store the action for later execution
            )
            # Add structured effect data for UI formatting
            message.effect_data = effect_data
            return message
        else:
            # Error occurred
            return StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step=f"action_{result.action_id}_error",
            )
    
    def _extract_effect_data(self, executed_action, result) -> dict:
        """Extract structured data about an executed effect for UI formatting."""
        if not executed_action:
            return {"type": "unknown"}
        
        from ..models.abilities.composable.effects import (
            DiscardCard, GainLoreEffect, DrawCards, BanishCharacter, 
            ReturnToHand, ExertCharacter, ReadyCharacter, RemoveDamageEffect,
            AbilityTriggerEffect
        )
        
        effect = executed_action.effect
        target = executed_action.target
        
        # Handle ability trigger announcements
        if isinstance(effect, AbilityTriggerEffect):
            return {
                "type": "ability_trigger",
                "ability_name": effect.ability_name,
                "source_card_name": getattr(effect.source_card, 'name', 'Unknown'),
                "effect_preview": str(effect.actual_effect),
                "target": target
            }
        
        # Extract structured data based on effect type
        if isinstance(effect, DiscardCard):
            # For discard effects, get the card name and player name
            card_name = getattr(target, 'name', str(target))
            
            # Get player name from the controller or game context
            if hasattr(target, 'controller') and target.controller:
                player_name = getattr(target.controller, 'name', 'Unknown Player')
            else:
                # Fallback: look in execution context for player info
                context_player = executed_action.context.get('player')
                if context_player and hasattr(context_player, 'name'):
                    player_name = context_player.name
                else:
                    player_name = 'Unknown Player'
            
            return {
                "type": "discard_card",
                "card_name": card_name,
                "player_name": player_name,
                "target": target
            }
        
        elif isinstance(effect, GainLoreEffect):
            return {
                    "type": "gain_lore",
                    "amount": effect.amount,
                    "target": target
                }
        
        elif isinstance(effect, DrawCards):
            return {
                    "type": "draw_cards",
                    "count": effect.count,
                    "target": target
                }
        
        elif isinstance(effect, BanishCharacter):
            return {
                    "type": "banish_character",
                    "character_name": getattr(target, 'name', str(target)),
                    "target": target
                }
        
        elif isinstance(effect, ReturnToHand):
            return {
                    "type": "return_to_hand",
                    "card_name": getattr(target, 'name', str(target)),
                    "target": target
                }
        
        elif isinstance(effect, ExertCharacter):
            return {
                    "type": "exert_character",
                    "character_name": getattr(target, 'name', str(target)),
                    "target": target
                }
        
        elif isinstance(effect, ReadyCharacter):
            return {
                    "type": "ready_character",
                    "character_name": getattr(target, 'name', str(target)),
                    "target": target
                }
        
        elif isinstance(effect, RemoveDamageEffect):
            return {
                    "type": "remove_damage",
                    "amount": effect.amount,
                    "character_name": getattr(target, 'name', str(target)),
                    "target": target
                }
        
        else:
            # Generic effect data
            return {
                "type": "generic",
                "effect_class": type(effect).__name__,
                "effect_str": str(effect),
                "target_name": getattr(target, 'name', str(target)),
                "target": target,
                "source_description": executed_action.source_description
            }
    
    
    def _resolve_choice(self, choice_id: str, option: str) -> None:
        """Resolve a player choice."""
            
        # Capture the last event timestamp before choice resolution
        last_event_before = getattr(self.game_state, 'last_event', None)
        timestamp_before = last_event_before.get('timestamp', -1) if last_event_before else -1
        
        # Set up event collection for composite effects
        if not hasattr(self.game_state, 'choice_events'):
            self.game_state.choice_events = []
        
        # Clear any previous choice events
        self.game_state.choice_events.clear()
        
        # Override the choice execution to ensure game state has choice_events
        original_provide_choice = self.choice_manager.provide_choice
        def wrapped_provide_choice(choice_id, selected_option):
            # Ensure choice_events is available during effect execution
            if not hasattr(self.game_state, 'choice_events'):
                self.game_state.choice_events = []
            
            # Also ensure the context in the current choice includes the correct game state and action queue
            if self.choice_manager.current_choice:
                context = self.choice_manager.current_choice.trigger_context.get('_choice_execution_context', {})
                context['game_state'] = self.game_state
                context['action_queue'] = self.execution_engine.action_queue  # Add action queue for deferred execution
                self.choice_manager.current_choice.trigger_context['_choice_execution_context'] = context
                
            return original_provide_choice(choice_id, selected_option)
        
        # Temporarily replace the method
        self.choice_manager.provide_choice = wrapped_provide_choice
        
        try:
            success = self.provide_player_choice(choice_id, option)
        finally:
            # Restore original method
            self.choice_manager.provide_choice = original_provide_choice
            
        if not success:
            raise ValueError(f"Failed to resolve choice {choice_id} with option {option}")
        
        # After choice resolution, actions queued in ActionQueue will be processed
        # by subsequent next_message() calls following the "ONE EFFECT PER CALL" principle
    
    def _process_turn_end_effects(self) -> None:
        """Process effect expiration at end of turn."""
            
        # Get the player whose turn just ended (before the turn switch)
        # Note: The turn has already switched, so we need the previous player
        old_player_index = (self.game_state.current_player_index - 1) % len(self.game_state.players)
        ending_player = self.game_state.players[old_player_index]
        
        # Clear temporary bonuses from all characters belonging to the ending player
        for character in ending_player.characters_in_play:
            expired_effects = character.clear_temporary_bonuses(self.game_state)
            
            # Note: Expired effects will be handled by the new on-demand message generation
    
    
    def _get_legal_actions(self) -> List[LegalAction]:
        """Get legal actions formatted for messages."""
            
        legal_actions = []
        raw_actions = self.validator.get_all_legal_actions()
        
        for action, params in raw_actions:
            legal_action = LegalAction(
                action=action,
                target=params.get('card') or params.get('character') or params.get('attacker'),
                parameters=params
            )
            legal_actions.append(legal_action)
        
        return legal_actions
    
    # NOTE: _setup_step_listeners removed - step system deprecated
    
    def _setup_input_handlers(self) -> None:
        """Set up input handlers - reduced functionality after step system removal."""
        # NOTE: Input handlers simplified after step system removal
        pass
    
    def _evaluate_conditional_effects_before_step(self) -> None:
        """Evaluate conditional effects before a step is executed - delegates to ExecutionEngine."""
        events = self.execution_engine._evaluate_conditional_effects_before_step()
        # Note: Events will be handled by on-demand message generation in new architecture
    
    def _evaluate_conditional_effects_on_turn_change(self) -> None:
        """Evaluate conditional effects when turn changes - delegates to ExecutionEngine."""
        events = self.execution_engine._evaluate_conditional_effects_on_turn_change()
        # Note: Events will be handled by on-demand message generation in new architecture
    
    def _evaluate_conditional_effects_on_phase_change(self) -> None:
        """Evaluate conditional effects when phase changes - delegates to ExecutionEngine."""
        events = self.execution_engine._evaluate_conditional_effects_on_phase_change()
        # Note: Events will be handled by on-demand message generation in new architecture
    
