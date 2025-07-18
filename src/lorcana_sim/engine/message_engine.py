"""MessageEngine for handling message flow and structured event data creation."""

from typing import Dict, Any, Optional, List
from collections import deque
from ..models.game.game_state import GameState
from .event_system import GameEvent
from .choice_system import GameChoiceManager
from .move_validator import MoveValidator
from .game_messages import (
    GameMessage, MessageType, ActionRequiredMessage, ChoiceRequiredMessage, 
    StepExecutedMessage, GameOverMessage, LegalAction
)
from .game_moves import GameMove, ChoiceMove


def create_event_data(event: GameEvent, **context) -> Dict[str, Any]:
    """Create standardized event_data structure."""
    return {
        'event': event,
        'context': context
    }


class MessageEngine:
    """Handles message flow and structured event data creation - NO string formatting"""
    
    def __init__(self, game_state: GameState, choice_manager: GameChoiceManager, validator: MoveValidator, execution_engine=None, shared_message_queue=None, shared_current_steps=None):
        self.game_state = game_state
        self.choice_manager = choice_manager
        self.validator = validator
        self.execution_engine = execution_engine  # Reference to ExecutionEngine for coordination
        
        # Message flow components - share with GameEngine during transition
        self.message_queue = shared_message_queue if shared_message_queue is not None else deque()
        self.current_steps = shared_current_steps if shared_current_steps is not None else deque()
        self.waiting_for_input = False
        
        # Choice handling (integrated with messages)
        self.current_choice = None
    
    def next_message(self, move: Optional[GameMove] = None, game_engine=None) -> GameMessage:
        """Get next message OR handle choice response"""
        # Process move if provided (delegate to game engine for now)
        if move and self.waiting_for_input:
            if game_engine:
                game_engine._process_move(move)
                game_engine._evaluate_conditional_effects_after_move(move)
            else:
                self._process_choice_response(move)
            self.waiting_for_input = False
        
        # Return queued messages first
        if self.message_queue:
            message = self.message_queue.popleft()
            # Apply deferred action if this message has one
            if hasattr(message, 'deferred_action') and message.deferred_action:
                # Apply the deferred effect now
                try:
                    result = message.deferred_action.effect.apply(message.deferred_action.target, message.deferred_action.context)
                except Exception as e:
                    print(f"DEBUG: Error applying deferred action: {e}")
            return message
        
        # Process pending actions from action queue (delegate to execution engine)
        if self.execution_engine and self.execution_engine.action_queue.has_pending_actions():
            if game_engine:
                message = game_engine._process_next_queued_action()
                if message:
                    return message
        
        # Execute next step if available (delegate to game engine for now)
        if self.current_steps:
            if game_engine:
                message = game_engine._execute_next_step()
                game_engine._evaluate_conditional_effects_after_step()
                return message
        
        # Check for choices
        if self.current_choice or self.is_waiting_for_choice():
            if not self.current_choice:
                self.current_choice = self._get_current_choice()
            
            if self.current_choice:
                self.waiting_for_input = True
                return ChoiceRequiredMessage(
                    type=MessageType.CHOICE_REQUIRED,
                    player=self.current_choice.player,
                    choice=self.current_choice,
                    ability_source=getattr(self.current_choice, 'source', None)
                )
        
        # Check game over
        if self.game_state.is_game_over():
            result, winner, game_over_data = self.game_state.get_game_result()
            # Build reason string from game_over_data for backward compatibility
            reason = ""
            if game_over_data:
                context = game_over_data.get('context', {})
                result_type = context.get('result')
                if result_type == 'lore_victory':
                    winner_name = context.get('winner_name', 'Unknown')
                    lore = context.get('lore', 0)
                    reason = f"{winner_name} wins with {lore} lore!"
                elif result_type == 'deck_exhaustion':
                    winner_name = context.get('winner_name', 'Unknown')
                    loser_name = context.get('loser_name', 'Unknown')
                    reason = f"{winner_name} wins - {loser_name} ran out of cards!"
                elif result_type == 'stalemate':
                    reason = "Game ended in stalemate - both players unable to make progress"
            
            return GameOverMessage(
                type=MessageType.GAME_OVER,
                player=self.game_state.current_player,
                winner=winner,
                reason=reason
            )
        
        # Need player action
        self.waiting_for_input = True
        return ActionRequiredMessage(
            type=MessageType.ACTION_REQUIRED,
            player=self.game_state.current_player,
            phase=self.game_state.current_phase,
            legal_actions=self._get_legal_actions()
        )
    
    def queue_event_message(self, event: GameEvent, context: Dict) -> None:
        """Queue a message with structured event data"""
        message = StepExecutedMessage(
            type=MessageType.STEP_EXECUTED,
            player=self.game_state.current_player,
            step=event,
            event_data=create_event_data(event, **context)
        )
        self.message_queue.append(message)
    
    def is_waiting_for_choice(self) -> bool:
        """Check if game is paused for player choice"""
        return self.choice_manager.has_pending_choices()
    
    def resolve_choice(self, choice_move: ChoiceMove) -> None:
        """Resolve a player choice from external input"""
        if self.current_choice:
            self.choice_manager.resolve_choice(choice_move.choice_id, choice_move.selected_option)
            self.current_choice = None
    
    def _process_choice_response(self, move: GameMove) -> None:
        """Process a choice response move"""
        if isinstance(move, ChoiceMove):
            self.resolve_choice(move)
    
    def _get_current_choice(self):
        """Get the current pending choice"""
        return self.choice_manager.get_current_choice()
    
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