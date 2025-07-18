"""Game engine for executing actions and managing state transitions."""

from typing import Dict, Any, Tuple, Optional, List
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


class GameEngine:
    """Executes game actions and manages state transitions."""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.validator = MoveValidator(game_state)
        self.event_manager = GameEventManager(game_state)
        self.damage_calculator = DamageCalculator(game_state)
        self.choice_manager = GameChoiceManager()
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
        """Execute a game action and update state."""
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
        
        # Record action for stalemate detection
        self.game_state.record_action(action)
        
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
            elif action == GameAction.PROGRESS:
                return self._execute_progress()
            elif action == GameAction.PASS_TURN:
                return self._execute_pass_turn()
            else:
                return ActionResult.failure_result(action, f"Unknown action: {action}")
        
        except Exception as e:
            return ActionResult.failure_result(action, f"Error executing action: {str(e)}")
    
    def _execute_play_ink(self, card: Card) -> ActionResult:
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
            
            return ActionResult.success_result(
                action_type=GameAction.PLAY_INK,
                result_type=ActionResultType.INK_PLAYED,
                card=card,
                player=current_player,
                ink_after=current_player.available_ink,
                total_ink=current_player.total_ink,
                triggered_abilities=trigger_results or []
            )
        
        return ActionResult.failure_result(GameAction.PLAY_INK, "Failed to play ink")
    
    def _execute_play_character(self, character: CharacterCard) -> ActionResult:
        """Execute playing a character card."""
        print(f"DEBUG: _execute_play_character called for {character.name}")
        current_player = self.game_state.current_player
        
        if current_player.play_character(character, character.cost):
            print(f"DEBUG: Successfully played character {character.name}")
            self.game_state.actions_this_turn.append(GameAction.PLAY_CHARACTER)
            
            print(f"DEBUG: Setting turn_played for {character.name}")
            # Set turn_played for ink drying system
            character.turn_played = self.game_state.turn_number
            character.is_dry = False  # Character has wet ink when just played
            
            # Note: Triggered abilities are now part of composable_abilities
            # They will be registered below with the composable abilities
            
            # Register composable abilities this character has
            try:
                print(f"DEBUG: About to register composable abilities for {character.name}")
                print(f"DEBUG: Character {character.name} has {len(character.composable_abilities)} composable abilities")
                for ability in character.composable_abilities:
                    print(f"DEBUG: Registering ability {ability.name}")
                    self.event_manager.register_composable_ability(ability)
            except Exception as e:
                print(f"DEBUG: Exception during ability registration: {e}")
                import traceback
                traceback.print_exc()
            
            # Notify zone transition: card moved from hand to play
            # This will handle conditional effect registration/deregistration based on activation zones
            zone_events = self.game_state.notify_card_zone_change(character, 'hand', 'play')
            
            # Store zone events for message processing later
            if zone_events and not hasattr(self, '_pending_zone_events'):
                self._pending_zone_events = []
            if zone_events:
                self._pending_zone_events.extend(zone_events)
            
            # Trigger CHARACTER_ENTERS_PLAY event (more general)
            enters_context = EventContext(
                event_type=GameEvent.CHARACTER_ENTERS_PLAY,
                source=character,
                player=current_player,
                game_state=self.game_state
            )
            trigger_results = self.trigger_event_with_choices(enters_context)
            
            # Trigger CHARACTER_PLAYED event (specific to playing from hand)
            played_context = EventContext(
                event_type=GameEvent.CHARACTER_PLAYED,
                source=character,
                player=current_player,
                game_state=self.game_state
            )
            played_results = self.trigger_event_with_choices(played_context)
            if played_results:
                trigger_results.extend(played_results)
            
            # Include zone events in the result
            result_data = {
                'character': character,
                'player': current_player,
                'ink_after': current_player.available_ink,
                'total_ink': current_player.total_ink,
                'triggered_abilities': trigger_results or []
            }
            
            # Add zone events if any occurred
            if hasattr(self, '_pending_zone_events') and self._pending_zone_events:
                result_data['zone_events'] = self._pending_zone_events.copy()
                self._pending_zone_events.clear()
            
            return ActionResult.success_result(
                action_type=GameAction.PLAY_CHARACTER,
                result_type=ActionResultType.CHARACTER_PLAYED,
                **result_data
            )
        
        return ActionResult.failure_result(GameAction.PLAY_CHARACTER, "Failed to play character")
    
    def _execute_play_action(self, action: ActionCard) -> ActionResult:
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
            
            return ActionResult.success_result(
                action_type=GameAction.PLAY_ACTION,
                result_type=ActionResultType.ACTION_PLAYED,
                action=action,
                player=current_player,
                ink_after=current_player.available_ink,
                total_ink=current_player.total_ink,
                triggered_abilities=trigger_results or []
            )
        
        return ActionResult.failure_result(GameAction.PLAY_ACTION, "Failed to play action")
    
    def _execute_play_item(self, item: ItemCard) -> ActionResult:
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
            
            return ActionResult.success_result(
                action_type=GameAction.PLAY_ITEM,
                result_type=ActionResultType.ITEM_PLAYED,
                item=item,
                player=current_player,
                ink_after=current_player.available_ink,
                total_ink=current_player.total_ink,
                triggered_abilities=trigger_results or []
            )
        
        return ActionResult.failure_result(GameAction.PLAY_ITEM, "Failed to play item")
    
    def _execute_quest_character(self, character: CharacterCard) -> ActionResult:
        """Execute questing with a character."""
        if character.can_quest(self.game_state.turn_number) and not self.game_state.has_character_acted_this_turn(character.id):
            character.exert()
            self.game_state.mark_character_acted(character.id)
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
            # current_lore already includes all bonuses from abilities
            lore_gained = character.current_lore
            lore_before = current_player.lore
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
            
            return ActionResult.success_result(
                action_type=GameAction.QUEST_CHARACTER,
                result_type=ActionResultType.CHARACTER_QUESTED,
                character=character,
                player=current_player,
                lore_gained=lore_gained,
                lore_before=lore_before,
                lore_after=current_player.lore,
                triggered_abilities=trigger_results or []
            )
        
        # Check if character has already acted this turn
        if self.game_state.has_character_acted_this_turn(character.id):
            return ActionResult.failure_result(GameAction.QUEST_CHARACTER, "Character has already acted this turn")
        
        return ActionResult.failure_result(GameAction.QUEST_CHARACTER, "Character cannot quest")
    
    def _execute_challenge(self, attacker: CharacterCard, defender: CharacterCard) -> ActionResult:
        """Execute a challenge between characters."""
        if self.game_state.has_character_acted_this_turn(attacker.id):
            return ActionResult.failure_result(GameAction.CHALLENGE_CHARACTER, "Character has already acted this turn")
        
        if not self.validator.can_challenge(attacker, defender):
            return ActionResult.failure_result(GameAction.CHALLENGE_CHARACTER, "Invalid challenge")
        
        # Exert attacker and mark as acted
        attacker.exert()
        self.game_state.mark_character_acted(attacker.id)
        
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
        
        # Calculate damage to defender with ability modifications
        defender_base_damage = attacker.current_strength
        if defender_base_damage > 0:
            # Trigger CHARACTER_TAKES_DAMAGE event BEFORE dealing damage (for Resist, etc.)
            defender_damage_context = EventContext(
                event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
                source=attacker,
                target=defender,
                player=current_player,
                game_state=self.game_state,
                additional_data={
                    'damage': defender_base_damage,
                    'base_damage': defender_base_damage,
                    'damage_type': DamageType.CHALLENGE
                }
            )
            self.event_manager.trigger_event(defender_damage_context)
            
            # Get the modified damage from the event context
            final_defender_damage = defender_damage_context.additional_data.get('damage', defender_base_damage)
            
            # Apply the damage (bypassing damage calculator since we already calculated it via events)
            defender.damage += final_defender_damage
            defender_damage_taken = final_defender_damage
        else:
            defender_damage_taken = 0
        
        # Calculate damage to attacker with ability modifications
        attacker_base_damage = defender.current_strength
        if attacker_base_damage > 0:
            # Trigger CHARACTER_TAKES_DAMAGE event BEFORE dealing damage (for Resist, etc.)
            attacker_damage_context = EventContext(
                event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
                source=defender,
                target=attacker,
                player=self.game_state.opponent,
                game_state=self.game_state,
                additional_data={
                    'damage': attacker_base_damage,
                    'base_damage': attacker_base_damage,
                    'damage_type': DamageType.CHALLENGE
                }
            )
            self.event_manager.trigger_event(attacker_damage_context)
            
            # Get the modified damage from the event context
            final_attacker_damage = attacker_damage_context.additional_data.get('damage', attacker_base_damage)
            
            # Apply the damage (bypassing damage calculator since we already calculated it via events)
            attacker.damage += final_attacker_damage
            attacker_damage_taken = final_attacker_damage
        else:
            attacker_damage_taken = 0
        
        # Remove banished characters and trigger banishment events
        opponent = self.game_state.opponent
        banished_characters = []
        
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
            
            # Trigger CHARACTER_BANISHED event BEFORE unregistering abilities
            banish_context = EventContext(
                event_type=GameEvent.CHARACTER_BANISHED,
                source=attacker,
                player=current_player,
                game_state=self.game_state,
                banishment_cause="challenge"
            )
            self.trigger_event_with_choices(banish_context)
            
            # Trigger CHARACTER_BANISHED_IN_CHALLENGE event for abilities that specifically care
            challenge_banish_context = EventContext(
                event_type=GameEvent.CHARACTER_BANISHED_IN_CHALLENGE,
                source=attacker,
                player=current_player,
                game_state=self.game_state
            )
            self.trigger_event_with_choices(challenge_banish_context)
            
            # Now remove from play and unregister abilities
            # Note: Some abilities like RECURRING GUST may have already moved the character to hand
            if attacker in current_player.characters_in_play:
                current_player.characters_in_play.remove(attacker)
                current_player.discard_pile.append(attacker)
            # Unregister composable abilities from banished character
            attacker.unregister_composable_abilities(self.event_manager)
            banished_characters.append(attacker.name)
        
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
            
            # Trigger CHARACTER_BANISHED event BEFORE unregistering abilities
            banish_context = EventContext(
                event_type=GameEvent.CHARACTER_BANISHED,
                source=defender,
                player=opponent,
                game_state=self.game_state,
                banishment_cause="challenge"
            )
            self.trigger_event_with_choices(banish_context)
            
            # Trigger CHARACTER_BANISHED_IN_CHALLENGE event for abilities that specifically care
            challenge_banish_context = EventContext(
                event_type=GameEvent.CHARACTER_BANISHED_IN_CHALLENGE,
                source=defender,
                player=opponent,
                game_state=self.game_state
            )
            self.trigger_event_with_choices(challenge_banish_context)
            
            # Now remove from play and unregister abilities
            # Note: Some abilities like RECURRING GUST may have already moved the character to hand
            if defender in opponent.characters_in_play:
                opponent.characters_in_play.remove(defender)
                opponent.discard_pile.append(defender)
            # Unregister composable abilities from banished character
            defender.unregister_composable_abilities(self.event_manager)
            banished_characters.append(defender.name)
        
        self.game_state.actions_this_turn.append(GameAction.CHALLENGE_CHARACTER)
        
        return ActionResult.success_result(
            action_type=GameAction.CHALLENGE_CHARACTER,
            result_type=ActionResultType.CHARACTER_CHALLENGED,
            attacker=attacker,
            defender=defender,
            player=current_player,
            attacker_damage_taken=attacker_damage_taken,
            defender_damage_taken=defender_damage_taken,
            banished_characters=banished_characters,
            triggered_abilities=trigger_results or []
        )
    
    def _execute_sing_song(self, song: ActionCard, singer: CharacterCard) -> ActionResult:
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
                game_state=self.game_state,
                additional_data={'singer': singer, 'song': song}
            )
            trigger_results = self.event_manager.trigger_event(event_context)
            
            self.game_state.actions_this_turn.append(GameAction.SING_SONG)
            
            return ActionResult.success_result(
                action_type=GameAction.SING_SONG,
                result_type=ActionResultType.SONG_SUNG,
                song=song,
                singer=singer,
                player=current_player,
                triggered_abilities=trigger_results or []
            )
        
        return ActionResult.failure_result(GameAction.SING_SONG, "Failed to sing song")
    
    def _execute_progress(self) -> ActionResult:
        """Execute progressing to the next phase."""
        old_phase = self.game_state.current_phase
        current_player = self.game_state.current_player
        
        # Capture hand/deck state before phase transition for draw detection
        hand_before = len(current_player.hand)
        deck_before = len(current_player.deck)
        
        # Trigger PHASE_ENDS event
        phase_end_context = EventContext(
            event_type=GameEvent.PHASE_ENDS,
            source=old_phase,
            player=current_player,
            game_state=self.game_state,
            additional_data={'phase': old_phase.value}
        )
        self.event_manager.trigger_event(phase_end_context)
        
        # If we're progressing from play phase, end the turn
        if self.game_state.current_phase.value == 'play':
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
                
                # Don't execute ready step here - let the stepped engine handle it
                # Mark that ready step needs to be executed
                self.game_state._needs_ready_step = True
                
                return ActionResult.success_result(
                    action_type=GameAction.PROGRESS,
                    result_type=ActionResultType.TURN_ENDED,
                    old_player=current_player,
                    new_player=new_player,
                    turn_number=self.game_state.turn_number,
                    new_phase=self.game_state.current_phase
                )
        else:
            # Advance phase within the same turn
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
            
            # Trigger specific phase events and execute phase logic
            result_data = {
                'old_phase': old_phase,
                'new_phase': new_phase,
                'player': current_player
            }
            
            if new_phase.value == 'set':
                set_context = EventContext(
                    event_type=GameEvent.SET_STEP,
                    player=current_player,
                    game_state=self.game_state
                )
                self.event_manager.trigger_event(set_context)
                self._execute_set_step()
                
            elif new_phase.value == 'draw':
                draw_context = EventContext(
                    event_type=GameEvent.DRAW_STEP,
                    player=current_player,
                    game_state=self.game_state
                )
                self.event_manager.trigger_event(draw_context)
                
                # Use the event-aware draw method instead of direct draw_step
                self._execute_draw_step()
                
                # Check if cards were drawn
                hand_after = len(current_player.hand)
                deck_after = len(current_player.deck)
                cards_drawn = hand_after - hand_before
                
                # Get draw events from the game state
                draw_events = []
                if cards_drawn > 0:
                    # Find the most recent card drawn event
                    last_event = self.game_state.get_last_event()
                    if last_event and last_event.get('type') == 'CARD_DRAWN':
                        cards_drawn_names = [card.name for card in last_event.get('cards_drawn', [])]
                        if cards_drawn_names:
                            draw_events = [f"{current_player.name} drew {card_name}" for card_name in cards_drawn_names]
                
                result_data.update({
                    'card_drawn': cards_drawn > 0,
                    'cards_drawn': cards_drawn,
                    'hand_size': hand_after,
                    'deck_size': deck_after,
                    'first_player_first_turn': (self.game_state.turn_number == 1 and 
                                              self.game_state.current_player_index == 0),
                    'draw_events': draw_events
                })
                
                # Include zone events from drawing if any occurred
                if hasattr(self, '_pending_zone_events') and self._pending_zone_events:
                    result_data['zone_events'] = self._pending_zone_events.copy()
                    self._pending_zone_events.clear()
                
            elif new_phase.value == 'play':
                play_context = EventContext(
                    event_type=GameEvent.MAIN_PHASE_BEGINS,
                    player=current_player,
                    game_state=self.game_state
                )
                self.event_manager.trigger_event(play_context)
            
            return ActionResult.success_result(
                action_type=GameAction.PROGRESS,
                result_type=ActionResultType.PHASE_ADVANCED,
                **result_data
            )
    
    def _execute_pass_turn(self) -> ActionResult:
        """Execute passing the turn to the opponent."""
        old_phase = self.game_state.current_phase
        current_player = self.game_state.current_player
        
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
        
        # End turn and start next player's turn
        old_player_index = self.game_state.current_player_index
        self.game_state.end_turn()
        
        # Evaluate conditional effects now that turn has actually changed
        turn_change_events = self.game_state.evaluate_conditional_effects()
        
        # Store turn change events for stepped engine processing
        if turn_change_events and not hasattr(self, '_pending_zone_events'):
            self._pending_zone_events = []
        if turn_change_events:
            self._pending_zone_events.extend(turn_change_events)
        
        # Trigger TURN_BEGINS for new player
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
        
        # Don't execute ready step here - let the stepped engine handle it
        # Mark that ready step needs to be executed
        self.game_state._needs_ready_step = True
        
        # Include turn change events in the result
        result_data = {
            'old_player': current_player,
            'new_player': new_player,
            'turn_number': self.game_state.turn_number,
            'new_phase': self.game_state.current_phase
        }
        
        # Add turn change events if any occurred
        if hasattr(self, '_pending_zone_events') and self._pending_zone_events:
            result_data['zone_events'] = self._pending_zone_events.copy()
            self._pending_zone_events.clear()
        
        return ActionResult.success_result(
            action_type=GameAction.PASS_TURN,
            result_type=ActionResultType.TURN_ENDED,
            **result_data
        )
    
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
    
    def auto_resolve_choices(self) -> int:
        """
        Auto-resolve all pending choices with their default options.
        Useful for automated play or testing.
        
        Returns:
            Number of choices that were auto-resolved
        """
        return self.choice_manager.auto_resolve_with_defaults()
    
    def clear_all_choices(self) -> None:
        """Clear all pending choices and resume the game. Use with caution."""
        self.choice_manager.clear_all_choices()
    
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