"""Action execution module for the game engine."""

from typing import Dict, Any, Tuple, Optional, List
from ..models.game.game_state import GameState, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card
from .move_validator import MoveValidator
from .event_system import GameEventManager, GameEvent, EventContext
from .damage_calculator import DamageCalculator, DamageType
from .action_result import ActionResult, ActionResultType
from .choice_system import GameChoiceManager
from ..utils.logging_config import get_game_logger

logger = get_game_logger(__name__)

class ActionExecutor:
    """Executes game actions and returns results."""
    
    def __init__(self, game_state: GameState, validator: MoveValidator, 
                 event_manager: GameEventManager, damage_calculator: DamageCalculator,
                 choice_manager: GameChoiceManager, action_queue: Any = None):
        self.game_state = game_state
        self.validator = validator
        self.event_manager = event_manager
        self.damage_calculator = damage_calculator
        self.choice_manager = choice_manager
        self.action_queue = action_queue
    
    
    def execute_action(self, action: str, parameters: Dict[str, Any]) -> ActionResult:
        """Execute a game action and return the result."""
        # Dispatch to appropriate action handler
        if action == "play_ink":
            return self._execute_play_ink(parameters)
        elif action == "play_character":
            return self._execute_play_character(parameters)
        elif action == "play_action":
            return self._execute_play_action(parameters)
        elif action == "play_item":
            return self._execute_play_item(parameters)
        elif action == "quest_character":
            return self._execute_quest_character(parameters)
        elif action == "challenge_character":
            return self._execute_challenge(parameters)
        elif action == "sing_song":
            return self._execute_sing_song(parameters)
        elif action == "progress":
            return self._execute_progress(parameters)
        elif action == "pass_turn":
            return self._execute_pass_turn(parameters)
        else:
            return ActionResult(
                success=False,
                action_type=action,
                result_type=ActionResultType.ACTION_FAILED,
                error_message=f"Unknown action: {action}"
            )
    
    def _execute_play_ink(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute playing a card as ink."""
        card = parameters.get('card')
        player = self.game_state.current_player
        
        # Validation already happened in _execute_action_direct
        
        # Use the player's play_ink method which handles everything correctly
        if not player.play_ink(card):
            return ActionResult(
                success=False,
                action_type="play_ink",
                result_type=ActionResultType.ACTION_FAILED,
                error_message="Failed to play ink"
            )
        
        
        # Mark that ink was played this turn
        self.game_state.ink_played_this_turn = True
        
        # Record the action
        self.game_state.record_action("play_ink")
        
        # Trigger INK_PLAYED event
        ink_context = EventContext(
            event_type=GameEvent.INK_PLAYED,
            player=player,
            game_state=self.game_state,
            source=card,
            additional_data={'card': card},
            action_queue=self.action_queue
        )
        self.event_manager.trigger_event(ink_context)
        
        return ActionResult(
            success=True,
            action_type="play_ink",
            result_type=ActionResultType.INK_PLAYED,
            data={'card': card, 'player': player}
        )
    
    def _execute_play_character(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute playing a character card."""
        card = parameters.get('card')
        player = self.game_state.current_player
        
        # Get the modified cost for the card
        modified_cost = self.game_state.get_modified_card_cost(card)
        
        # Validation already happened in _execute_action_direct
        
        # Use the player's play_character method which handles ink cost and placement
        if not player.play_character(card, modified_cost):
            return ActionResult(
                success=False,
                action_type="play_character",
                result_type=ActionResultType.ACTION_FAILED,
                error_message="Failed to play character"
            )
        
        # Set the turn played
        card.turn_played = self.game_state.turn_number
        
        # Register any conditional effects the card has
        self.game_state.register_card_conditional_effects(card)
        
        # Register any composable abilities the card has
        if hasattr(card, 'composable_abilities') and card.composable_abilities:
            for ability in card.composable_abilities:
                if hasattr(ability, 'register_with_event_manager'):
                    ability.register_with_event_manager(self.event_manager)
                    logger.debug("Registered ability {getattr(ability, 'name', 'unknown')} for events")
        
        # Trigger CHARACTER_ENTERS_PLAY event
        enter_play_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            player=player,
            game_state=self.game_state,
            source=card,
            additional_data={'character': card},
            action_queue=self.action_queue
        )
        
        # Check for choices in the event context
        if not hasattr(enter_play_context, 'additional_data'):
            enter_play_context.additional_data = {}
        enter_play_context.additional_data['choice_manager'] = self.choice_manager
        
        ability_messages = self.event_manager.trigger_event(enter_play_context)
        
        # Record the action
        self.game_state.record_action("play_character")
        
        return ActionResult(
            success=True,
            action_type="play_character",
            result_type=ActionResultType.CHARACTER_PLAYED,
            data={
                'card': card,
                'player': player,
                'ability_messages': ability_messages
            }
        )
    
    def _execute_play_action(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute playing an action card."""
        card = parameters.get('card')
        player = self.game_state.current_player
        
        # Validation already happened in _execute_action_direct
        
        # Check cost
        if not player.can_afford(card):
            return ActionResult(success=False, action_type="play_action", result_type=ActionResultType.ACTION_FAILED, error_message="Not enough ink to play this action")
        
        # Spend ink
        exerted_cards = player.spend_ink(card.cost)
        if len(exerted_cards) != card.cost:
            return ActionResult(success=False, action_type="play_action", result_type=ActionResultType.ACTION_FAILED, error_message="Failed to spend ink")
        
        # Remove from hand
        player.hand.remove(card)
        
        # Action effects would be resolved here based on the specific card
        # For now, we'll add it to discard
        player.discard.append(card)
        
        # Record the action
        self.game_state.record_action("play_action")
        
        return ActionResult(
            success=True,
            action_type="play_action",
            result_type=ActionResultType.ACTION_PLAYED,
            data={'card': card, 'player': player}
        )
    
    def _execute_play_item(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute playing an item card."""
        card = parameters.get('card')
        player = self.game_state.current_player
        
        # Validation already happened in _execute_action_direct
        
        # Check cost
        if not player.can_afford(card):
            return ActionResult(success=False, action_type="play_item", result_type=ActionResultType.ACTION_FAILED, error_message="Not enough ink to play this item")
        
        # Spend ink
        exerted_cards = player.spend_ink(card.cost)
        if len(exerted_cards) != card.cost:
            return ActionResult(success=False, action_type="play_item", result_type=ActionResultType.ACTION_FAILED, error_message="Failed to spend ink")
        
        # Remove from hand and add to play
        player.hand.remove(card)
        player.items_in_play.append(card)
        
        # Record the action
        self.game_state.record_action("play_item")
        
        return ActionResult(
            success=True,
            action_type="play_item",
            result_type=ActionResultType.ITEM_PLAYED,
            data={'card': card, 'player': player}
        )
    
    def _execute_quest_character(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute a character questing for lore."""
        character = parameters.get('character')
        player = self.game_state.current_player
        
        # Validation already happened in _execute_action_direct
        
        # Check if character has already acted this turn  
        if self.game_state.has_character_acted_this_turn(character.id):
            return ActionResult(success=False, action_type="quest_character", result_type=ActionResultType.ACTION_FAILED, error_message="This character has already acted this turn")
        
        # Exert the character
        character.exerted = True
        
        # Mark character as having acted this turn
        self.game_state.mark_character_acted(character.id)
        
        # Trigger CHARACTER_QUESTS event BEFORE gaining lore (in case abilities modify lore)
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=character,
            player=player,
            game_state=self.game_state,
            action_queue=self.action_queue
        )
        trigger_results = self.event_manager.trigger_event(event_context)
        
        # Calculate lore after abilities have had a chance to modify it
        # current_lore already includes all bonuses from abilities
        lore_gained = character.current_lore
        lore_before = player.lore
        
        # Gain lore
        player.lore += lore_gained
        
        # Record the action
        self.game_state.record_action("quest_character")
        
        return ActionResult(
            success=True,
            action_type="quest_character",
            result_type=ActionResultType.CHARACTER_QUESTED,
            data={
                'character': character,
                'player': player,
                'lore_gained': lore_gained,
                'lore_before': lore_before,
                'lore_after': player.lore,
                'triggered_abilities': trigger_results or []
            }
        )
    
    def _execute_challenge(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute a challenge between two characters."""
        attacker = parameters.get('attacker')
        defender = parameters.get('defender')
        current_player = self.game_state.current_player
        opponent = self.game_state.opponent
        
        # Validation already happened in _execute_action_direct
        
        # Check if attacker has already acted this turn
        if self.game_state.has_character_acted_this_turn(attacker.id):
            return ActionResult(success=False, action_type="challenge_character", result_type=ActionResultType.ACTION_FAILED, error_message="This character has already acted this turn")
        
        # Mark attacker as having acted this turn
        self.game_state.mark_character_acted(attacker.id)
        
        # Exert the attacker
        attacker.exerted = True
        
        # Store original stats
        original_attacker_strength = attacker.current_strength
        original_defender_strength = defender.current_strength
        
        # Trigger CHARACTER_CHALLENGES event (for abilities like Challenger)
        challenge_context = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            player=current_player,
            game_state=self.game_state,
            source=attacker,
            target=defender,
            additional_data={
                'attacker': attacker,
                'defender': defender
            },
            action_queue=self.action_queue
        )
        self.event_manager.trigger_event(challenge_context)
        
        # Calculate damage considering all modifiers
        damage_to_defender = self.damage_calculator.calculate_damage(
            attacker, defender, attacker.current_strength, DamageType.CHALLENGE
        )
        damage_to_attacker = self.damage_calculator.calculate_damage(
            defender, attacker, defender.current_strength, DamageType.CHALLENGE
        )
        
        # Apply damage
        defender.damage += damage_to_defender
        attacker.damage += damage_to_attacker
        
        
        # Handle CHARACTER_TAKES_DAMAGE events
        if damage_to_defender > 0:
            damage_context = EventContext(
                event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
                player=opponent,
                game_state=self.game_state,
                source=defender,
                additional_data={
                    'damage_amount': damage_to_defender,
                    'damage_source': attacker,
                    'damage_type': DamageType.CHALLENGE
                },
                action_queue=self.action_queue
            )
            self.event_manager.trigger_event(damage_context)
        
        if damage_to_attacker > 0:
            damage_context = EventContext(
                event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
                player=current_player,
                game_state=self.game_state,
                source=attacker,
                additional_data={
                    'damage_amount': damage_to_attacker,
                    'damage_source': defender,
                    'damage_type': DamageType.CHALLENGE
                },
                action_queue=self.action_queue
            )
            self.event_manager.trigger_event(damage_context)
        
        # Record the action
        self.game_state.record_action("challenge_character")
        
        result = ActionResult(
            success=True,
            action_type="challenge_character",
            result_type=ActionResultType.CHARACTER_CHALLENGED,
            data={
                'attacker': attacker,
                'defender': defender,
                'damage_to_attacker': damage_to_attacker,
                'damage_to_defender': damage_to_defender,
                'original_attacker_strength': original_attacker_strength,
                'original_defender_strength': original_defender_strength,
                'modified_attacker_strength': attacker.current_strength,
                'modified_defender_strength': defender.current_strength
            }
        )
        return result
    
    def _execute_sing_song(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute singing a song with a character."""
        character = parameters.get('character')
        song = parameters.get('song')
        player = self.game_state.current_player
        
        # Validation already happened in _execute_action_direct
        
        # Check if character has already acted this turn
        if self.game_state.has_character_acted_this_turn(character.id):
            return ActionResult(success=False, action_type="sing_song", result_type=ActionResultType.ACTION_FAILED, error_message="This character has already acted this turn")
        
        # Mark character as having acted this turn
        self.game_state.mark_character_acted(character.id)
        
        # Exert the character
        character.exerted = True
        
        # Remove song from hand
        player.hand.remove(song)
        
        # Song effects would be resolved here
        # For now, add to discard
        player.discard.append(song)
        
        # Record the action
        self.game_state.record_action("sing_song")
        
        return ActionResult(
            success=True,
            action_type="sing_song",
            result_type=ActionResultType.SONG_SUNG,
            data={
                'character': character,
                'song': song,
                'player': player
            }
        )
    
    def _execute_progress(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute progressing to the next phase or turn."""
        current_phase = self.game_state.current_phase
        
        # Execute phase-specific actions
        if current_phase == Phase.READY:
            # Execute ready step
            readied_items = self.game_state.ready_step()
            
            # Advance to SET phase
            self.game_state.advance_phase()
            
            # Trigger SET_PHASE event
            phase_context = EventContext(
                event_type=GameEvent.SET_PHASE,
                player=self.game_state.current_player,
                game_state=self.game_state,
                additional_data={'phase': 'set'},
                action_queue=self.action_queue
            )
            self.event_manager.trigger_event(phase_context)
            
            return ActionResult(
                success=True,
                action_type="progress",
                result_type=ActionResultType.PHASE_ADVANCED,
                data={
                    'previous_phase': Phase.READY,
                    'new_phase': self.game_state.current_phase,
                    'readied_items': readied_items
                }
            )
            
        elif current_phase == Phase.SET:
            # Execute set step
            self.game_state.set_step()
            
            # Advance to DRAW phase
            self.game_state.advance_phase()
            
            # Trigger DRAW_PHASE event
            phase_context = EventContext(
                event_type=GameEvent.DRAW_PHASE,
                player=self.game_state.current_player,
                game_state=self.game_state,
                additional_data={'phase': 'draw'},
                action_queue=self.action_queue
            )
            self.event_manager.trigger_event(phase_context)
            
            return ActionResult(
                success=True,
                action_type="progress",
                result_type=ActionResultType.PHASE_ADVANCED,
                data={
                    'previous_phase': Phase.SET,
                    'new_phase': self.game_state.current_phase
                }
            )
            
        elif current_phase == Phase.DRAW:
            # Execute draw step with events (similar to GameEngine.draw_card_with_events)
            current_player = self.game_state.current_player
            
            # Draw card (skip on first turn for first player)
            should_draw = not (self.game_state.turn_number == 1 and 
                              self.game_state.current_player_index == 0 and 
                              not self.game_state.first_turn_draw_skipped)
            
            draw_events = []
            if should_draw:
                card = current_player.draw_card()
                if card:
                    # Set the last event with structured data
                    source = "draw_phase"
                    
                    self.game_state.set_last_event(
                        'CARD_DRAWN',
                        player=current_player.name,
                        cards_drawn=[card],
                        count=1,
                        source=source,
                        hand_size_after=len(current_player.hand),
                        deck_size_after=len(current_player.deck)
                    )
                    
                    # Handle zone transition: card moved from deck to hand
                    zone_events = self.game_state.notify_card_zone_change(card, 'deck', 'hand')
                    if zone_events:
                        draw_events.extend(zone_events)
                    
                    # Trigger CARD_DRAWN event
                    draw_context = EventContext(
                        event_type=GameEvent.CARD_DRAWN,
                        source=card,
                        player=current_player,
                        game_state=self.game_state,
                        action_queue=self.action_queue
                    )
                    self.event_manager.trigger_event(draw_context)
                    
                    draw_events.append({
                        'type': 'card_drawn',  # Use lowercase for consistency with _queue_game_event_message
                        'player': current_player.name,
                        'cards_drawn': [card],  # Match expected format
                        'card': card,
                        'source': source
                    })
            elif self.game_state.turn_number == 1 and self.game_state.current_player_index == 0:
                self.game_state.first_turn_draw_skipped = True
            
            # Advance to PLAY phase
            self.game_state.advance_phase()
            
            # Trigger PLAY_PHASE event
            phase_context = EventContext(
                event_type=GameEvent.PLAY_PHASE,
                player=self.game_state.current_player,
                game_state=self.game_state,
                additional_data={'phase': 'play'},
                action_queue=self.action_queue
            )
            self.event_manager.trigger_event(phase_context)
            
            return ActionResult(
                success=True,
                action_type="progress",
                result_type=ActionResultType.PHASE_ADVANCED,
                data={
                    'previous_phase': Phase.DRAW,
                    'new_phase': self.game_state.current_phase,
                    'draw_events': draw_events
                }
            )
            
        elif current_phase == Phase.PLAY:
            # End the turn
            previous_player = self.game_state.current_player
            previous_turn = self.game_state.turn_number
            
            # Trigger TURN_ENDS event before changing turn
            turn_end_context = EventContext(
                event_type=GameEvent.TURN_ENDS,
                player=previous_player,
                game_state=self.game_state,
                additional_data={'turn_number': previous_turn},
                action_queue=self.action_queue
            )
            self.event_manager.trigger_event(turn_end_context)
            
            # Advance phase (which will call end_turn)
            self.game_state.advance_phase()
            
            # Trigger TURN_BEGINS event for new player
            new_player = self.game_state.current_player
            turn_begin_context = EventContext(
                event_type=GameEvent.TURN_BEGINS,
                player=new_player,
                game_state=self.game_state,
                additional_data={'turn_number': self.game_state.turn_number},
                action_queue=self.action_queue
            )
            self.event_manager.trigger_event(turn_begin_context)
            
            # Trigger READY_PHASE event for new turn
            ready_phase_context = EventContext(
                event_type=GameEvent.READY_PHASE,
                player=new_player,
                game_state=self.game_state,
                additional_data={'phase': 'ready'},
                action_queue=self.action_queue
            )
            self.event_manager.trigger_event(ready_phase_context)
            
            return ActionResult(
                success=True,
                action_type="progress",
                result_type=ActionResultType.TURN_ENDED,
                data={
                    'previous_phase': Phase.PLAY,
                    'new_phase': self.game_state.current_phase,
                    'previous_player': previous_player,
                    'new_player': new_player,
                    'previous_turn': previous_turn,
                    'new_turn': self.game_state.turn_number
                }
            )
        
        return ActionResult(
            success=False,
            action_type="progress",
            result_type=ActionResultType.ACTION_FAILED,
            error_message=f"Cannot progress from phase: {current_phase}"
        )
    
    def _execute_pass_turn(self, parameters: Dict[str, Any]) -> ActionResult:
        """Execute passing the turn to the opponent."""
        current_phase = self.game_state.current_phase
        
        # Can only pass during play phase
        if current_phase != Phase.PLAY:
            return ActionResult(
                success=False,
                action_type="pass_turn",
                result_type=ActionResultType.ACTION_FAILED,
                error_message="Can only pass turn during play phase"
            )
        
        # Record the pass action
        self.game_state.record_action("pass_turn")
        
        # Execute the same logic as progress during play phase
        previous_player = self.game_state.current_player
        previous_turn = self.game_state.turn_number
        
        # Trigger TURN_ENDS event
        turn_end_context = EventContext(
            event_type=GameEvent.TURN_ENDS,
            player=previous_player,
            game_state=self.game_state,
            additional_data={'turn_number': previous_turn},
            action_queue=self.action_queue
        )
        self.event_manager.trigger_event(turn_end_context)
        
        # End the turn
        self.game_state.end_turn()
        
        # Trigger TURN_BEGINS event for new player
        new_player = self.game_state.current_player
        turn_begin_context = EventContext(
            event_type=GameEvent.TURN_BEGINS,
            player=new_player,
            game_state=self.game_state,
            additional_data={'turn_number': self.game_state.turn_number},
            action_queue=self.action_queue
        )
        self.event_manager.trigger_event(turn_begin_context)
        
        return ActionResult(
            success=True,
            action_type="pass_turn",
            result_type=ActionResultType.TURN_ENDED,
            data={
                'previous_player': previous_player,
                'new_player': new_player,
                'previous_turn': previous_turn,
                'new_turn': self.game_state.turn_number,
                'action': 'pass_turn'
            }
        )