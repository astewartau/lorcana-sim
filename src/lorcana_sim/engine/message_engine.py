"""MessageEngine for handling message flow and structured event data creation."""

from typing import Dict, Any, Optional, List
from ..models.game.game_state import GameState
from .event_system import GameEvent
from .choice_system import GameChoiceManager
from .move_validator import MoveValidator
from .game_messages import (
    GameMessage, MessageType, ActionRequiredMessage, ChoiceRequiredMessage, 
    StepExecutedMessage, GameOverMessage, LegalAction
)
from .game_moves import GameMove, ChoiceMove


class ReadyInkReportEffect:
    """A simple effect that reports ink ready events without doing any actual readying."""
    
    def __init__(self, ink_count: int):
        self.ink_count = ink_count
    
    def apply(self, target, context):
        # No-op: The readying was already done in phase_management.ready_step
        return target


class ReadyCharacterReportEffect:
    """A simple effect that reports character ready events without doing any actual readying."""
    
    def __init__(self, character_name: str, character=None):
        self.character_name = character_name
        self.character = character  # Store full character object if available
    
    def apply(self, target, context):
        # No-op: The readying was already done in phase_management.ready_step
        return target


def create_event_data(event: GameEvent, **context) -> Dict[str, Any]:
    """Create standardized event_data structure."""
    return {
        'event': event,
        'context': context
    }


