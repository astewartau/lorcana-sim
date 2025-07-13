"""High-level game loop with step-by-step progression for interactive gameplay."""

from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

from ..models.game.game_state import GameState, GameAction, Phase
from .stepped_game_engine import SteppedGameEngine
from .step_system import ExecutionMode, StepType, StepStatus
from .input_system import PlayerInput, AbilityInputBuilder


class GameLoopState(Enum):
    """Current state of the game loop."""
    WAITING_FOR_PLAYER_ACTION = "waiting_for_player_action"
    WAITING_FOR_ABILITY_INPUT = "waiting_for_ability_input"
    EXECUTING_ACTION = "executing_action"
    GAME_OVER = "game_over"


@dataclass
class GameChoice:
    """Represents a choice the player needs to make."""
    choice_type: str
    prompt: str
    options: List[Any]
    metadata: Dict[str, Any]


@dataclass
class GameTurnInfo:
    """Information about the current game turn."""
    current_player_name: str
    current_player_index: int
    turn_number: int
    current_phase: str
    available_actions: List[Tuple[GameAction, Dict[str, Any]]]
    game_state_summary: Dict[str, Any]


class InteractiveGameLoop:
    """High-level game loop for interactive step-by-step gameplay."""
    
    def __init__(self, game_state: GameState, execution_mode: ExecutionMode = ExecutionMode.PAUSE_ON_INPUT):
        self.engine = SteppedGameEngine(game_state, execution_mode)
        self.game_state = game_state
        self.state = GameLoopState.WAITING_FOR_PLAYER_ACTION
        self.current_choice: Optional[GameChoice] = None
        
    def get_current_turn_info(self) -> GameTurnInfo:
        """Get information about the current turn and available actions."""
        legal_actions = self.engine.validator.get_all_legal_actions()
        
        return GameTurnInfo(
            current_player_name=self.game_state.current_player.name,
            current_player_index=self.game_state.current_player_index,
            turn_number=self.game_state.turn_number,
            current_phase=self.game_state.current_phase.value,
            available_actions=legal_actions,
            game_state_summary=self._get_game_state_summary()
        )
    
    def _get_game_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current game state."""
        current_player = self.game_state.current_player
        opponent = self.game_state.opponent
        
        return {
            'current_player': {
                'name': current_player.name,
                'lore': current_player.lore,
                'available_ink': current_player.available_ink,
                'total_ink': current_player.total_ink,
                'hand_size': len(current_player.hand),
                'characters_in_play': len(current_player.characters_in_play),
                'items_in_play': len(current_player.items_in_play)
            },
            'opponent': {
                'name': opponent.name,
                'lore': opponent.lore,
                'available_ink': opponent.available_ink,
                'total_ink': opponent.total_ink,
                'hand_size': len(opponent.hand),
                'characters_in_play': len(opponent.characters_in_play),
                'items_in_play': len(opponent.items_in_play)
            },
            'ink_played_this_turn': self.game_state.ink_played_this_turn,
            'actions_this_turn': [action.value for action in self.game_state.actions_this_turn],
            'winner': self.game_state.winner
        }
    
    def execute_player_action(self, action: GameAction, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a player's chosen action and return the result."""
        if self.state != GameLoopState.WAITING_FOR_PLAYER_ACTION:
            return {
                'success': False,
                'error': f'Cannot execute action in state {self.state.value}'
            }
        
        # Validate the action is legal
        legal_actions = self.engine.validator.get_all_legal_actions()
        action_tuple = (action, parameters)
        
        # Check if this action is in the legal actions (simplified check)
        is_legal = any(
            legal_action == action and 
            all(parameters.get(k) == v for k, v in legal_params.items())
            for legal_action, legal_params in legal_actions
        )
        
        if not is_legal:
            return {
                'success': False,
                'error': 'Action is not legal in current game state'
            }
        
        # Execute the action using stepped engine
        self.state = GameLoopState.EXECUTING_ACTION
        success, message = self.engine.execute_action_stepped(action, parameters)
        
        if not success:
            self.state = GameLoopState.WAITING_FOR_PLAYER_ACTION
            return {
                'success': False,
                'error': message
            }
        
        # Check if we need input for ability execution
        current_step = self.engine.get_current_step()
        if current_step and current_step.status == StepStatus.WAITING_FOR_INPUT:
            self.state = GameLoopState.WAITING_FOR_ABILITY_INPUT
            self.current_choice = self._create_choice_from_step(current_step)
            
            return {
                'success': True,
                'message': message,
                'requires_input': True,
                'choice': self.current_choice,
                'game_state': self._get_game_state_summary()
            }
        else:
            # Action completed, check if game is over or advance turn
            return self._complete_action_execution(message)
    
    def provide_ability_input(self, input_data: Any) -> Dict[str, Any]:
        """Provide input for a waiting ability and continue execution."""
        if self.state != GameLoopState.WAITING_FOR_ABILITY_INPUT:
            return {
                'success': False,
                'error': f'Cannot provide input in state {self.state.value}'
            }
        
        # Provide input to the step engine
        next_step = self.engine.provide_input_for_current_step(input_data)
        
        # Check if more input is needed
        current_step = self.engine.get_current_step()
        if current_step and current_step.status == StepStatus.WAITING_FOR_INPUT:
            # Still need more input
            self.current_choice = self._create_choice_from_step(current_step)
            
            return {
                'success': True,
                'message': 'Input provided, more input required',
                'requires_input': True,
                'choice': self.current_choice,
                'game_state': self._get_game_state_summary()
            }
        else:
            # No more input needed, complete action
            return self._complete_action_execution('Ability input completed')
    
    def _create_choice_from_step(self, step) -> GameChoice:
        """Create a GameChoice from a waiting step."""
        if not step.player_input:
            return GameChoice(
                choice_type="unknown",
                prompt=step.description,
                options=[],
                metadata={'step_id': step.step_id}
            )
        
        player_input = step.player_input
        choice_type_map = {
            StepType.CHOICE: "choice",
            StepType.SELECTION: "selection", 
            StepType.CONFIRMATION: "confirmation"
        }
        
        return GameChoice(
            choice_type=choice_type_map.get(player_input.input_type, "unknown"),
            prompt=player_input.prompt,
            options=player_input.options,
            metadata={
                'step_id': step.step_id,
                'constraints': player_input.constraints,
                'timeout_seconds': player_input.timeout_seconds
            }
        )
    
    def _complete_action_execution(self, message: str) -> Dict[str, Any]:
        """Complete action execution and determine next state."""
        self.current_choice = None
        
        # Check if game is over
        if self.game_state.winner:
            self.state = GameLoopState.GAME_OVER
            return {
                'success': True,
                'message': message,
                'game_over': True,
                'winner': self.game_state.winner,
                'game_state': self._get_game_state_summary()
            }
        
        # Check if we need to advance turn or phase
        current_phase = self.game_state.current_phase
        if current_phase.value == 'play':
            # Player can continue with more actions in play phase
            self.state = GameLoopState.WAITING_FOR_PLAYER_ACTION
            return {
                'success': True,
                'message': message,
                'requires_input': False,
                'turn_info': self.get_current_turn_info(),
                'game_state': self._get_game_state_summary()
            }
        else:
            # Other phases typically auto-advance
            self.state = GameLoopState.WAITING_FOR_PLAYER_ACTION
            return {
                'success': True,
                'message': message,
                'requires_input': False,
                'turn_info': self.get_current_turn_info(),
                'game_state': self._get_game_state_summary()
            }
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get the current state of the game loop."""
        base_state = {
            'loop_state': self.state.value,
            'game_state': self._get_game_state_summary()
        }
        
        if self.state == GameLoopState.WAITING_FOR_PLAYER_ACTION:
            base_state['turn_info'] = self.get_current_turn_info()
        elif self.state == GameLoopState.WAITING_FOR_ABILITY_INPUT:
            base_state['choice'] = self.current_choice
        elif self.state == GameLoopState.GAME_OVER:
            base_state['winner'] = self.game_state.winner
        
        return base_state
    
    def force_advance_turn(self) -> Dict[str, Any]:
        """Force advance to next player's turn (pass turn)."""
        if self.state not in [GameLoopState.WAITING_FOR_PLAYER_ACTION, GameLoopState.EXECUTING_ACTION]:
            return {
                'success': False,
                'error': f'Cannot advance turn in state {self.state.value}'
            }
        
        # Execute pass turn action
        success, message = self.engine.execute_action(GameAction.PASS_TURN, {})
        
        if success:
            self.state = GameLoopState.WAITING_FOR_PLAYER_ACTION
            return {
                'success': True,
                'message': message,
                'turn_info': self.get_current_turn_info(),
                'game_state': self._get_game_state_summary()
            }
        else:
            return {
                'success': False,
                'error': message
            }
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.state == GameLoopState.GAME_OVER or bool(self.game_state.winner)
    
    def get_step_queue_status(self) -> Dict[str, Any]:
        """Get the current status of the step queue (for debugging)."""
        return self.engine.get_step_queue_status()