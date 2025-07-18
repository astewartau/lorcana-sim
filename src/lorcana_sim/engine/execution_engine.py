"""Execution engine for handling all internal game logic execution."""

from typing import Dict, Any, List, Optional, Deque
from collections import deque
from ..models.game.game_state import GameState, GameAction
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from .move_validator import MoveValidator
from .event_system import GameEventManager, GameEvent
from .damage_calculator import DamageCalculator
from .choice_system import GameChoiceManager
from .action_result import ActionResult
from .step_system import StepProgressionEngine, GameStep, ExecutionMode
from .action_queue import ActionQueue
from .action_executor import ActionExecutor
from .game_moves import GameMove, ActionMove, InkMove, PlayMove, QuestMove, ChallengeMove, SingMove
from .game_messages import StepExecutedMessage, MessageType
from ..models.abilities.composable.conditional_effects import ActivationZone


class ExecutionEngine:
    """Handles all internal game logic execution.
    
    Combines action execution, step progression, and conditional effects.
    """
    
    def __init__(self, game_state, validator, event_manager, damage_calculator, choice_manager, execution_mode, message_queue: Deque):
        self.game_state = game_state
        self.validator = validator
        self.event_manager = event_manager
        self.damage_calculator = damage_calculator
        self.choice_manager = choice_manager
        self.message_queue = message_queue
        
        # Execution components
        self.action_executor = ActionExecutor(
            game_state, validator, event_manager, damage_calculator, choice_manager
        )
        self.step_engine = StepProgressionEngine(execution_mode)
        self.action_queue = ActionQueue(event_manager)
        self.current_action_steps = []
        
        # Conditional effect evaluation
        self._condition_evaluator = None
    
    def execute_action(self, action: GameAction, parameters: Dict) -> ActionResult:
        """Execute action directly and return result."""
        result = self._execute_action_direct(action, parameters)
        
        # If this was a PROGRESS action with draw events, queue draw messages
        if (action == GameAction.PROGRESS and result.success and 
            hasattr(result, 'data') and result.data and 'draw_events' in result.data):
            self._queue_draw_event_messages(result.data['draw_events'])
        
        return result
    
    def process_move_as_steps(self, move: GameMove) -> List[GameStep]:
        """Convert a move into executable steps."""
        if isinstance(move, ActionMove):
            return self._create_action_steps(move.action, move.parameters)
        elif isinstance(move, (InkMove, PlayMove, QuestMove, ChallengeMove, SingMove)):
            action_move = self._convert_to_action_move(move)
            return self._create_action_steps(action_move.action, action_move.parameters)
        return []
    
    def execute_next_step(self) -> StepExecutedMessage:
        """Execute the next queued step."""
        return self._execute_next_step()
    
    def evaluate_conditional_effects(self, trigger_context) -> List[Dict]:
        """Evaluate and trigger conditional effects."""
        from ..models.abilities.composable.condition_evaluator import EvaluationTrigger
        
        if self._condition_evaluator is None:
            return []
            
        return self._condition_evaluator.evaluate_all_conditions(
            self.game_state, 
            trigger_context
        )
    
    def can_execute_action(self, action: GameAction, parameters: Dict) -> bool:
        """Check if action can be executed."""
        is_valid, _ = self.validator.validate_action(action, parameters)
        return is_valid
    
    def force_evaluate_conditional_effects(self) -> None:
        """Force evaluation of all conditional effects."""
        from ..models.abilities.composable.condition_evaluator import EvaluationTrigger
        
        if self._condition_evaluator is None:
            return
        
        # Evaluate effects for current game state
        events = self._condition_evaluator.evaluate_all_conditions(
            self.game_state, 
            EvaluationTrigger.FORCED_EVALUATION
        )
        return events
    
    # Private methods moved from GameEngine
    
    def _execute_action_direct(self, action, parameters: Dict[str, Any]) -> ActionResult:
        """Execute a game action directly (internal use only)."""
        # Convert string actions to GameAction enum if needed
        if isinstance(action, str):
            try:
                action = GameAction(action)
            except ValueError:
                return ActionResult.failure_result(action, f"Unknown action: {action}")
        
        # Check if game is over
        if self.game_state.is_game_over():
            result, winner, reason = self.game_state.get_game_result()
            return ActionResult.failure_result(action, f"Game is over: {reason}")
        
        # Validate action first
        is_valid, message = self.validator.validate_action(action, parameters)
        if not is_valid:
            return ActionResult.failure_result(action, message)
        
        # Execute the action using the ActionExecutor
        try:
            # Adjust parameters for ActionExecutor format
            if action == GameAction.SING_SONG:
                # ActionExecutor expects 'character' and 'song' keys
                adjusted_params = {
                    'character': parameters.get('singer'),
                    'song': parameters.get('song')
                }
                return self.action_executor.execute_action(action, adjusted_params)
            else:
                return self.action_executor.execute_action(action, parameters)
        
        except Exception as e:
            return ActionResult.failure_result(action, f"Error executing action: {str(e)}")
    
    def _convert_to_action_move(self, move: GameMove) -> ActionMove:
        """Convert specific move types to generic action moves."""
        if isinstance(move, InkMove):
            return ActionMove(GameAction.PLAY_INK, {'card': move.card})
        elif isinstance(move, PlayMove):
            if isinstance(move.card, CharacterCard):
                return ActionMove(GameAction.PLAY_CHARACTER, {'card': move.card})
            elif isinstance(move.card, ActionCard):
                return ActionMove(GameAction.PLAY_ACTION, {'card': move.card})
            elif isinstance(move.card, ItemCard):
                return ActionMove(GameAction.PLAY_ITEM, {'card': move.card})
        elif isinstance(move, QuestMove):
            return ActionMove(GameAction.QUEST_CHARACTER, {'character': move.character})
        elif isinstance(move, ChallengeMove):
            return ActionMove(GameAction.CHALLENGE_CHARACTER, {'attacker': move.attacker, 'defender': move.defender})
        elif isinstance(move, SingMove):
            return ActionMove(GameAction.SING_SONG, {'singer': move.singer, 'song': move.song})
        
        raise ValueError(f"Cannot convert move type: {type(move)}")
    
    def _create_action_steps(self, action: GameAction, parameters: Dict[str, Any]) -> List[GameStep]:
        """Create steps for a game action."""
        # For now, disable step creation to use clean direct execution
        # This ensures all actions use the new clean messaging format
        return []
    
    def _execute_next_step(self) -> StepExecutedMessage:
        """Execute the next step and return message."""
        # This method would need to be implemented based on the step execution logic
        # For now, return a placeholder
        return StepExecutedMessage(
            type=MessageType.STEP_EXECUTED,
            player=self.game_state.current_player,
            step="placeholder"
        )
    
    def _evaluate_conditional_effects_after_move(self, move: GameMove) -> None:
        """Evaluate conditional effects after a move is processed."""
        from ..models.abilities.composable.condition_evaluator import EvaluationTrigger
        
        if self._condition_evaluator is None:
            return
        
        # Determine trigger type based on move
        trigger = EvaluationTrigger.STEP_EXECUTED
        if isinstance(move, PlayMove):
            trigger = EvaluationTrigger.CARD_PLAYED
        elif isinstance(move, (ActionMove,)):
            # Check if this caused a phase or turn change
            trigger = EvaluationTrigger.PHASE_CHANGE
        
        # Evaluate and return events (don't queue them here)
        return self._condition_evaluator.evaluate_all_conditions(self.game_state, trigger)
    
    def _evaluate_conditional_effects_after_step(self) -> List[Dict]:
        """Evaluate conditional effects after a step is executed."""
        from ..models.abilities.composable.condition_evaluator import EvaluationTrigger
        
        if self._condition_evaluator is None:
            return []
        
        return self._condition_evaluator.evaluate_all_conditions(
            self.game_state, 
            EvaluationTrigger.STEP_EXECUTED
        )
    
    def _evaluate_conditional_effects_on_turn_change(self) -> List[Dict]:
        """Evaluate conditional effects when turn changes."""
        from ..models.abilities.composable.condition_evaluator import EvaluationTrigger
        
        if self._condition_evaluator is None:
            return []
        
        return self._condition_evaluator.evaluate_all_conditions(
            self.game_state, 
            EvaluationTrigger.TURN_CHANGE
        )
    
    def _evaluate_conditional_effects_on_phase_change(self) -> List[Dict]:
        """Evaluate conditional effects when phase changes."""
        from ..models.abilities.composable.condition_evaluator import EvaluationTrigger
        
        if self._condition_evaluator is None:
            return []
        
        return self._condition_evaluator.evaluate_all_conditions(
            self.game_state, 
            EvaluationTrigger.PHASE_CHANGE
        )
    
    def _queue_draw_event_messages(self, draw_events: List[Dict]) -> None:
        """Queue draw event messages for UI display."""
        for event in draw_events:
            if event.get('type') == 'card_drawn':
                cards_drawn = event.get('cards_drawn', [])
                player_name = event.get('player', 'Unknown')
                
                # Get player object - use current player if name matches, otherwise look up
                player = None
                if player_name == self.game_state.current_player.name:
                    player = self.game_state.current_player
                elif player_name == self.game_state.players[0].name:
                    player = self.game_state.players[0]
                elif player_name == self.game_state.players[1].name:
                    player = self.game_state.players[1]
                
                for card in cards_drawn:
                    draw_message = StepExecutedMessage(
                        type=MessageType.STEP_EXECUTED,
                        player=self.game_state.current_player,
                        step=GameEvent.CARD_DRAWN,
                        event_data={
                            'event': GameEvent.CARD_DRAWN,
                            'context': {
                                'player': player,
                                'card': card
                            }
                        }
                    )
                    self.message_queue.append(draw_message)
    
    @property
    def condition_evaluator(self):
        """Lazy initialization of condition evaluator."""
        if self._condition_evaluator is None:
            try:
                from ..models.abilities.composable.condition_evaluator import ConditionEvaluator
                self._condition_evaluator = ConditionEvaluator()
            except ImportError:
                # Handle case where condition evaluator is not available
                pass
        return self._condition_evaluator