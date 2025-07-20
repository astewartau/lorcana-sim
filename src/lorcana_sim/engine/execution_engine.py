"""Execution engine for handling all internal game logic execution."""

from typing import Dict, Any, List, Optional, Deque
from collections import deque
from ..models.game.game_state import GameState
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from .move_validator import MoveValidator
from .event_system import GameEventManager, GameEvent
from .damage_calculator import DamageCalculator
from .choice_system import GameChoiceManager
from .action_result import ActionResult
# NOTE: Step system imports removed in Phase 4
from .action_queue import ActionQueue
from .action_executor import ActionExecutor
from .game_moves import GameMove, InkMove, PlayMove, QuestMove, ChallengeMove, SingMove
from ..models.abilities.composable.effects import (
    InkCardEffect, PlayCharacterEffect, PlayActionEffect, PlayItemEffect,
    QuestEffect, ChallengeEffect, SingEffect, PhaseProgressionEffect
)
from .action_queue import ActionPriority
from .game_messages import StepExecutedMessage, MessageType
from ..models.abilities.composable.conditional_effects import ActivationZone


class ExecutionEngine:
    """Handles all internal game logic execution.
    
    Combines action execution, step progression, and conditional effects.
    """
    
    def __init__(self, game_state, validator, event_manager, damage_calculator, choice_manager, execution_mode):
        self.game_state = game_state
        self.validator = validator
        self.event_manager = event_manager
        self.damage_calculator = damage_calculator
        self.choice_manager = choice_manager
        
        # Execution components
        self.action_executor = ActionExecutor(
            game_state, validator, event_manager, damage_calculator, choice_manager
        )
        # NOTE: step_engine removed in Phase 4
        self.action_queue = ActionQueue(event_manager)
        # NOTE: current_action_steps removed in Phase 4
        
        # Conditional effect evaluation
        self._condition_evaluator = None
    
    def execute_action(self, action: str, parameters: Dict) -> ActionResult:
        """Execute action directly and return result."""
        result = self._execute_action_direct(action, parameters)
        
        # Draw events are now handled by the new on-demand message generation system
        # when draw effects are executed through the ActionQueue ("ONE EFFECT PER CALL" principle)
        
        return result
    
    def process_move(self, move: GameMove) -> str:
        """Convert move directly to effect and queue it.
        
        Returns:
            The action ID for tracking
        """
        from .game_moves import PassMove, ChoiceMove
        
        if isinstance(move, InkMove):
            return self.action_queue.enqueue(
                effect=InkCardEffect(move.card),
                target=self.game_state.current_player,
                context={'game_state': self.game_state},
                priority=ActionPriority.NORMAL,
                source_description=f"Player inks {move.card.name}"
            )
            
        elif isinstance(move, PlayMove):
            if isinstance(move.card, CharacterCard):
                effect = PlayCharacterEffect(move.card)
            elif isinstance(move.card, ActionCard):
                effect = PlayActionEffect(move.card)
            elif isinstance(move.card, ItemCard):
                effect = PlayItemEffect(move.card)
            else:
                raise ValueError(f"Unknown card type for PlayMove: {type(move.card)}")
                
            return self.action_queue.enqueue(
                effect=effect,
                target=self.game_state.current_player,
                context={'game_state': self.game_state},
                priority=ActionPriority.NORMAL,
                source_description=f"Player plays {move.card.name}"
            )
            
        elif isinstance(move, QuestMove):
            return self.action_queue.enqueue(
                effect=QuestEffect(move.character),
                target=move.character,
                context={'game_state': self.game_state},
                priority=ActionPriority.NORMAL,
                source_description=f"{move.character.name} quests"
            )
            
        elif isinstance(move, ChallengeMove):
            return self.action_queue.enqueue(
                effect=ChallengeEffect(move.attacker, move.defender),
                target=move.defender,
                context={'game_state': self.game_state, 'attacker': move.attacker},
                priority=ActionPriority.NORMAL,
                source_description=f"{move.attacker.name} challenges {move.defender.name}"
            )
            
        elif isinstance(move, SingMove):
            return self.action_queue.enqueue(
                effect=SingEffect(move.singer, move.song),
                target=move.song,
                context={'game_state': self.game_state, 'singer': move.singer},
                priority=ActionPriority.NORMAL,
                source_description=f"{move.singer.name} sings {move.song.name}"
            )
            
        elif isinstance(move, PassMove):
            return self.action_queue.enqueue(
                effect=PhaseProgressionEffect(),
                target=self.game_state,
                context={'game_state': self.game_state},
                priority=ActionPriority.NORMAL,
                source_description="Player passes/progresses"
            )
            
        elif isinstance(move, ChoiceMove):
            # Choices resolve immediately, not queued
            self.choice_manager.resolve_choice(move.choice_id, move.option)
            return ""  # No action ID for immediate resolution
            
        # NOTE: ActionMove support REMOVED in Phase 4
        
        raise ValueError(f"Cannot process move type: {type(move)}")

    # NOTE: process_move_as_steps REMOVED in Phase 4 - use process_move instead
    
    def execute_next_effect(self) -> Optional[Any]:
        """Execute the next effect from the action queue.
        
        Returns:
            The result of executing the effect, or None if queue is empty
        """
        return self.action_queue.process_next_action()
    
    def queue_reactive_effects(self) -> List[str]:
        """Check and queue reactive effects that should trigger.
        
        Returns:
            List of action IDs for queued reactive effects
        """
        action_ids = []
        
        # Check reactive conditions (like banishment)
        reactive_events = self._check_reactive_conditions()
        
        # For now, we don't queue effects for reactive events
        # This will be enhanced when we integrate with hook system
        
        return action_ids
    
    def queue_conditional_effects(self) -> List[str]:
        """Evaluate and queue conditional effects.
        
        Returns:
            List of action IDs for queued conditional effects  
        """
        action_ids = []
        
        # This will be implemented when conditional effects are uncommented
        # For now, just return empty list
        
        return action_ids
    
    def has_pending_effects(self) -> bool:
        """Check if there are effects waiting to be executed."""
        return self.action_queue.has_pending_actions()

    # NOTE: execute_next_step REMOVED in Phase 4 - use execute_next_effect instead
    
    def evaluate_conditional_effects(self, trigger_context) -> List[Dict]:
        """Evaluate and trigger conditional effects."""
        from ..models.abilities.composable.condition_evaluator import EvaluationTrigger
        
        if self._condition_evaluator is None:
            return []
            
        return self._condition_evaluator.evaluate_all_conditions(
            self.game_state, 
            trigger_context
        )
    
    def can_execute_action(self, action: str, parameters: Dict) -> bool:
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
        # NOTE: Action conversion simplified in Phase 4
        # Actions are now handled as strings directly
        
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
            if action == "sing_song":
                # ActionExecutor expects 'character' and 'song' keys
                adjusted_params = {
                    'character': parameters.get('singer'),
                    'song': parameters.get('song')
                }
                result = self.action_executor.execute_action(action, adjusted_params)
            else:
                result = self.action_executor.execute_action(action, parameters)
            
            return result
        
        except Exception as e:
            return ActionResult.failure_result(action, f"Error executing action: {str(e)}")
    
    # NOTE: _convert_to_action_move REMOVED in Phase 4
    
    # NOTE: _convert_action_move_to_effect REMOVED in Phase 4
    
    # NOTE: _create_action_steps REMOVED in Phase 4
    
    # NOTE: _create_choice_steps REMOVED in Phase 4
    
    # NOTE: _execute_next_step REMOVED in Phase 4
    
    def _evaluate_conditional_effects_before_step(self) -> List[Dict]:
        """Evaluate conditional effects before a step is executed."""
        from ..models.abilities.composable.condition_evaluator import EvaluationTrigger
        
        events = []
        
        # Evaluate conditional effects (reactive conditions are handled separately in MessageEngine)
        if self._condition_evaluator is not None:
            conditional_events = self._condition_evaluator.evaluate_all_conditions(
                self.game_state, 
                EvaluationTrigger.STEP_EXECUTED
            )
            events.extend(conditional_events)
        
        return events
    
    def _check_reactive_conditions(self) -> List[Dict]:
        """Check for reactive conditions that should trigger after game state changes.
        
        This includes banishment (willpower <= 0), but can be extended for other 
        reactive conditions like discard limits, win conditions, etc.
        """
        from .event_system import EventContext
        
        events = []
        
        # Check banishment conditions (willpower <= 0)
        characters_to_banish = []
        for player in self.game_state.players:
            for character in player.characters_in_play[:]:  # Copy list to avoid modification during iteration
                if character.current_willpower <= 0:
                    characters_to_banish.append((character, player))
        
        # Banish characters and create events - but only process ONE at a time
        if characters_to_banish:
            # Only process the first character that needs banishing
            character, player = characters_to_banish[0]
            
            # Actually banish the character
            if character in player.characters_in_play:
                player.characters_in_play.remove(character)
                player.discard_pile.append(character)
                
                # Trigger CHARACTER_BANISHED event
                banish_context = EventContext(
                    event_type=GameEvent.CHARACTER_BANISHED,
                    player=player,
                    game_state=self.game_state,
                    source=character,
                    additional_data={
                        'character': character,
                        'reason': 'willpower_depleted'
                    }
                )
                
                # Trigger the event through the event manager
                self.event_manager.trigger_event(banish_context)
                
                # Create event dict for message system
                from .game_event_types import GameEventType
                events.append({
                    'type': GameEventType.CHARACTER_BANISHED,
                    'character': character,
                    'character_name': character.name,
                    'player': player,
                    'player_name': player.name,
                    'reason': 'willpower_depleted'
                })
        
        return events
    
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
    
    def _resolve_choice_direct(self, choice_id: str, option: str) -> ActionResult:
        """Resolve a choice directly."""
        # This should delegate to the choice manager
        from .action_result import ActionResult
        # NOTE: GameAction import removed in Phase 4
        
        try:
            success = self.choice_manager.provide_choice(choice_id, option)
            if success:
                return ActionResult.success_result("progress", {})
            else:
                return ActionResult.failure_result("progress", f"Failed to resolve choice {choice_id}")
        except Exception as e:
            return ActionResult.failure_result("progress", f"Error resolving choice: {str(e)}")
    
    
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