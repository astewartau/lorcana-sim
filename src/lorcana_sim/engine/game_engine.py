"""Game engine for executing actions and managing state transitions."""

from typing import Dict, Any, Tuple, Optional
from ..models.game.game_state import GameState, GameAction, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card
from .move_validator import MoveValidator
from .event_system import GameEventManager, GameEvent, EventContext
from .damage_calculator import DamageCalculator, DamageType


class GameEngine:
    """Executes game actions and manages state transitions."""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.validator = MoveValidator(game_state)
        self.event_manager = GameEventManager(game_state)
        self.damage_calculator = DamageCalculator(game_state)
        # Register all triggered abilities from characters currently in play
        self.event_manager.rebuild_listeners()
    
    def draw_card_with_events(self, player):
        """Draw a card for a player and trigger CARD_DRAWN event."""
        card = player.draw_card()
        if card:
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
        """Execute the set step (draw card with events)."""
        current_player = self.game_state.current_player
        
        # Draw card (skip on first turn for first player)
        should_draw = not (self.game_state.turn_number == 1 and 
                          self.game_state.current_player_index == 0 and 
                          not self.game_state.first_turn_draw_skipped)
        
        if should_draw:
            self.draw_card_with_events(current_player)
        elif self.game_state.turn_number == 1 and self.game_state.current_player_index == 0:
            self.game_state.first_turn_draw_skipped = True
    
    def execute_action(self, action: GameAction, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a game action and update state."""
        # Validate action first
        is_valid, message = self.validator.validate_action(action, parameters)
        if not is_valid:
            return False, message
        
        # Execute the action
        try:
            if action == GameAction.PLAY_INK:
                return self._execute_play_ink(parameters['card'])
            elif action == GameAction.PLAY_CHARACTER:
                return self._execute_play_character(parameters['card'])
            elif action == GameAction.PLAY_ACTION:
                return self._execute_play_action(parameters['card'])
            elif action == GameAction.PLAY_ITEM:
                return self._execute_play_item(parameters['card'])
            elif action == GameAction.QUEST_CHARACTER:
                return self._execute_quest_character(parameters['character'])
            elif action == GameAction.CHALLENGE_CHARACTER:
                return self._execute_challenge(parameters['attacker'], parameters['defender'])
            elif action == GameAction.SING_SONG:
                return self._execute_sing_song(parameters['song'], parameters['singer'])
            elif action == GameAction.PASS_TURN:
                return self._execute_pass_turn()
            else:
                return False, f"Unknown action: {action}"
        
        except Exception as e:
            return False, f"Error executing action: {str(e)}"
    
    def _execute_play_ink(self, card: Card) -> Tuple[bool, str]:
        """Execute playing a card as ink."""
        current_player = self.game_state.current_player
        
        if current_player.play_ink(card):
            self.game_state.ink_played_this_turn = True
            self.game_state.actions_this_turn.append(GameAction.PLAY_INK)
            
            # Trigger INK_PLAYED event
            ink_context = EventContext(
                event_type=GameEvent.INK_PLAYED,
                source=card,
                player=current_player,
                game_state=self.game_state
            )
            trigger_results = self.event_manager.trigger_event(ink_context)
            
            result_message = f"Played {card.name} as ink"
            if trigger_results:
                result_message += f" (Triggered: {'; '.join(trigger_results)})"
            
            return True, result_message
        
        return False, "Failed to play ink"
    
    def _execute_play_character(self, character: CharacterCard) -> Tuple[bool, str]:
        """Execute playing a character card."""
        current_player = self.game_state.current_player
        
        if current_player.play_character(character, character.cost):
            self.game_state.actions_this_turn.append(GameAction.PLAY_CHARACTER)
            
            # Set turn_played for ink drying system
            character.turn_played = self.game_state.turn_number
            
            # Register any triggered abilities this character has
            for ability in character.abilities:
                if hasattr(ability, 'get_trigger_events') and ability.get_trigger_events():
                    self.event_manager.register_triggered_ability(ability)
            
            # Trigger CHARACTER_ENTERS_PLAY event (more general)
            enters_context = EventContext(
                event_type=GameEvent.CHARACTER_ENTERS_PLAY,
                source=character,
                player=current_player,
                game_state=self.game_state
            )
            trigger_results = self.event_manager.trigger_event(enters_context)
            
            # Trigger CHARACTER_PLAYED event (specific to playing from hand)
            played_context = EventContext(
                event_type=GameEvent.CHARACTER_PLAYED,
                source=character,
                player=current_player,
                game_state=self.game_state
            )
            played_results = self.event_manager.trigger_event(played_context)
            if played_results:
                trigger_results.extend(played_results)
            
            result_message = f"Played character {character.name}"
            if trigger_results:
                result_message += f" (Triggered: {'; '.join(trigger_results)})"
            
            return True, result_message
        
        return False, "Failed to play character"
    
    def _execute_play_action(self, action: ActionCard) -> Tuple[bool, str]:
        """Execute playing an action card."""
        current_player = self.game_state.current_player
        
        if current_player.play_action(action, action.cost):
            self.game_state.actions_this_turn.append(GameAction.PLAY_ACTION)
            
            # Trigger ACTION_PLAYED event
            action_context = EventContext(
                event_type=GameEvent.ACTION_PLAYED,
                source=action,
                player=current_player,
                game_state=self.game_state
            )
            trigger_results = self.event_manager.trigger_event(action_context)
            
            # If it's a song, also trigger SONG_PLAYED event
            if action.is_song:
                song_context = EventContext(
                    event_type=GameEvent.SONG_PLAYED,
                    source=action,
                    player=current_player,
                    game_state=self.game_state
                )
                song_results = self.event_manager.trigger_event(song_context)
                if song_results:
                    trigger_results.extend(song_results)
            
            # TODO: Execute action's effects
            result_message = f"Played action {action.name}"
            if trigger_results:
                result_message += f" (Triggered: {'; '.join(trigger_results)})"
            
            return True, result_message
        
        return False, "Failed to play action"
    
    def _execute_play_item(self, item: ItemCard) -> Tuple[bool, str]:
        """Execute playing an item card."""
        current_player = self.game_state.current_player
        
        if current_player.play_item(item, item.cost):
            self.game_state.actions_this_turn.append(GameAction.PLAY_ITEM)
            
            # Trigger ITEM_PLAYED event
            item_context = EventContext(
                event_type=GameEvent.ITEM_PLAYED,
                source=item,
                player=current_player,
                game_state=self.game_state
            )
            trigger_results = self.event_manager.trigger_event(item_context)
            
            result_message = f"Played item {item.name}"
            if trigger_results:
                result_message += f" (Triggered: {'; '.join(trigger_results)})"
            
            return True, result_message
        
        return False, "Failed to play item"
    
    def _execute_quest_character(self, character: CharacterCard) -> Tuple[bool, str]:
        """Execute questing with a character."""
        if character.can_quest(self.game_state.turn_number):
            character.exert()
            current_player = self.game_state.current_player
            
            # Trigger CHARACTER_QUESTS event BEFORE gaining lore (in case abilities modify lore)
            event_context = EventContext(
                event_type=GameEvent.CHARACTER_QUESTS,
                source=character,
                player=current_player,
                game_state=self.game_state
            )
            trigger_results = self.event_manager.trigger_event(event_context)
            
            # Calculate lore after abilities have had a chance to modify it
            lore_gained = getattr(character, 'temporary_lore_bonus', 0) + character.current_lore
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
            if lore_results:
                trigger_results.extend(lore_results)
            
            # Clear temporary lore bonus
            if hasattr(character, 'temporary_lore_bonus'):
                character.temporary_lore_bonus = 0
            
            self.game_state.actions_this_turn.append(GameAction.QUEST_CHARACTER)
            
            result_message = f"{character.name} quested for {lore_gained} lore"
            if trigger_results:
                result_message += f" (Triggered: {'; '.join(trigger_results)})"
            
            return True, result_message
        
        return False, "Character cannot quest"
    
    def _execute_challenge(self, attacker: CharacterCard, defender: CharacterCard) -> Tuple[bool, str]:
        """Execute a challenge between characters."""
        if not self.validator.can_challenge(attacker, defender):
            return False, "Invalid challenge"
        
        # Exert attacker
        attacker.exert()
        
        # Trigger CHARACTER_CHALLENGES event
        current_player = self.game_state.current_player
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=attacker,
            target=defender,
            player=current_player,
            game_state=self.game_state
        )
        trigger_results = self.event_manager.trigger_event(event_context)
        
        # Deal damage using the new damage calculation system
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
        
        # Trigger damage events with actual damage taken
        if defender_damage_taken > 0:
            damage_context = EventContext(
                event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
                source=attacker,
                target=defender,
                player=current_player,
                game_state=self.game_state,
                additional_data={
                    'damage': defender_damage_taken,
                    'base_damage': attacker.current_strength,
                    'damage_type': DamageType.CHALLENGE
                }
            )
            self.event_manager.trigger_event(damage_context)
        
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
            self.event_manager.trigger_event(damage_context)
        
        # Remove banished characters and trigger banishment events
        opponent = self.game_state.opponent
        result_messages = []
        
        if not attacker.is_alive:
            # Trigger CHARACTER_LEAVES_PLAY event (more general)
            leaves_context = EventContext(
                event_type=GameEvent.CHARACTER_LEAVES_PLAY,
                source=attacker,
                player=current_player,
                game_state=self.game_state,
                additional_data={'reason': 'banished'}
            )
            self.event_manager.trigger_event(leaves_context)
            
            current_player.characters_in_play.remove(attacker)
            current_player.discard_pile.append(attacker)
            # Unregister abilities from banished character
            for ability in attacker.abilities:
                self.event_manager.unregister_triggered_ability(ability)
            
            # Trigger CHARACTER_BANISHED event (specific to banishment)
            banish_context = EventContext(
                event_type=GameEvent.CHARACTER_BANISHED,
                source=attacker,
                player=current_player,
                game_state=self.game_state
            )
            self.event_manager.trigger_event(banish_context)
            result_messages.append(f"{attacker.name} was banished")
        
        if not defender.is_alive:
            # Trigger CHARACTER_LEAVES_PLAY event (more general)
            leaves_context = EventContext(
                event_type=GameEvent.CHARACTER_LEAVES_PLAY,
                source=defender,
                player=opponent,
                game_state=self.game_state,
                additional_data={'reason': 'banished'}
            )
            self.event_manager.trigger_event(leaves_context)
            
            opponent.characters_in_play.remove(defender)
            opponent.discard_pile.append(defender)
            # Unregister abilities from banished character
            for ability in defender.abilities:
                self.event_manager.unregister_triggered_ability(ability)
            
            # Trigger CHARACTER_BANISHED event (specific to banishment)
            banish_context = EventContext(
                event_type=GameEvent.CHARACTER_BANISHED,
                source=defender,
                player=opponent,
                game_state=self.game_state
            )
            self.event_manager.trigger_event(banish_context)
            result_messages.append(f"{defender.name} was banished")
        
        self.game_state.actions_this_turn.append(GameAction.CHALLENGE_CHARACTER)
        
        base_message = f"{attacker.name} challenged {defender.name}"
        if result_messages:
            base_message += f" ({'; '.join(result_messages)})"
        if trigger_results:
            base_message += f" (Triggered: {'; '.join(trigger_results)})"
        
        return True, base_message
    
    def _execute_sing_song(self, song: ActionCard, singer: CharacterCard) -> Tuple[bool, str]:
        """Execute singing a song."""
        current_player = self.game_state.current_player
        
        # Remove song from hand, add to discard
        if song in current_player.hand:
            current_player.hand.remove(song)
            current_player.discard_pile.append(song)
            
            # Exert the singer
            singer.exert()
            
            # Trigger SONG_SUNG event
            event_context = EventContext(
                event_type=GameEvent.SONG_SUNG,
                source=singer,
                target=song,
                player=current_player,
                game_state=self.game_state
            )
            trigger_results = self.event_manager.trigger_event(event_context)
            
            self.game_state.actions_this_turn.append(GameAction.SING_SONG)
            
            result_message = f"{singer.name} sang {song.name}"
            if trigger_results:
                result_message += f" (Triggered: {'; '.join(trigger_results)})"
            
            return True, result_message
        
        return False, "Failed to sing song"
    
    def _execute_pass_turn(self) -> Tuple[bool, str]:
        """Execute passing the turn."""
        old_phase = self.game_state.current_phase
        current_player = self.game_state.current_player
        
        if self.game_state.current_phase.value == 'main':
            # Trigger PHASE_ENDS event
            phase_end_context = EventContext(
                event_type=GameEvent.PHASE_ENDS,
                source=old_phase,
                player=current_player,
                game_state=self.game_state,
                additional_data={'phase': old_phase.value}
            )
            self.event_manager.trigger_event(phase_end_context)
            
            # Trigger TURN_ENDS event
            turn_end_context = EventContext(
                event_type=GameEvent.TURN_ENDS,
                player=current_player,
                game_state=self.game_state,
                additional_data={'turn_number': self.game_state.turn_number}
            )
            self.event_manager.trigger_event(turn_end_context)
            
            # Advance phase (which will end turn and start new turn)
            old_player_index = self.game_state.current_player_index
            self.game_state.advance_phase()
            
            # If we moved to a new player, trigger TURN_BEGINS
            if self.game_state.current_player_index != old_player_index:
                new_player = self.game_state.current_player
                turn_begin_context = EventContext(
                    event_type=GameEvent.TURN_BEGINS,
                    player=new_player,
                    game_state=self.game_state,
                    additional_data={'turn_number': self.game_state.turn_number}
                )
                self.event_manager.trigger_event(turn_begin_context)
                
                # Trigger READY_STEP event
                ready_context = EventContext(
                    event_type=GameEvent.READY_STEP,
                    player=new_player,
                    game_state=self.game_state
                )
                self.event_manager.trigger_event(ready_context)
            
            return True, "Turn ended"
        else:
            # Trigger PHASE_ENDS event
            phase_end_context = EventContext(
                event_type=GameEvent.PHASE_ENDS,
                source=old_phase,
                player=current_player,
                game_state=self.game_state,
                additional_data={'phase': old_phase.value}
            )
            self.event_manager.trigger_event(phase_end_context)
            
            # Advance phase
            self.game_state.advance_phase()
            
            # Trigger PHASE_BEGINS event
            new_phase = self.game_state.current_phase
            phase_begin_context = EventContext(
                event_type=GameEvent.PHASE_BEGINS,
                source=new_phase,
                player=current_player,
                game_state=self.game_state,
                additional_data={'phase': new_phase.value}
            )
            self.event_manager.trigger_event(phase_begin_context)
            
            # Trigger specific phase events
            if new_phase.value == 'set':
                set_context = EventContext(
                    event_type=GameEvent.SET_STEP,
                    player=current_player,
                    game_state=self.game_state
                )
                self.event_manager.trigger_event(set_context)
                
                # Execute set step logic (draw card with events)
                self._execute_set_step()
            elif new_phase.value == 'main':
                main_context = EventContext(
                    event_type=GameEvent.MAIN_PHASE_BEGINS,
                    player=current_player,
                    game_state=self.game_state
                )
                self.event_manager.trigger_event(main_context)
            
            return True, f"Advanced to {self.game_state.current_phase.value} phase"