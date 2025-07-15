"""Enhanced game engine with step-by-step progression support."""

from typing import Dict, Any, Tuple, Optional, List, Union
from collections import deque
from ..models.game.game_state import GameState, GameAction, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card

from .game_engine import GameEngine
from .step_system import StepProgressionEngine, GameStep, StepType, ExecutionMode, StepStatus
from .input_system import InputManager, PlayerInput, AbilityInputBuilder
from .state_serializer import SnapshotManager
from .event_system import GameEventManager, GameEvent, EventContext
from .game_messages import (
    GameMessage, MessageType, ActionRequiredMessage, ChoiceRequiredMessage, 
    StepExecutedMessage, GameOverMessage, LegalAction
)
from .game_moves import GameMove, ActionMove, ChoiceMove, InkMove, PlayMove, QuestMove, ChallengeMove, SingMove, PassMove


class SteppedGameEngine(GameEngine):
    """Game engine with message-stream interface and step-by-step progression."""
    
    def __init__(self, game_state: GameState, execution_mode: ExecutionMode = ExecutionMode.PAUSE_ON_INPUT):
        super().__init__(game_state)
        
        # Message stream components
        self.message_queue = deque()
        self.current_steps = deque()
        self.waiting_for_input = False
        self.current_choice = None
        
        # Step-by-step components
        self.step_engine = StepProgressionEngine(execution_mode)
        self.input_manager = InputManager()
        self.snapshot_manager = SnapshotManager()
        
        # Set up integration
        self.event_manager.set_step_engine(self.step_engine)
        self._setup_step_listeners()
        self._setup_input_handlers()
        
        # Track current action being executed
        self.current_action_steps: List[GameStep] = []
    
    def next_message(self, move: Optional[GameMove] = None) -> GameMessage:
        """Get the next message in the game progression."""
        
        # Process move if provided
        if move and self.waiting_for_input:
            self._process_move(move)
            self.waiting_for_input = False
        
        # Return queued messages first
        if self.message_queue:
            return self.message_queue.popleft()
        
        # Execute next step if available
        if self.current_steps:
            return self._execute_next_step()
        
        # Check for choices
        if self.current_choice or self.is_paused_for_choice():
            if not self.current_choice:
                self.current_choice = self.get_current_choice()
            
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
            result, winner, reason = self.game_state.get_game_result()
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
    
    def _process_move(self, move: GameMove) -> None:
        """Process a player move."""
        if isinstance(move, ActionMove):
            # Break action into steps and queue them
            steps = self._create_action_steps(move.action, move.parameters)
            if steps:
                self.current_steps.extend(steps)
            else:
                # Fall back to direct execution if no steps created
                result = self.execute_action(move.action, move.parameters)
                self._queue_result_message(result)
            
        elif isinstance(move, (InkMove, PlayMove, QuestMove, ChallengeMove, SingMove)):
            # Convert specific moves to action moves
            action_move = self._convert_to_action_move(move)
            steps = self._create_action_steps(action_move.action, action_move.parameters)
            if steps:
                self.current_steps.extend(steps)
            else:
                # Fall back to direct execution if no steps created
                result = self.execute_action(action_move.action, action_move.parameters)
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
                        step_id=f"character_readied",
                        description=readied_item,
                        result="Readied"
                    )
                    self.message_queue.append(ready_message)
                # Clear the flag
                delattr(self.game_state, '_needs_ready_step')
            
            result = self.execute_action(GameAction.PROGRESS, {})
            self._queue_result_message(result)
            
        elif isinstance(move, ChoiceMove):
            # Resolve choice and continue
            self._resolve_choice(move.choice_id, move.option)
            self.current_choice = None
    
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
                    char_name = character.name if character and hasattr(character, 'name') else 'character'
                    lore = result.data.get('lore_gained', 0) if result.data else 0
                    lore_after = result.data.get('lore_after', 0) if result.data else 0
                    description = f"{char_name} quested for {lore} lore → {lore_after} total"
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
                elif result_type == "turn_ended":
                    description = "Turn ended"
                else:
                    description = result_type.replace('_', ' ').title()
            
            message = StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step_id=f"action_{result.result_type.value if hasattr(result, 'result_type') else 'unknown'}",
                description=description,
                result="Completed"
            )
            self.message_queue.append(message)
            
            # Check for triggered abilities and queue them as separate messages
            if result.data and result.data.get('triggered_abilities'):
                for ability in result.data['triggered_abilities']:
                    ability_message = StepExecutedMessage(
                        type=MessageType.STEP_EXECUTED,
                        player=self.game_state.current_player,
                        step_id=f"ability_triggered_{ability}",
                        description=f"Ability triggered: {ability}",
                        result="Triggered"
                    )
                    self.message_queue.append(ability_message)
            
            # Don't execute ready step here - it should happen during PROGRESS in ready phase
            
            # Check for readied items and queue them as separate messages
            if result.data and result.data.get('readied_items'):
                for readied_item in result.data['readied_items']:
                    ready_message = StepExecutedMessage(
                        type=MessageType.STEP_EXECUTED,
                        player=self.game_state.current_player,
                        step_id=f"character_readied",
                        description=readied_item,
                        result="Readied"
                    )
                    self.message_queue.append(ready_message)
            
            # Check for draw events and queue them as separate messages
            if result.data and result.data.get('draw_events'):
                for draw_event in result.data['draw_events']:
                    draw_message = StepExecutedMessage(
                        type=MessageType.STEP_EXECUTED,
                        player=self.game_state.current_player,
                        step_id=f"card_drawn",
                        description=draw_event,
                        result="Drew"
                    )
                    self.message_queue.append(draw_message)
            
            # Check for banished characters and queue them as separate messages
            if result.data and result.data.get('banished_characters'):
                for banished_character in result.data['banished_characters']:
                    banish_message = StepExecutedMessage(
                        type=MessageType.STEP_EXECUTED,
                        player=self.game_state.current_player,
                        step_id=f"character_banished",
                        description=f"{banished_character} was banished",
                        result="Banished"
                    )
                    self.message_queue.append(banish_message)
    
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
    
    def _create_pass_steps(self) -> List[GameStep]:
        """Create steps for passing/progressing."""
        steps = []
        
        def progress_step():
            # Use the existing progress logic
            result = self.execute_action(GameAction.PROGRESS, {})
            return f"Progressed from {self.game_state.current_phase} phase"
        
        steps.append(GameStep(
            step_id=f"progress_{self.game_state.current_phase}",
            step_type=StepType.AUTOMATIC,
            description=f"Progress from {self.game_state.current_phase} phase",
            execute_fn=progress_step
        ))
        
        return steps
    
    def _execute_next_step(self) -> StepExecutedMessage:
        """Execute the next step and return message."""
        step = self.current_steps.popleft()
        
        try:
            result = step.execute_fn()
            step.status = StepStatus.COMPLETED
            step.result = result
            
            # Check if step triggered a choice
            if self.is_paused_for_choice():
                self.current_choice = self.get_current_choice()
            
            return StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step_id=step.step_id,
                description=step.description,
                result=str(result) if result else "Completed"
            )
            
        except Exception as e:
            step.status = StepStatus.CANCELLED
            step.error = str(e)
            return StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step_id=step.step_id,
                description=step.description,
                result=f"Error: {str(e)}"
            )
    
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
        
        success = self.provide_player_choice(choice_id, option)
        if not success:
            raise ValueError(f"Failed to resolve choice {choice_id} with option {option}")
        
        # Check for multiple events that occurred during choice resolution
        # First check if there are collected choice events
        if hasattr(self.game_state, 'choice_events') and self.game_state.choice_events:
            # Process all collected events
            for event in self.game_state.choice_events:
                self._queue_choice_event_message(event)
            # Clear the events after processing
            self.game_state.choice_events.clear()
        else:
            # Fallback to single event detection
            last_event_after = getattr(self.game_state, 'last_event', None)
            timestamp_after = last_event_after.get('timestamp', -1) if last_event_after else -1
            if (last_event_after and timestamp_after > timestamp_before):
                self._queue_choice_event_message(last_event_after)
    
    def _queue_choice_event_message(self, event: dict) -> None:
        """Queue a message for a choice-triggered event."""
        event_type = event.get('type')
        player_name = event.get('player', 'Unknown')
        
        if event_type == 'CARD_DRAWN':
            # Queue draw event messages for choice-triggered draws
            cards_drawn = event.get('cards_drawn', [])
            for card in cards_drawn:
                card_name = card.name if hasattr(card, 'name') else 'Unknown Card'
                draw_message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step_id=f"card_drawn",
                    description=f"{player_name} drew {card_name}",
                    result="Drew"
                )
                self.message_queue.append(draw_message)
        
        elif event_type == 'CARD_DISCARDED':
            # Queue discard event messages for choice-triggered discards
            card_name = event.get('card_name', 'Unknown Card')
            discard_message = StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step_id=f"card_discarded",
                description=f"{player_name} discarded {card_name}",
                result="Discarded"
            )
            self.message_queue.append(discard_message)
        
        elif event_type == 'LORE_GAINED':
            # Queue lore gain event messages for choice-triggered lore gains
            lore_amount = event.get('lore_amount', 0)
            lore_after = event.get('lore_after', 0)
            lore_message = StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step_id=f"lore_gained",
                description=f"{player_name} gained {lore_amount} lore → {lore_after} total",
                result="Gained"
            )
            self.message_queue.append(lore_message)
    
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
    
    def execute_action_stepped(self, action: GameAction, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a game action using step-by-step progression."""
        # Validate action first
        is_valid, message = self.validator.validate_action(action, parameters)
        if not is_valid:
            return False, message
        
        # Create steps for the action
        action_steps = self._create_action_steps(action, parameters)
        if not action_steps:
            # Fall back to immediate execution for actions without steps
            return self.execute_action(action, parameters)
        
        # Queue the steps
        self.current_action_steps = action_steps
        self.step_engine.queue_steps(action_steps)
        
        # Start execution
        if self.step_engine.step_queue.execution_mode == ExecutionMode.PAUSE_ON_INPUT:
            # Auto-advance until input needed
            executed_steps = self.step_engine.continue_execution()
            return True, f"Started {action.value} execution ({len(executed_steps)} steps completed)"
        else:
            # Manual mode - execute first step only
            first_step = self.step_engine.execute_next_step()
            if first_step:
                return True, f"Started {action.value} execution (step: {first_step.description})"
            else:
                return False, "Failed to start action execution"
    
    def _create_action_steps(self, action: GameAction, parameters: Dict[str, Any]) -> List[GameStep]:
        """Create steps for a game action."""
        # For now, disable step creation to use clean direct execution
        # This ensures all actions use the new clean messaging format
        return []
    
    def _create_play_action_steps(self, action_card: ActionCard) -> List[GameStep]:
        """Create steps for playing an action card."""
        steps = []
        
        # Step 1: Pay cost and move card
        def pay_cost_step():
            current_player = self.game_state.current_player
            if current_player.play_action(action_card, action_card.cost):
                self.game_state.actions_this_turn.append(GameAction.PLAY_ACTION)
                return f"Paid {action_card.cost} ink and played {action_card.name}"
            else:
                raise Exception("Failed to pay cost")
        
        steps.append(GameStep(
            step_id=f"play_action_{action_card.name}_pay_cost",
            step_type=StepType.AUTOMATIC,
            description=f"Pay {action_card.cost} ink to play {action_card.name}",
            execute_fn=pay_cost_step
        ))
        
        # Step 2: Execute action effects (if any)
        if hasattr(action_card, 'effects') and action_card.effects:
            effect_steps = self._create_ability_effect_steps(action_card, action_card.effects)
            steps.extend(effect_steps)
        
        # Step 3: Trigger events
        def trigger_events_step():
            # Trigger ACTION_PLAYED event
            action_context = EventContext(
                event_type=GameEvent.ACTION_PLAYED,
                source=action_card,
                player=self.game_state.current_player,
                game_state=self.game_state
            )
            results = self.event_manager.trigger_event(action_context)
            
            # If it's a song, also trigger SONG_PLAYED event
            if action_card.is_song:
                song_context = EventContext(
                    event_type=GameEvent.SONG_PLAYED,
                    source=action_card,
                    player=self.game_state.current_player,
                    game_state=self.game_state
                )
                song_results = self.event_manager.trigger_event(song_context)
                results.extend(song_results)
            
            return f"Triggered events: {'; '.join(results)}" if results else "No events triggered"
        
        steps.append(GameStep(
            step_id=f"play_action_{action_card.name}_events",
            step_type=StepType.AUTOMATIC,
            description=f"Trigger events for {action_card.name}",
            execute_fn=trigger_events_step
        ))
        
        return steps
    
    def _create_play_character_steps(self, character: CharacterCard) -> List[GameStep]:
        """Create steps for playing a character card."""
        steps = []
        
        # Step 1: Pay cost and put character in play
        def play_character_step():
            current_player = self.game_state.current_player
            if current_player.play_character(character, character.cost):
                character.turn_played = self.game_state.turn_number
                self.game_state.actions_this_turn.append(GameAction.PLAY_CHARACTER)
                return f"Played {character.name} and paid {character.cost} ink"
            else:
                raise Exception("Failed to play character")
        
        steps.append(GameStep(
            step_id=f"play_character_{character.name}_play",
            step_type=StepType.AUTOMATIC,
            description=f"Play {character.name} for {character.cost} ink",
            execute_fn=play_character_step
        ))
        
        # Step 2: Register abilities and trigger enter events
        def trigger_enter_events_step():
            # Register triggered abilities
            for ability in character.abilities:
                if hasattr(ability, 'get_trigger_events') and ability.get_trigger_events():
                    self.event_manager.register_triggered_ability(ability)
            
            # Trigger CHARACTER_ENTERS_PLAY event
            enters_context = EventContext(
                event_type=GameEvent.CHARACTER_ENTERS_PLAY,
                source=character,
                player=self.game_state.current_player,
                game_state=self.game_state
            )
            results = self.event_manager.trigger_event(enters_context)
            
            # Trigger CHARACTER_PLAYED event
            played_context = EventContext(
                event_type=GameEvent.CHARACTER_PLAYED,
                source=character,
                player=self.game_state.current_player,
                game_state=self.game_state
            )
            played_results = self.event_manager.trigger_event(played_context)
            results.extend(played_results)
            
            return f"Triggered events: {'; '.join(results)}" if results else "No events triggered"
        
        steps.append(GameStep(
            step_id=f"play_character_{character.name}_events",
            step_type=StepType.AUTOMATIC,
            description=f"Register abilities and trigger enter events for {character.name}",
            execute_fn=trigger_enter_events_step
        ))
        
        return steps
    
    def _create_challenge_steps(self, attacker: CharacterCard, defender: CharacterCard) -> List[GameStep]:
        """Create steps for a challenge between characters."""
        steps = []
        
        # Step 1: Exert attacker and trigger challenge event
        def start_challenge_step():
            attacker.exert()
            
            # Trigger CHARACTER_CHALLENGES event
            event_context = EventContext(
                event_type=GameEvent.CHARACTER_CHALLENGES,
                source=attacker,
                target=defender,
                player=self.game_state.current_player,
                game_state=self.game_state
            )
            results = self.event_manager.trigger_event(event_context)
            
            return f"{attacker.name} challenges {defender.name}. Events: {'; '.join(results)}"
        
        steps.append(GameStep(
            step_id=f"challenge_{attacker.name}_vs_{defender.name}_start",
            step_type=StepType.AUTOMATIC,
            description=f"{attacker.name} challenges {defender.name}",
            execute_fn=start_challenge_step
        ))
        
        # Step 2: Deal damage
        def deal_damage_step():
            from .damage_calculator import DamageType
            
            # Deal damage using the damage calculation system
            attacker_damage_taken = attacker.deal_damage(
                defender.current_strength,
                source=defender,
                damage_calculator=self.damage_calculator,
                damage_type=DamageType.CHALLENGE
            )
            
            defender_damage_taken = defender.deal_damage(
                attacker.current_strength,
                source=attacker,
                damage_calculator=self.damage_calculator,
                damage_type=DamageType.CHALLENGE
            )
            
            # Trigger damage events
            damage_results = []
            if defender_damage_taken > 0:
                damage_context = EventContext(
                    event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
                    source=attacker,
                    target=defender,
                    player=self.game_state.current_player,
                    game_state=self.game_state,
                    additional_data={
                        'damage': defender_damage_taken,
                        'base_damage': attacker.current_strength,
                        'damage_type': DamageType.CHALLENGE
                    }
                )
                damage_results.extend(self.event_manager.trigger_event(damage_context))
            
            if attacker_damage_taken > 0:
                damage_context = EventContext(
                    event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
                    source=defender,
                    target=attacker,
                    player=self.game_state.opponent,
                    game_state=self.game_state,
                    additional_data={
                        'damage': attacker_damage_taken,
                        'base_damage': defender.current_strength,
                        'damage_type': DamageType.CHALLENGE
                    }
                )
                damage_results.extend(self.event_manager.trigger_event(damage_context))
            
            return f"Damage dealt - {attacker.name}: {attacker_damage_taken}, {defender.name}: {defender_damage_taken}"
        
        steps.append(GameStep(
            step_id=f"challenge_{attacker.name}_vs_{defender.name}_damage",
            step_type=StepType.AUTOMATIC,
            description="Deal challenge damage",
            execute_fn=deal_damage_step
        ))
        
        # Step 3: Remove banished characters
        def cleanup_banished_step():
            banished_messages = []
            
            if not attacker.is_alive:
                self._banish_character(attacker, self.game_state.current_player)
                banished_messages.append(f"{attacker.name} was banished")
            
            if not defender.is_alive:
                self._banish_character(defender, self.game_state.opponent)
                banished_messages.append(f"{defender.name} was banished")
            
            self.game_state.actions_this_turn.append(GameAction.CHALLENGE_CHARACTER)
            
            return "; ".join(banished_messages) if banished_messages else "No characters banished"
        
        steps.append(GameStep(
            step_id=f"challenge_{attacker.name}_vs_{defender.name}_cleanup",
            step_type=StepType.AUTOMATIC,
            description="Remove banished characters",
            execute_fn=cleanup_banished_step
        ))
        
        return steps
    
    def _create_quest_steps(self, character: CharacterCard) -> List[GameStep]:
        """Create steps for questing with a character."""
        steps = []
        
        # Step 1: Exert character and trigger quest event
        def start_quest_step():
            character.exert()
            
            # Trigger CHARACTER_QUESTS event BEFORE gaining lore
            event_context = EventContext(
                event_type=GameEvent.CHARACTER_QUESTS,
                source=character,
                player=self.game_state.current_player,
                game_state=self.game_state
            )
            results = self.event_manager.trigger_event(event_context)
            
            return f"{character.name} quests. Events: {'; '.join(results)}"
        
        steps.append(GameStep(
            step_id=f"quest_{character.name}_start",
            step_type=StepType.AUTOMATIC,
            description=f"{character.name} begins questing",
            execute_fn=start_quest_step
        ))
        
        # Step 2: Calculate and gain lore
        def gain_lore_step():
            # Calculate lore after abilities have had a chance to modify it
            lore_gained = getattr(character, 'temporary_lore_bonus', 0) + character.current_lore
            current_player = self.game_state.current_player
            current_player.gain_lore(lore_gained)
            
            # Trigger LORE_GAINED event
            lore_context = EventContext(
                event_type=GameEvent.LORE_GAINED,
                source=character,
                player=current_player,
                game_state=self.game_state,
                additional_data={'lore_amount': lore_gained}
            )
            lore_results = self.event_manager.trigger_event(lore_context)
            
            # Clear temporary lore bonus
            if hasattr(character, 'temporary_lore_bonus'):
                character.temporary_lore_bonus = 0
            
            self.game_state.actions_this_turn.append(GameAction.QUEST_CHARACTER)
            
            return f"Gained {lore_gained} lore. Events: {'; '.join(lore_results)}"
        
        steps.append(GameStep(
            step_id=f"quest_{character.name}_lore",
            step_type=StepType.AUTOMATIC,
            description=f"Gain lore from {character.name}",
            execute_fn=gain_lore_step
        ))
        
        return steps
    
    def _create_ability_effect_steps(self, source_card: Card, effects: List[Any]) -> List[GameStep]:
        """Create steps for ability effects (placeholder for complex abilities)."""
        # This would be expanded to handle specific ability effects
        # For now, return empty list
        return []
    
    def _banish_character(self, character: CharacterCard, owner) -> None:
        """Helper method to banish a character."""
        # Trigger CHARACTER_LEAVES_PLAY event
        leaves_context = EventContext(
            event_type=GameEvent.CHARACTER_LEAVES_PLAY,
            source=character,
            player=owner,
            game_state=self.game_state,
            additional_data={'reason': 'banished'}
        )
        self.event_manager.trigger_event(leaves_context)
        
        # Trigger CHARACTER_BANISHED event BEFORE unregistering abilities
        banish_context = EventContext(
            event_type=GameEvent.CHARACTER_BANISHED,
            source=character,
            player=owner,
            game_state=self.game_state
        )
        self.event_manager.trigger_event(banish_context)
        
        # Now remove from play and unregister abilities
        owner.characters_in_play.remove(character)
        owner.discard_pile.append(character)
        
        # Unregister composable abilities from banished character
        character.unregister_composable_abilities(self.event_manager)
    
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