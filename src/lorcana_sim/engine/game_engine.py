"""Game engine for executing actions and managing state transitions."""

from typing import Dict, Any, Tuple, Optional, List, Union
from collections import deque
from ..models.game.game_state import GameState, GameAction, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card
from .move_validator import MoveValidator
from .event_system import GameEventManager, GameEvent, EventContext
from .damage_calculator import DamageCalculator, DamageType
from .action_result import ActionResult, ActionResultType
from .choice_system import GameChoiceManager, ChoiceContext
from .step_system import StepProgressionEngine, GameStep, StepType, ExecutionMode, StepStatus
from .input_system import InputManager, PlayerInput, AbilityInputBuilder
from .state_serializer import SnapshotManager
from .game_messages import (
    GameMessage, MessageType, ActionRequiredMessage, ChoiceRequiredMessage, 
    StepExecutedMessage, GameOverMessage, LegalAction
)
from .game_moves import GameMove, ActionMove, ChoiceMove, InkMove, PlayMove, QuestMove, ChallengeMove, SingMove, PassMove
from .action_queue import ActionQueue, ActionPriority, QueuedAction
from .action_executor import ActionExecutor
from .execution_engine import ExecutionEngine
from .message_engine import MessageEngine
from .choice_engine import ChoiceEngine
from ..models.abilities.composable.conditional_effects import ActivationZone


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
        
        # Message stream components - legacy for compatibility during transition
        self.message_queue = deque()
        self.current_steps = deque()
        self.waiting_for_input = False
        self.current_choice = None
        
        # Three specialized engines
        self.execution_engine = ExecutionEngine(
            game_state, self.validator, self.event_manager, 
            self.damage_calculator, self.choice_manager, execution_mode, self.message_queue
        )
        self.message_engine = MessageEngine(
            game_state, self.choice_manager, self.validator, self.execution_engine,
            shared_message_queue=self.message_queue, shared_current_steps=self.current_steps
        )
        self.choice_engine = ChoiceEngine(game_state, self.choice_manager)
        
        # Legacy components for compatibility
        self.step_engine = StepProgressionEngine(execution_mode)
        self.input_manager = InputManager()
        self.snapshot_manager = SnapshotManager()
        
        # Set up integration
        self.event_manager.set_step_engine(self.step_engine)
        self._setup_step_listeners()
        self._setup_input_handlers()
        
        # Register all triggered abilities from characters currently in play
        self.event_manager.rebuild_listeners()
    
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
                game_state=self.game_state
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
    
    
    def advance_step(self) -> Optional[GameStep]:
        """Advance to the next step in manual mode."""
        return self.step_engine.execute_next_step()
    
    def provide_input_for_current_step(self, input_data: Any) -> Optional[GameStep]:
        """Provide input for the current step that's waiting for input."""
        return self.step_engine.provide_input(input_data)
    
    def get_current_step(self) -> Optional[GameStep]:
        """Get the current step being executed."""
        return self.step_engine.get_current_step()
    
    def get_step_queue_status(self) -> Dict[str, Any]:
        """Get the current status of the step queue."""
        return self.step_engine.get_queue_state()
    
    def pause_execution(self) -> None:
        """Pause step execution."""
        self.step_engine.pause()
    
    def resume_execution(self) -> None:
        """Resume step execution."""
        self.step_engine.resume()
    
    def clear_step_queue(self) -> None:
        """Clear the step queue."""
        self.step_engine.clear_queue()
        self.current_action_steps.clear()
    
    def set_execution_mode(self, mode: ExecutionMode) -> None:
        """Set the execution mode."""
        self.step_engine.step_queue.execution_mode = mode
    
    def register_player_input_provider(self, player_id: str, provider) -> None:
        """Register an input provider for a player."""
        self.input_manager.register_input_provider(player_id, provider)
    
    def force_evaluate_conditional_effects(self) -> None:
        """Force evaluation of all conditional effects - delegates to ExecutionEngine."""
        events = self.execution_engine.force_evaluate_conditional_effects()
        if events:
            self._queue_conditional_effect_events(events)
    
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
    
    def _queue_game_event_message(self, event: dict) -> None:
        """Queue a message for a game event from the regular game engine."""
            
        event_type = event.get('type')
        player_name = event.get('player', 'Unknown')
        
        if event_type == 'card_drawn':
            # Get player object - use current player if name matches, otherwise look up
            player = None
            if player_name == self.game_state.current_player.name:
                player = self.game_state.current_player
            elif player_name == self.game_state.players[0].name:
                player = self.game_state.players[0]
            elif player_name == self.game_state.players[1].name:
                player = self.game_state.players[1]
            
            # Queue draw event message
            cards_drawn = event.get('cards_drawn', [])
            for card in cards_drawn:
                draw_message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=GameEvent.CARD_DRAWN,
                    event_data=create_event_data(
                        GameEvent.CARD_DRAWN,
                        player=player,
                        card=card
                    )
                )
                self.message_queue.append(draw_message)
    
    def _check_for_ability_triggers(self) -> None:
        """Check for ability triggers and queue messages for them."""
            
        # Check if Royal Guard has gained challenger bonus (indicating HEAVILY ARMED triggered)
        current_player = self.game_state.current_player
        for character in current_player.characters_in_play:
            if character.name == "Royal Guard" and character.current_challenger_bonus > 0:
                # Check if this is a new bonus from this turn
                for amount, duration in character.challenger_bonuses:
                    if duration in ["turn", "this_turn"]:
                        ability_message = StepExecutedMessage(
                            type=MessageType.STEP_EXECUTED,
                            player=current_player,
                            step=GameEvent.ABILITY_TRIGGERED,
                            event_data=create_event_data(
                                GameEvent.ABILITY_TRIGGERED,
                                character=character,
                                ability_name="HEAVILY ARMED",
                                effect_type="challenger_bonus",
                                amount=amount
                            )
                        )
                        self.message_queue.append(ability_message)
                        break
    
    def _process_move(self, move: GameMove) -> None:
        """Process a player move."""
            
        if isinstance(move, ActionMove):
            # Break action into steps and queue them
            steps = self.execution_engine.process_move_as_steps(move)
            if steps:
                self.current_steps.extend(steps)
            else:
                # Fall back to direct execution if no steps created
                result = self.execution_engine.execute_action(move.action, move.parameters)
                self._queue_result_message(result)
            
        elif isinstance(move, (InkMove, PlayMove, QuestMove, ChallengeMove, SingMove)):
            # Convert specific moves to action moves and delegate to execution engine
            steps = self.execution_engine.process_move_as_steps(move)
            if steps:
                self.current_steps.extend(steps)
            else:
                # Fall back to direct execution if no steps created
                action_move = self.execution_engine._convert_to_action_move(move)
                result = self.execution_engine.execute_action(action_move.action, action_move.parameters)
                self._queue_result_message(result)
            
        elif isinstance(move, PassMove):
            # Handle pass/progress
            # If we're in ready phase and this is the start of a new turn, execute ready step first
            if (self.game_state.current_phase.value == 'ready' and 
                hasattr(self.game_state, '_needs_ready_step')):
                readied_items = self.game_state.ready_step()
                # Queue ready step messages
                for readied_item in readied_items:
                    ready_message = StepExecutedMessage(
                            type=MessageType.STEP_EXECUTED,
                            player=self.game_state.current_player,
                            step=GameEvent.CHARACTER_READIED,
                            event_data=readied_item  # Pass the full event data
                    )
                    self.message_queue.append(ready_message)
                # Clear the flag
                delattr(self.game_state, '_needs_ready_step')
            
            result = self.execution_engine.execute_action(GameAction.PROGRESS, {})
            self._queue_result_message(result)
            
        elif isinstance(move, ChoiceMove):
            # Resolve choice and continue
            self._resolve_choice(move.choice_id, move.option)
            self.current_choice = None
    
    def _execute_next_step(self) -> StepExecutedMessage:
        """Execute the next step and return message - delegates to ExecutionEngine."""
        return self.execution_engine.execute_next_step()
    
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
            ReturnToHand, ExertCharacter, ReadyCharacter, RemoveDamageEffect
        )
        
        effect = executed_action.effect
        target = executed_action.target
        
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
    
    def _queue_result_message(self, result):
        """Queue a result message from action execution."""
            
        if result.success:
            # Create a clean result description based on action type
            description = "Action completed"
            if hasattr(result, 'result_type'):
                result_type = result.result_type.value
                
                # Create more descriptive messages
                if result_type == "ink_played":
                    card = result.data.get('card') if result.data else None
                    card_name = card.name if card and hasattr(card, 'name') else 'card'
                    ink_after = result.data.get('ink_after', 0) if result.data else 0
                    total_ink = result.data.get('total_ink', 0) if result.data else 0
                    description = f"Inked {card_name} → {ink_after}/{total_ink} ink"
                elif result_type == "character_played":
                    character = result.data.get('character') if result.data else None
                    char_name = character.name if character and hasattr(character, 'name') else 'character'
                    cost = character.cost if character and hasattr(character, 'cost') else 0
                    ink_after = result.data.get('ink_after', 0) if result.data else 0
                    total_ink = result.data.get('total_ink', 0) if result.data else 0
                    description = f"Played {char_name} ({cost} ink) → {ink_after}/{total_ink} ink"
                elif result_type == "character_quested":
                    character = result.data.get('character') if result.data else None
                    lore = result.data.get('lore_gained', 0) if result.data else 0
                    # For questing, the source is the character that quested
                    description = ""  # Will be handled by event_data
                elif result_type == "character_challenged":
                    attacker = result.data.get('attacker') if result.data else None
                    defender = result.data.get('defender') if result.data else None
                    attacker_name = attacker.name if attacker and hasattr(attacker, 'name') else 'character'
                    defender_name = defender.name if defender and hasattr(defender, 'name') else 'character'
                    attacker_str = attacker.current_strength if attacker and hasattr(attacker, 'current_strength') else 0
                    defender_str = defender.current_strength if defender and hasattr(defender, 'current_strength') else 0
                    attacker_dmg = result.data.get('attacker_damage_taken', 0) if result.data else 0
                    defender_dmg = result.data.get('defender_damage_taken', 0) if result.data else 0
                    description = f"{attacker_name} ({attacker_str} str) vs {defender_name} ({defender_str} str) → {defender_dmg}/{attacker_dmg} damage"
                elif result_type == "phase_advanced":
                    old_phase = result.data.get('old_phase') if result.data else None
                    new_phase = result.data.get('new_phase') if result.data else None
                    old_name = old_phase.value if old_phase and hasattr(old_phase, 'value') else 'phase'
                    new_name = new_phase.value if new_phase and hasattr(new_phase, 'value') else 'phase'
                    description = f"{old_name} → {new_name} phase"
                    
                    # Evaluate conditional effects on phase change
                    self._evaluate_conditional_effects_on_phase_change()
                elif result_type == "turn_ended":
                    # Create cleaner turn transition message
                    old_player = result.data.get('old_player') if result.data else None
                    new_player = result.data.get('new_player') if result.data else None
                    new_phase = result.data.get('new_phase') if result.data else None
                    
                    if old_player and new_player and new_phase:
                        old_name = old_player.name.split(' ')[0]  # Just first name
                        new_name = new_player.name.split(' ')[0]  # Just first name  
                        phase_name = new_phase.value if hasattr(new_phase, 'value') else str(new_phase)
                        description = f"play ({old_name}) → {phase_name} phase ({new_name})"
                    else:
                        description = "Turn ended"
                    
                    # Process end-of-turn effect expiration
                    self._process_turn_end_effects()
                else:
                    description = result_type.replace('_', ' ').title()
            
            # Special handling for specific action types to use structured event_data
            if hasattr(result, 'result_type') and result.result_type.value == "character_quested":
                character = result.data.get('character') if result.data else None
                lore = result.data.get('lore_gained', 0) if result.data else 0
                message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=GameEvent.LORE_GAINED,
                    event_data=create_event_data(
                        GameEvent.LORE_GAINED,
                        player=character.controller if character and hasattr(character, 'controller') else self.game_state.current_player,
                        amount=lore,
                        source=character
                    )
                )
            elif hasattr(result, 'result_type') and result.result_type.value == "ink_played":
                card = result.data.get('card') if result.data else None
                player = result.data.get('player') if result.data else self.game_state.current_player
                message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=GameEvent.INK_PLAYED,
                    event_data=create_event_data(
                        GameEvent.INK_PLAYED,
                        player=player,
                        card=card,
                        source=card
                    )
                )
            else:
                message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=f"action_{result.result_type.value if hasattr(result, 'result_type') else 'unknown'}",
                )
            self.message_queue.append(message)
            
            # Check for zone events (conditional effect activations) and queue them as separate messages
            if result.data and result.data.get('zone_events'):
                for zone_event in result.data['zone_events']:
                    event_type = zone_event.get('type', 'UNKNOWN_EVENT')
                    
                    if event_type == 'CONDITIONAL_EFFECT_APPLIED':
                        from .game_event_types import GameEventType
                        
                        zone_message = StepExecutedMessage(
                            type=MessageType.STEP_EXECUTED,
                            player=self.game_state.current_player,
                            step=GameEventType.CONDITIONAL_EFFECT_APPLIED,
                        )
                        # Store the raw event data
                        zone_message.event_data = zone_event
                        self.message_queue.append(zone_message)
                    
                    elif event_type == 'CONDITIONAL_EFFECT_REMOVED':
                        from .game_event_types import GameEventType
                        
                        zone_message = StepExecutedMessage(
                            type=MessageType.STEP_EXECUTED,
                            player=self.game_state.current_player,
                            step=GameEventType.CONDITIONAL_EFFECT_REMOVED,
                        )
                        # Store the raw event data
                        zone_message.event_data = zone_event
                        self.message_queue.append(zone_message)
    
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
        
        # After choice resolution, check if actions were queued and need to be processed
        if self.execution_engine.action_queue.has_pending_actions():
            # Process actions but DON'T apply effects yet - just prepare messages
            # Process ALL actions at once to ensure composite effects are fully split
            while self.execution_engine.action_queue.has_pending_actions():
                result = self.execution_engine.action_queue.process_next_action(apply_effect=False)
                if result:
                    # Create a message for this action (with deferred effect)
                    message = self._create_action_message(result)
                    if message:
                        self.message_queue.append(message)
    
    def _process_turn_end_effects(self) -> None:
        """Process effect expiration at end of turn."""
            
        # Get the player whose turn just ended (before the turn switch)
        # Note: The turn has already switched, so we need the previous player
        old_player_index = (self.game_state.current_player_index - 1) % len(self.game_state.players)
        ending_player = self.game_state.players[old_player_index]
        
        # Clear temporary bonuses from all characters belonging to the ending player
        for character in ending_player.characters_in_play:
            expired_effects = character.clear_temporary_bonuses(self.game_state)
            
            # Queue messages for each expired effect
            for effect in expired_effects:
                self.choice_engine.queue_choice_event_message(effect, self.message_queue)
    
    
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
    
    def _setup_step_listeners(self) -> None:
        """Set up listeners for step events."""
            
        def on_step_completed(step: GameStep):
            # Create snapshot after each completed step
            if step.status.value == "completed":
                self.snapshot_manager.create_snapshot(
                    step.step_id, 
                    self.game_state,
                    {"step_description": step.description}
                )
        
        self.step_engine.add_step_listener(on_step_completed)
    
    def _setup_input_handlers(self) -> None:
        """Set up input handlers for different step types."""
            
        def handle_choice_input(step: GameStep, input_data: Any) -> Any:
            if not step.player_input or step.player_input.input_type != StepType.CHOICE:
                raise ValueError("Step does not require choice input")
            
            if input_data not in step.player_input.options:
                raise ValueError(f"Invalid choice: {input_data}")
            
            return step.execute_fn(input_data)
        
        def handle_selection_input(step: GameStep, input_data: Any) -> Any:
            if not step.player_input or step.player_input.input_type != StepType.SELECTION:
                raise ValueError("Step does not require selection input")
            
            if not isinstance(input_data, list):
                input_data = [input_data]
            
            constraints = step.player_input.constraints
            min_count = constraints.get('min_count', 1)
            max_count = constraints.get('max_count', 1)
            
            if len(input_data) < min_count or len(input_data) > max_count:
                raise ValueError(f"Invalid selection count: {len(input_data)}")
            
            for item in input_data:
                if item not in step.player_input.options:
                    raise ValueError(f"Invalid selection: {item}")
            
            return step.execute_fn(input_data)
        
        def handle_confirmation_input(step: GameStep, input_data: Any) -> Any:
            if not step.player_input or step.player_input.input_type != StepType.CONFIRMATION:
                raise ValueError("Step does not require confirmation input")
            
            if not isinstance(input_data, bool):
                raise ValueError("Confirmation input must be boolean")
            
            return step.execute_fn(input_data)
        
        self.step_engine.register_input_handler(StepType.CHOICE, handle_choice_input)
        self.step_engine.register_input_handler(StepType.SELECTION, handle_selection_input)
        self.step_engine.register_input_handler(StepType.CONFIRMATION, handle_confirmation_input)
    
    # Conditional Effect Evaluation Methods
    def _evaluate_conditional_effects_after_move(self, move: GameMove) -> None:
        """Evaluate conditional effects after a move is processed - delegates to ExecutionEngine."""
        events = self.execution_engine._evaluate_conditional_effects_after_move(move)
        if events:
            self._queue_conditional_effect_events(events)
    
    def _evaluate_conditional_effects_after_step(self) -> None:
        """Evaluate conditional effects after a step is executed - delegates to ExecutionEngine."""
        events = self.execution_engine._evaluate_conditional_effects_after_step()
        if events:
            self._queue_conditional_effect_events(events)
    
    def _evaluate_conditional_effects_on_turn_change(self) -> None:
        """Evaluate conditional effects when turn changes - delegates to ExecutionEngine."""
        events = self.execution_engine._evaluate_conditional_effects_on_turn_change()
        if events:
            self._queue_conditional_effect_events(events)
    
    def _evaluate_conditional_effects_on_phase_change(self) -> None:
        """Evaluate conditional effects when phase changes - delegates to ExecutionEngine."""
        events = self.execution_engine._evaluate_conditional_effects_on_phase_change()
        if events:
            self._queue_conditional_effect_events(events)
    
    def _queue_conditional_effect_events(self, events: List[Dict]) -> None:
        """Queue conditional effect events as messages."""
            
        for event in events:
            event_type = event.get('type')
            
            if event_type == 'CONDITIONAL_EFFECT_APPLIED':
                from .game_event_types import GameEventType
                
                message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=GameEventType.CONDITIONAL_EFFECT_APPLIED,
                )
                # Store the raw event data for proper formatting
                message.event_data = event
                self.message_queue.append(message)
                return  # Return early to avoid duplicating the message
            
            elif event_type == 'CONDITIONAL_EFFECT_REMOVED':
                from .game_event_types import GameEventType
                
                message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=GameEventType.CONDITIONAL_EFFECT_REMOVED,
                )
                # Store the raw event data for proper formatting
                message.event_data = event
                self.message_queue.append(message)
                return  # Return early to avoid duplicating the message
            
            else:
                description = f"Conditional effect event: {event_type}"
                
                message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=f"conditional_effect_{event_type.lower()}",
                    description=description,
                    result="Applied" if "APPLIED" in event_type else "Removed"
                )
                self.message_queue.append(message)