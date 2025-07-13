"""Enhanced game engine with step-by-step progression support."""

from typing import Dict, Any, Tuple, Optional, List, Union
from ..models.game.game_state import GameState, GameAction, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card

from .game_engine import GameEngine
from .step_system import StepProgressionEngine, GameStep, StepType, ExecutionMode
from .input_system import InputManager, PlayerInput, AbilityInputBuilder
from .state_serializer import SnapshotManager
from .event_system import GameEventManager, GameEvent, EventContext


class SteppedGameEngine(GameEngine):
    """Game engine with step-by-step progression capabilities."""
    
    def __init__(self, game_state: GameState, execution_mode: ExecutionMode = ExecutionMode.PAUSE_ON_INPUT):
        super().__init__(game_state)
        
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
        if action == GameAction.PLAY_ACTION:
            return self._create_play_action_steps(parameters['card'])
        elif action == GameAction.PLAY_CHARACTER:
            return self._create_play_character_steps(parameters['card'])
        elif action == GameAction.CHALLENGE_CHARACTER:
            return self._create_challenge_steps(parameters['attacker'], parameters['defender'])
        elif action == GameAction.QUEST_CHARACTER:
            return self._create_quest_steps(parameters['character'])
        else:
            # For other actions, use immediate execution
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
        
        owner.characters_in_play.remove(character)
        owner.discard_pile.append(character)
        
        # Unregister abilities from banished character
        for ability in character.abilities:
            self.event_manager.unregister_triggered_ability(ability)
        
        # Trigger CHARACTER_BANISHED event
        banish_context = EventContext(
            event_type=GameEvent.CHARACTER_BANISHED,
            source=character,
            player=owner,
            game_state=self.game_state
        )
        self.event_manager.trigger_event(banish_context)
    
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