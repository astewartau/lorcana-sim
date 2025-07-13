"""Move validation system for Lorcana gameplay."""

from typing import List, Tuple, Optional, Dict, Any
from ..models.game.game_state import GameState, GameAction, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card


class MoveValidator:
    """Validates possible moves and game actions."""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
    
    def get_all_legal_actions(self) -> List[Tuple[GameAction, Dict[str, Any]]]:
        """Get all legal actions for current player in current phase."""
        legal_actions = []
        
        # No actions available if game is over
        if self.game_state.is_game_over():
            return legal_actions
        
        current_player = self.game_state.current_player
        phase = self.game_state.current_phase
        
        # Use value comparison to avoid enum identity issues
        if phase.value == 'ready':
            legal_actions.append((GameAction.PROGRESS, {}))
            legal_actions.append((GameAction.PASS_TURN, {}))
        
        elif phase.value == 'set':
            # Set step - resolve start-of-turn effects
            legal_actions.append((GameAction.PROGRESS, {}))
            legal_actions.append((GameAction.PASS_TURN, {}))
        
        elif phase.value == 'draw':
            # Draw step - draw a card
            legal_actions.append((GameAction.PROGRESS, {}))
            legal_actions.append((GameAction.PASS_TURN, {}))
        
        elif phase.value == 'play':
            # Play ink (once per turn)
            if self.game_state.can_play_ink():
                ink_cards = self.get_playable_ink_cards()
                for card in ink_cards:
                    legal_actions.append((GameAction.PLAY_INK, {'card': card}))
            # Play characters
            characters = self.get_playable_characters()
            for character in characters:
                legal_actions.append((GameAction.PLAY_CHARACTER, {'card': character}))
            
            # Play actions
            actions = self.get_playable_actions()
            for action in actions:
                legal_actions.append((GameAction.PLAY_ACTION, {'card': action}))
            
            # Play items
            items = self.get_playable_items()
            for item in items:
                legal_actions.append((GameAction.PLAY_ITEM, {'card': item}))
            
            # Quest with characters
            questing = self.get_characters_that_can_quest()
            for character in questing:
                legal_actions.append((GameAction.QUEST_CHARACTER, {'character': character}))
            
            # Challenge with characters
            challenges = self.get_possible_challenges()
            for attacker, defender in challenges:
                legal_actions.append((GameAction.CHALLENGE_CHARACTER, {
                    'attacker': attacker, 
                    'defender': defender
                }))
            
            # Sing songs
            songs = self.get_singable_songs()
            for song, singer in songs:
                legal_actions.append((GameAction.SING_SONG, {
                    'song': song,
                    'singer': singer
                }))
            
            # Add progress and pass turn options
            legal_actions.append((GameAction.PROGRESS, {}))
            legal_actions.append((GameAction.PASS_TURN, {}))
        
        return legal_actions
    
    def get_playable_ink_cards(self) -> List[Card]:
        """Get cards that can be played as ink."""
        current_player = self.game_state.current_player
        return [card for card in current_player.hand if card.can_be_inked()]
    
    def get_playable_characters(self) -> List[CharacterCard]:
        """Get character cards that can be played."""
        current_player = self.game_state.current_player
        playable = []
        
        for card in current_player.hand:
            if isinstance(card, CharacterCard) and current_player.can_afford(card):
                playable.append(card)
        
        return playable
    
    def get_playable_actions(self) -> List[ActionCard]:
        """Get action cards that can be played."""
        current_player = self.game_state.current_player
        playable = []
        
        for card in current_player.hand:
            if isinstance(card, ActionCard) and current_player.can_afford(card):
                playable.append(card)
        
        return playable
    
    def get_playable_items(self) -> List[ItemCard]:
        """Get item cards that can be played."""
        current_player = self.game_state.current_player
        playable = []
        
        for card in current_player.hand:
            if isinstance(card, ItemCard) and current_player.can_afford(card):
                playable.append(card)
        
        return playable
    
    def get_characters_that_can_quest(self) -> List[CharacterCard]:
        """Get characters that can quest this turn."""
        current_player = self.game_state.current_player
        current_turn = self.game_state.turn_number
        return [char for char in current_player.characters_in_play if char.can_quest(current_turn)]
    
    def get_possible_challenges(self) -> List[Tuple[CharacterCard, CharacterCard]]:
        """Get all possible (attacker, defender) challenge pairs."""
        current_player = self.game_state.current_player
        opponent = self.game_state.opponent
        current_turn = self.game_state.turn_number
        
        challenges = []
        # Get attackers that can challenge (considering ink drying and Rush)
        ready_attackers = [char for char in current_player.characters_in_play 
                          if char.can_challenge(current_turn)]
        possible_defenders = opponent.characters_in_play
        
        for attacker in ready_attackers:
            # Get valid targets for this attacker (considering targeting modification abilities)
            valid_defenders = self._get_valid_challenge_targets(attacker, possible_defenders)
            
            for defender in valid_defenders:
                if self.can_challenge(attacker, defender):
                    challenges.append((attacker, defender))
        
        return challenges
    
    def _get_valid_challenge_targets(self, attacker: CharacterCard, all_defenders: List[CharacterCard]) -> List[CharacterCard]:
        """Get valid challenge targets considering abilities that modify targeting."""
        valid_targets = []
        
        # Check if attacker has Evasive
        attacker_has_evasive = self._character_has_evasive(attacker)
        
        for defender in all_defenders:
            # Check if defender has Evasive
            if self._character_has_evasive(defender):
                # Only attackers with Evasive can challenge Evasive defenders
                if attacker_has_evasive:
                    valid_targets.append(defender)
                # else: can't challenge this defender
            else:
                # Non-Evasive defenders can be challenged by anyone
                valid_targets.append(defender)
        
        # TODO: Add Bodyguard redirection logic here
        
        return valid_targets
    
    def _character_has_evasive(self, character: CharacterCard) -> bool:
        """Check if a character has Evasive ability."""
        if hasattr(character, 'composable_abilities'):
            for ability in character.composable_abilities:
                if hasattr(ability, 'name') and 'evasive' in ability.name.lower():
                    return True
        return False
    
    def can_challenge(self, attacker: CharacterCard, defender: CharacterCard) -> bool:
        """Check if attacker can challenge defender using ability delegation."""
        current_turn = self.game_state.turn_number
        
        # Basic challenge rules (including ink drying and Rush)
        if not attacker.can_challenge(current_turn):
            return False
        
        if not defender.is_alive:
            return False
        
        # Get the defender's owner's characters to check targeting restrictions
        opponent = self.game_state.opponent if attacker in self.game_state.current_player.characters_in_play else self.game_state.current_player
        all_possible_defenders = opponent.characters_in_play
        
        # Check if this defender is a valid target considering targeting modifications
        valid_targets = self._get_valid_challenge_targets(attacker, all_possible_defenders)
        if defender not in valid_targets:
            return False
        
        # New framework abilities don't restrict challenges by default
        
        return True
    
    def get_singable_songs(self) -> List[Tuple[ActionCard, CharacterCard]]:
        """Get (song, singer) pairs for songs that can be sung using ability delegation."""
        current_player = self.game_state.current_player
        singable = []
        
        for card in current_player.hand:
            if isinstance(card, ActionCard) and card.is_song:
                # Find characters that can sing this song
                ready_characters = current_player.get_ready_characters()
                
                for character in ready_characters:
                    if self._can_sing_song(character, card):
                        singable.append((card, character))
        
        return singable
    
    def _can_sing_song(self, singer: CharacterCard, song: ActionCard) -> bool:
        """Check if a character can sing a song using composable abilities."""
        # Check if singer is exerted
        if singer.exerted:
            return False
        
        # Check composable abilities for Singer
        required_cost = self._get_song_singer_cost(song)
        for ability in singer.composable_abilities:
            if ability.can_sing_song(required_cost):
                return True
        
        return False
    
    def _get_song_singer_cost(self, song: ActionCard) -> int:
        """Extract the singer cost requirement from a song."""
        # Try to parse the singer cost from song abilities
        for ability in song.abilities:
            if hasattr(ability, 'effect') and "sing this song" in ability.effect.lower():
                # Try to extract cost from text like "A character with cost X or more can sing this song"
                import re
                match = re.search(r'cost (\d+)', ability.effect.lower())
                if match:
                    return int(match.group(1))
        
        # Fallback: assume songs require a cost equal to their regular cost
        return song.cost
    
    def validate_action(self, action: GameAction, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if a specific action with parameters is legal."""
        legal_actions = self.get_all_legal_actions()
        
        for legal_action, legal_params in legal_actions:
            if action == legal_action:
                # Check if parameters match
                if self._parameters_match(parameters, legal_params):
                    return True, "Action is legal"
        
        return False, f"Action {action} with parameters {parameters} is not legal"
    
    def _parameters_match(self, given: Dict[str, Any], legal: Dict[str, Any]) -> bool:
        """Check if given parameters match legal parameters."""
        for key, value in given.items():
            if key not in legal or legal[key] != value:
                return False
        return True