"""Condition evaluation system for continuous ability management."""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable, TYPE_CHECKING
from enum import Enum

from .conditional_effects import ConditionalEffect, ConditionType

if TYPE_CHECKING:
    from ...game.game_state import GameState
    from ...cards.character_card import CharacterCard


class EvaluationTrigger(Enum):
    """When condition evaluation should be triggered."""
    PHASE_CHANGE = "phase_change"
    TURN_CHANGE = "turn_change"
    CARD_PLAYED = "card_played"
    CARD_MOVED = "card_moved"
    STEP_EXECUTED = "step_executed"
    ABILITY_RESOLVED = "ability_resolved"
    FORCE_EVALUATE = "force_evaluate"


@dataclass
class ConditionEvaluator:
    """Manages when and how conditional effects are evaluated."""
    
    # Track evaluation state
    last_evaluated_turn: int = -1
    last_evaluated_phase: str = ""
    evaluation_counter: int = 0
    
    # Performance tracking
    evaluations_this_turn: int = 0
    max_evaluations_per_turn: int = 100  # Prevent infinite loops
    
    # Debugging
    evaluation_log: List[Dict[str, Any]] = field(default_factory=list)
    max_log_entries: int = 50
    debug_mode: bool = False
    
    def should_evaluate(self, game_state: 'GameState', trigger: EvaluationTrigger) -> bool:
        """Determine if conditional effects should be evaluated based on the trigger."""
        current_turn = game_state.turn_number
        current_phase = game_state.current_phase.value
        
        # Check for turn/phase changes
        turn_changed = current_turn != self.last_evaluated_turn
        phase_changed = current_phase != self.last_evaluated_phase
        
        # Reset evaluation counter on new turn
        if turn_changed:
            self.evaluations_this_turn = 0
        
        # Prevent excessive evaluations
        if self.evaluations_this_turn >= self.max_evaluations_per_turn:
            if self.debug_mode:
                self._log_evaluation("SKIPPED_MAX_EVALS", game_state, trigger, 
                                   {"count": self.evaluations_this_turn})
            return False
        
        # Determine if we should evaluate based on trigger type
        should_eval = False
        
        if trigger == EvaluationTrigger.FORCE_EVALUATE:
            should_eval = True
        elif trigger == EvaluationTrigger.TURN_CHANGE and turn_changed:
            should_eval = True
        elif trigger == EvaluationTrigger.PHASE_CHANGE and phase_changed:
            should_eval = True
        elif trigger in [EvaluationTrigger.CARD_PLAYED, EvaluationTrigger.CARD_MOVED]:
            # Always evaluate on card movement/play
            should_eval = True
        elif trigger == EvaluationTrigger.STEP_EXECUTED:
            # Only evaluate on step execution if turn or phase changed
            # Most conditional effects should only trigger on turn/phase changes
            should_eval = turn_changed or phase_changed
        elif trigger == EvaluationTrigger.ABILITY_RESOLVED:
            # Evaluate after abilities resolve
            should_eval = True
        
        if self.debug_mode and should_eval:
            self._log_evaluation("EVALUATION_TRIGGERED", game_state, trigger, {
                "turn_changed": turn_changed,
                "phase_changed": phase_changed
            })
        
        return should_eval
    
    def evaluate_all_conditions(self, game_state: 'GameState', trigger: EvaluationTrigger) -> List[Dict]:
        """Evaluate all conditional effects and return any events generated."""
        if not self.should_evaluate(game_state, trigger):
            return []
        
        events = []
        self.evaluations_this_turn += 1
        self.evaluation_counter += 1
        
        # Update tracking
        self.last_evaluated_turn = game_state.turn_number
        self.last_evaluated_phase = game_state.current_phase.value
        
        try:
            # Use the specific effects evaluator instead of the generic zone manager
            from .zone_manager import ZoneManager
            zone_manager = game_state._zone_management.zone_manager
            zone_events = self.evaluate_specific_effects(
                list(zone_manager.all_effects), 
                game_state, 
                trigger
            )
            events.extend(zone_events)
            
            if self.debug_mode:
                self._log_evaluation("EVALUATION_COMPLETED", game_state, trigger, {
                    "events_generated": len(zone_events),
                    "total_evaluations": self.evaluation_counter
                })
        
        except Exception as e:
            if self.debug_mode:
                self._log_evaluation("EVALUATION_ERROR", game_state, trigger, {
                    "error": str(e)
                })
            # Don't let evaluation errors crash the game
            print(f"Error during condition evaluation: {e}")
        
        return events
    
    def evaluate_specific_effects(self, 
                                effects: List[ConditionalEffect], 
                                game_state: 'GameState',
                                trigger: EvaluationTrigger) -> List[Dict]:
        """Evaluate specific conditional effects and return events for abilities that actually trigger."""
        events = []
        
        for effect in effects:
            try:
                # Check if effect is in valid zone
                if not effect.is_in_valid_zone(game_state):
                    # If effect was active but source moved to invalid zone, deactivate
                    if effect.is_active:
                        event = effect.remove_effect(game_state)
                        if event:
                            events.append(event)
                    continue
                
                # Force evaluation for specific effects
                if trigger == EvaluationTrigger.FORCE_EVALUATE:
                    print(f"Force evaluating effect {effect.effect_id} in {game_state.current_phase.value} phase")
                    effect.last_evaluation_turn = -1
                
                # Skip if we don't need to evaluate
                if not effect.should_evaluate(game_state):
                    print(f"Skipping evaluation for effect {effect.effect_id} in {game_state.current_phase.value} phase")
                    continue
                
                # Evaluate condition
                print(f"Evaluating effect {effect.effect_id} in {game_state.current_phase.value} phase")
                should_be_active = effect.evaluate_condition(game_state)
                
                if should_be_active and not effect.is_active:
                    print(f"Effect {effect.effect_id} is now active in {game_state.current_phase.value} phase")
                    # Apply effect - only return events for abilities that actually trigger
                    event = effect.apply_effect(game_state)
                    if event:
                        events.append(event)
                elif not should_be_active and effect.is_active:
                    print(f"Effect {effect.effect_id} is no longer active in {game_state.current_phase.value} phase")
                    # Remove effect - but don't create debug messages for abilities that stop triggering
                    # This prevents spam of abilities that didn't actually trigger
                    effect.remove_effect(game_state)
                    # Note: No event added to prevent debug spam
            
            except Exception as e:
                if self.debug_mode:
                    self._log_evaluation("EFFECT_ERROR", game_state, trigger, {
                        "effect_id": effect.effect_id,
                        "error": str(e)
                    })
                print(f"Error evaluating effect {effect.effect_id}: {e}")
        
        return events
    
    def force_evaluate_card(self, card: 'CharacterCard', game_state: 'GameState') -> List[Dict]:
        """Force evaluation of all conditional effects on a specific card."""
        if not hasattr(card, 'conditional_effects'):
            return []
        
        return self.evaluate_specific_effects(
            card.conditional_effects, 
            game_state, 
            EvaluationTrigger.FORCE_EVALUATE
        )
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get statistics about condition evaluations."""
        return {
            "total_evaluations": self.evaluation_counter,
            "evaluations_this_turn": self.evaluations_this_turn,
            "last_evaluated_turn": self.last_evaluated_turn,
            "last_evaluated_phase": self.last_evaluated_phase,
            "max_evaluations_per_turn": self.max_evaluations_per_turn,
            "log_entries": len(self.evaluation_log)
        }
    
    def reset_turn_stats(self) -> None:
        """Reset per-turn evaluation statistics."""
        self.evaluations_this_turn = 0
    
    def enable_debug_mode(self, enabled: bool = True) -> None:
        """Enable or disable debug logging."""
        self.debug_mode = enabled
        if not enabled:
            self.evaluation_log.clear()
    
    def get_evaluation_log(self) -> List[Dict[str, Any]]:
        """Get the evaluation log for debugging."""
        return self.evaluation_log.copy()
    
    def clear_evaluation_log(self) -> None:
        """Clear the evaluation log."""
        self.evaluation_log.clear()
    
    def _log_evaluation(self, event_type: str, game_state: 'GameState', 
                       trigger: EvaluationTrigger, details: Dict[str, Any]) -> None:
        """Log an evaluation event for debugging."""
        if not self.debug_mode:
            return
        
        log_entry = {
            "event_type": event_type,
            "turn": game_state.turn_number,
            "phase": game_state.current_phase.value,
            "trigger": trigger.value,
            "evaluation_count": self.evaluation_counter,
            "details": details
        }
        
        self.evaluation_log.append(log_entry)
        
        # Limit log size
        if len(self.evaluation_log) > self.max_log_entries:
            self.evaluation_log.pop(0)


# Global condition evaluation functions for common patterns
def create_turn_based_condition(during_controllers_turn: bool = True) -> Callable[['GameState', 'CharacterCard'], bool]:
    """Create a condition that checks if it's the controller's turn or opponent's turn."""
    def condition(game_state: 'GameState', source_card: 'CharacterCard') -> bool:
        # Find the card's controller
        for player in game_state.players:
            if (source_card in player.characters_in_play or 
                source_card in player.hand or 
                source_card in player.discard_pile):
                is_controllers_turn = game_state.current_player == player
                return is_controllers_turn if during_controllers_turn else not is_controllers_turn
        return False
    return condition


def create_character_present_condition(character_name: str, 
                                     controller_only: bool = True) -> Callable[['GameState', 'CharacterCard'], bool]:
    """Create a condition that checks if a named character is in play."""
    def condition(game_state: 'GameState', source_card: 'CharacterCard') -> bool:
        # Find the card's controller if we only check controller's characters
        controller = None
        if controller_only:
            for player in game_state.players:
                if (source_card in player.characters_in_play or 
                    source_card in player.hand or 
                    source_card in player.discard_pile):
                    controller = player
                    break
        
        # Check for the named character
        players_to_check = [controller] if controller and controller_only else game_state.players
        
        for player in players_to_check:
            for char in player.characters_in_play:
                if character_name.lower() in char.name.lower():
                    return True
        return False
    return condition


def create_phase_condition(phase_name: str) -> Callable[['GameState', 'CharacterCard'], bool]:
    """Create a condition that checks if the game is in a specific phase."""
    def condition(game_state: 'GameState', source_card: 'CharacterCard') -> bool:
        return game_state.current_phase.value == phase_name
    return condition