class MessageEngine:
    """Handles message flow and structured event data creation - NO string formatting"""
    
    def __init__(self, game_state: GameState, choice_manager: GameChoiceManager, validator: MoveValidator, execution_engine=None):
        self.game_state = game_state
        self.choice_manager = choice_manager
        self.validator = validator
        self.execution_engine = execution_engine  # Reference to ExecutionEngine for coordination
        self.next_message_calls = 0
        
        # Message flow components
        self.waiting_for_input = False
        
        # Choice handling (integrated with messages)
        self.current_choice = None
        
        # Conditional effect evaluation tracking
        self.last_conditional_eval_turn = -1
        self.last_conditional_eval_phase = ""
        self.conditional_evaluations_this_call = 0
        self.max_conditional_evals_per_call = 1  # Prevent infinite loops
    
    def next_message(self, move: Optional[GameMove] = None, game_engine=None) -> GameMessage:
        """Process ONE effect and return ONE message.
        
        CRITICAL: This method executes exactly one effect from the ActionQueue.
        If that effect triggers hooks that queue more effects, those effects
        are NOT executed in this call - they wait for subsequent calls.
        """
        self.next_message_calls += 1
        # Reset conditional evaluation counter for this call
        self.conditional_evaluations_this_call = 0
        
        # 1. Validate input
        if self.waiting_for_input and move is None:
            raise ValueError("Expected move or choice but none provided")
        
        # 2. Process move if provided (queues effect, doesn't execute)
        if move:
            self._process_move(move)  # Converts to effect, queues at BACK
            self.waiting_for_input = False
        
        # 3. Check reactive conditions and process them immediately (create messages)
        if self.execution_engine:
            reactive_message = self._check_and_process_reactive_conditions()
            if reactive_message:
                return reactive_message
        
        # 4. Legacy conditional effects evaluation removed - now handled by modern event-driven system
        
        # 4.5. Queue default action if no actions pending and phase requires default behavior
        if self.execution_engine and not self.execution_engine.action_queue.has_pending_actions():
            self._queue_default_action_if_needed()
        
        # 5. Execute ONLY the next effect from queue (ONE EFFECT ONLY)
        if self.execution_engine and self.execution_engine.action_queue.has_pending_actions():
            # This executes ONE effect, which may:
            # - Emit events that trigger hooks
            # - Queue more effects (but doesn't execute them)
            # - Return a result that we turn into a message
            result = self.execution_engine.action_queue.process_next_action()
            
            # Check for pending choices AFTER executing the action
            # This is important for choice-generating effects
            if self.choice_manager.has_pending_choices():
                choice = self.choice_manager.get_current_choice()
                self.waiting_for_input = True
                msg = ChoiceRequiredMessage(
                    type=MessageType.CHOICE_REQUIRED,
                    player=choice.player,
                    choice=choice,
                    ability_source=getattr(choice, 'source', None)
                )
                return msg
            
            return self._create_message_from_result(result)
        
        # 6. Check for pending choices
        if self.choice_manager.has_pending_choices():
            choice = self.choice_manager.get_current_choice()
            self.waiting_for_input = True
            msg = ChoiceRequiredMessage(
                type=MessageType.CHOICE_REQUIRED,
                player=choice.player,
                choice=choice,
                ability_source=getattr(choice, 'source', None)
            )
            return msg
        
        # 7. Check game over
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
            
            msg = GameOverMessage(
                type=MessageType.GAME_OVER,
                player=self.game_state.current_player,
                winner=winner,
                reason=reason
            )
            return msg
        
        # 8. Check if player has legal actions
        legal_actions = self._get_legal_actions()
        
        # 9. Auto-queue phase progression only if no legal actions available
        if not legal_actions and not self.waiting_for_input:
            self._queue_phase_progression()  # Queues effect for next call
            # Return a special message indicating auto-progression
            msg = StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step="auto_progression_queued"
            )
            return msg
        
        # 10. Request player action
        self.waiting_for_input = True
        msg = ActionRequiredMessage(
            type=MessageType.ACTION_REQUIRED,
            player=self.game_state.current_player,
            phase=self.game_state.current_phase,
            legal_actions=legal_actions
        )
        return msg
    
    
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
    
    def _check_and_process_reactive_conditions(self) -> Optional[GameMessage]:
        """Check reactive conditions and create messages for any triggered events."""
        if not self.execution_engine:
            return None
        
        # Get reactive events from execution engine
        reactive_events = self.execution_engine._check_reactive_conditions()
        
        if not reactive_events:
            return None
            
        # Convert the first reactive event to a message
        # If there are multiple events, we'll return the first one and queue the rest
        first_event = reactive_events[0]
        message = self._create_reactive_message(first_event)
        
        # Note: Additional reactive events will be handled in subsequent next_message() calls
        # This follows the "ONE EFFECT PER CALL" principle
        
        return message
    
    def _create_reactive_message(self, event: Dict) -> Optional[GameMessage]:
        """Create a message for a reactive event."""
        from .event_system import GameEvent
        from .game_event_types import GameEventType
        
        # For now, we'll handle CHARACTER_BANISHED events
        # The reactive events are actually already processed by the execution engine
        # but we need to create messages for them
        if event.get('type') == GameEventType.CHARACTER_BANISHED:
            character = event.get('character')
            player = event.get('player')
            reason = event.get('reason', 'unknown')
            
            return StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step=GameEvent.CHARACTER_BANISHED,
                event_data=create_event_data(
                    GameEvent.CHARACTER_BANISHED,
                    character=character,
                    character_name=getattr(character, 'name', 'Unknown Character'),
                    player=player,
                    player_name=getattr(player, 'name', 'Unknown Player'),
                    reason=reason
                )
            )
        
        # Add handlers for other reactive event types as needed
        return None
    
    def _process_move(self, move: GameMove) -> None:
        """Convert move directly to effect and queue it."""
        if self.execution_engine:
            self.execution_engine.process_move(move)
    
    def _check_and_queue_reactive_effects(self) -> None:
        """Check reactive conditions and queue effects (don't execute)."""
        if self.execution_engine:
            reactive_events = self.execution_engine._check_reactive_conditions()
    
    
    
    def _queue_default_action_if_needed(self) -> None:
        """Queue default actions for phases that require automatic behavior."""
        current_phase = self.game_state.current_phase
        
        if current_phase.value == 'ready':
            # READY phase: Queue individual ready effects when queue is empty
            self._queue_ready_phase_effects()
        elif current_phase.value == 'set':
            # SET phase: Queue set phase effects when queue is empty
            self._queue_set_phase_effects()
        elif current_phase.value == 'draw':
            # DRAW phase: Queue draw phase effects when queue is empty
            self._queue_draw_phase_effects()
        # Note: PLAY phase should use the original logic that checks for legal actions

    def _queue_ready_phase_effects(self) -> None:
        """Queue ready phase effects using modernized phase management."""
        from ..models.abilities.composable.effects import PhaseProgressionEffect
        from .action_queue import ActionPriority
        from .event_system import GameEvent, EventContext
        
        # CRITICAL: Trigger READY_PHASE event first so abilities can trigger
        ready_phase_context = EventContext(
            event_type=GameEvent.READY_PHASE,
            player=self.game_state.current_player,
            game_state=self.game_state,
            additional_data={'phase': 'ready'},
            action_queue=self.execution_engine.action_queue if self.execution_engine else None
        )
        if hasattr(self, 'execution_engine') and self.execution_engine:
            from ..engine.event_system import GameEventManager
            event_manager = getattr(self.execution_engine, 'event_manager', None)
            if event_manager:
                event_manager.trigger_event(ready_phase_context)
        
        # Get ready step effects from modernized phase management
        ready_effects = self.game_state._phase_management.ready_step(self.game_state)
        
        # Queue each effect returned by phase management
        for effect in ready_effects:
            self.execution_engine.action_queue.enqueue(
                effect=effect,
                target=self.game_state.current_player,
                context={'game_state': self.game_state},
                priority=ActionPriority.NORMAL,
                source_description=str(effect)
            )
        
        # Finally, queue phase transition to SET
        self.execution_engine.action_queue.enqueue(
            effect=PhaseProgressionEffect(),
            target=self.game_state.current_player,
            context={'game_state': self.game_state},
            priority=ActionPriority.NORMAL,
            source_description="Phase transition to SET"
        )

    def _queue_set_phase_effects(self) -> None:
        """Queue individual set phase effects."""
        from ..models.abilities.composable.effects import PhaseProgressionEffect
        from .action_queue import ActionPriority
        
        # SET phase currently has no effects, just transition to DRAW
        self.execution_engine.action_queue.enqueue(
            effect=PhaseProgressionEffect(),
            target=self.game_state.current_player,
            context={'game_state': self.game_state},
            priority=ActionPriority.NORMAL,
            source_description="Phase transition to DRAW"
        )

    def _queue_draw_phase_effects(self) -> None:
        """Queue draw phase effects using modernized phase management."""
        from ..models.abilities.composable.effects import PhaseProgressionEffect
        from .action_queue import ActionPriority
        
        # Get draw step effects from modernized phase management
        draw_effects = self.game_state._phase_management.draw_step(self.game_state)
        
        # Queue each effect returned by phase management
        for effect in draw_effects:
            self.execution_engine.action_queue.enqueue(
                effect=effect,
                target=self.game_state.current_player,
                context={'game_state': self.game_state},
                priority=ActionPriority.NORMAL,
                source_description=str(effect)
            )
        
        # Finally, queue phase transition to PLAY
        self.execution_engine.action_queue.enqueue(
            effect=PhaseProgressionEffect(),
            target=self.game_state.current_player,
            context={'game_state': self.game_state},
            priority=ActionPriority.NORMAL,
            source_description="Phase transition to PLAY"
        )

    def _queue_draw_phase_default_action(self) -> None:
        """Queue appropriate default action for DRAW phase."""
        # Check if card has been drawn this turn
        if not self.game_state.card_drawn_this_turn:
            # Check first turn exception
            if self._is_first_turn_first_player():
                # Skip draw on first player's first turn
                self.game_state.card_drawn_this_turn = True  # Mark as "drawn" to progress
                self._queue_phase_progression()
            else:
                # Queue mandatory card draw
                self._queue_draw_card_action()
        else:
            # Already drawn, progress to next phase
            self._queue_phase_progression()

    def _is_first_turn_first_player(self) -> bool:
        """Check if this is the first player's first turn (no draw)."""
        # Only the very first player on the very first turn skips the draw
        # Turn 1, Player 0 = skip draw
        # Turn 1, Player 1 = draw normally
        return (self.game_state.turn_number == 1 and 
                self.game_state.current_player_index == 0)

    def _queue_draw_card_action(self) -> None:
        """Queue the mandatory draw card action for DRAW phase."""
        from ..models.abilities.composable.effects import DrawCards
        from .action_queue import ActionPriority
        
        self.execution_engine.action_queue.enqueue(
            effect=DrawCards(1),
            target=self.game_state.current_player,
            context={'game_state': self.game_state, 'mandatory_draw': True},
            priority=ActionPriority.NORMAL,
            source_description="Mandatory draw phase card draw"
        )

    def _queue_phase_progression(self) -> None:
        """Queue phase progression effect (don't execute)."""
        if self.execution_engine:
            from ..models.abilities.composable.effects import PhaseProgressionEffect
            from .action_queue import ActionPriority
            self.execution_engine.action_queue.enqueue(
                effect=PhaseProgressionEffect(),
                target=self.game_state.current_player,
                context={
                    'game_state': self.game_state, 
                    'action_executor': getattr(self.execution_engine, 'action_executor', None)
                },
                priority=ActionPriority.NORMAL,
                source_description="Phase progression"
            )
    
    def _create_message_from_result(self, result) -> GameMessage:
        """Create a message immediately from effect result."""
        if not result or not result.success:
            if result and hasattr(result, 'queued_action'):
                
                # Block the failed action temporarily to prevent infinite loops
                self._block_failed_action(result)
                
            msg = StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step="action_error"
            )
            return msg
        
        # Extract effect data for message creation
        executed_action = result.queued_action
        effect_data = self._extract_effect_data(executed_action, result)
        
        # Every action must generate a message - never return None
        
        step_description = executed_action.source_description if executed_action and executed_action.source_description else f"action_{result.action_id}"
        
        msg = StepExecutedMessage(
            type=MessageType.STEP_EXECUTED,
            player=self.game_state.current_player,
            step=step_description,
            event_data=effect_data
        )
        # Also set effect_data for compatibility with display logic
        msg.effect_data = effect_data
        return msg
    
    def _extract_effect_data(self, executed_action, result) -> dict:
        """Extract structured data about an executed effect for UI formatting."""
        if not executed_action:
            return {"type": "unknown"}
        
        from ..models.abilities.composable.effects import (
            DiscardCard, GainLoreEffect, DrawCards, BanishCharacter, 
            ReturnToHand, ExertCharacter, ReadyCharacter, RemoveDamageEffect,
            ChallengeEffect, PhaseProgressionEffect, InkCardEffect, PlayCharacterEffect,
            ReadyInk
        )
        
        effect = executed_action.effect
        target = executed_action.target
        
        # Extract structured data based on effect type
        if isinstance(effect, DiscardCard):
            card_name = getattr(target, 'name', str(target))
            if hasattr(target, 'controller') and target.controller:
                player_name = getattr(target.controller, 'name', 'Unknown Player')
            else:
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
                "target": target,
                "drawn_cards": getattr(effect, '_drawn_cards', [])
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
        
        elif isinstance(effect, ChallengeEffect):
            # Return the challenge result data that the UI expects
            return {
                "type": "challenge",
                "context": effect._challenge_result if hasattr(effect, '_challenge_result') and effect._challenge_result else {},
                "attacker": effect.attacker,
                "defender": effect.defender,
                "attacker_name": getattr(effect.attacker, 'name', 'Unknown Character'),
                "defender_name": getattr(effect.defender, 'name', 'Unknown Character')
            }
        
        elif isinstance(effect, PhaseProgressionEffect):
            # Phase transition effects should show the phase change, not "played a card"
            return {
                "type": "phase_transition",
                "previous_phase": getattr(effect, '_previous_phase', None),
                "new_phase": getattr(effect, '_new_phase', None),
                "player": getattr(effect, '_player', None) or target
            }
        
        elif isinstance(effect, InkCardEffect):
            return {
                "type": "ink_card",
                "card_name": getattr(effect.card, 'name', 'Unknown Card'),
                "card": effect.card,  # Include full card object for detailed display
                "player": getattr(effect, '_player', None) or target
            }
        
        elif isinstance(effect, PlayCharacterEffect):
            return {
                "type": "play_character",
                "character_name": getattr(effect.card, 'name', 'Unknown Character'),
                "character": effect.card,  # Include full card object for detailed display
                "player": getattr(effect, '_player', None) or target
            }
        
        elif isinstance(effect, ReadyInk):
            return {
                "type": "ready_ink",
                "ink_count": len(getattr(effect, 'readied_cards', [])),
                "player": target
            }
        
        elif isinstance(effect, ReadyInkReportEffect):
            return {
                "type": "ready_ink",
                "ink_count": effect.ink_count,
                "player": target
            }
        
        elif isinstance(effect, ReadyCharacterReportEffect):
            return {
                "type": "ready_character",
                "character_name": effect.character_name,
                "character": effect.character,  # Include full character object
                "player": target
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
    
    def _block_failed_action(self, result) -> None:
        """Block a failed action temporarily to prevent infinite loops."""
        if not result or not hasattr(result, 'queued_action') or not result.queued_action:
            return
        
        executed_action = result.queued_action
        effect = executed_action.effect
        
        # Import effect types
        from ..models.abilities.composable.effects import (
            PlayCharacterEffect, InkCardEffect, PlayActionEffect, 
            PlayItemEffect, QuestEffect, ChallengeEffect
        )
        
        # Map effect types to actions and extract parameters
        if isinstance(effect, PlayCharacterEffect):
            action = "play_character"
            parameters = {'card': effect.card}
        elif isinstance(effect, InkCardEffect):
            action = "play_ink"
            parameters = {'card': effect.card}
        elif isinstance(effect, PlayActionEffect):
            action = "play_action"
            parameters = {'card': effect.card}
        elif isinstance(effect, PlayItemEffect):
            action = "play_item"
            parameters = {'card': effect.card}
        elif isinstance(effect, QuestEffect):
            action = "quest_character"
            parameters = {'character': effect.character}
        elif isinstance(effect, ChallengeEffect):
            action = "challenge_character"
            parameters = {'attacker': effect.attacker, 'defender': effect.defender}
        else:
            # Unknown effect type, can't block
            print(f"🐛 Cannot block unknown effect type: {type(effect).__name__}")
            return
        
        # Block the action
        self.validator.block_action_temporarily(action, parameters)
    
