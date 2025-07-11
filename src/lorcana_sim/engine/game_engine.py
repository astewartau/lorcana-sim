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
            return True, f"Played {card.name} as ink"
        
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
            
            # Trigger CHARACTER_PLAYED event
            event_context = EventContext(
                event_type=GameEvent.CHARACTER_PLAYED,
                source=character,
                player=current_player,
                game_state=self.game_state
            )
            trigger_results = self.event_manager.trigger_event(event_context)
            
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
            # TODO: Execute action's effects
            return True, f"Played action {action.name}"
        
        return False, "Failed to play action"
    
    def _execute_play_item(self, item: ItemCard) -> Tuple[bool, str]:
        """Execute playing an item card."""
        current_player = self.game_state.current_player
        
        if current_player.play_item(item, item.cost):
            self.game_state.actions_this_turn.append(GameAction.PLAY_ITEM)
            return True, f"Played item {item.name}"
        
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
        
        # Remove destroyed characters and trigger destruction events
        opponent = self.game_state.opponent
        result_messages = []
        
        if not attacker.is_alive:
            current_player.characters_in_play.remove(attacker)
            current_player.discard_pile.append(attacker)
            # Unregister abilities from destroyed character
            for ability in attacker.abilities:
                self.event_manager.unregister_triggered_ability(ability)
            destroy_context = EventContext(
                event_type=GameEvent.CHARACTER_DESTROYED,
                source=attacker,
                game_state=self.game_state
            )
            self.event_manager.trigger_event(destroy_context)
            result_messages.append(f"{attacker.name} was destroyed")
        
        if not defender.is_alive:
            opponent.characters_in_play.remove(defender)
            opponent.discard_pile.append(defender)
            # Unregister abilities from destroyed character
            for ability in defender.abilities:
                self.event_manager.unregister_triggered_ability(ability)
            destroy_context = EventContext(
                event_type=GameEvent.CHARACTER_DESTROYED,
                source=defender,
                game_state=self.game_state
            )
            self.event_manager.trigger_event(destroy_context)
            result_messages.append(f"{defender.name} was destroyed")
        
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
        if self.game_state.current_phase.value == 'main':
            self.game_state.advance_phase()
            return True, "Turn ended"
        else:
            self.game_state.advance_phase()
            return True, f"Advanced to {self.game_state.current_phase.value} phase"