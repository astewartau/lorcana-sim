"""Move validation system for Lorcana gameplay."""

from typing import List, Tuple, Optional, Dict, Any
from ..models.game.game_state import GameState, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card


class MoveValidator:
    """Validates possible moves and game actions."""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.temporarily_blocked_actions = set()
        self.last_clear_turn = -1
        self.last_clear_phase = ""
    
    def get_all_legal_actions(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all legal actions for current player in current phase."""
        legal_actions = []
        
        # No actions available if game is over
        if self.game_state.is_game_over():
            return legal_actions
        
        current_player = self.game_state.current_player
        phase = self.game_state.current_phase
        
        # Use value comparison to avoid enum identity issues
        if phase.value == 'ready':
            # READY phase auto-progresses - no player actions available
            pass
        
        elif phase.value == 'set':
            # SET phase auto-progresses - no player actions available
            pass
        
        elif phase.value == 'draw':
            # DRAW phase auto-progresses - no player actions available
            pass
        
        elif phase.value == 'play':
            # Play ink (once per turn)
            can_play_ink = self.game_state.can_play_ink()
            if can_play_ink:
                ink_cards = self.get_playable_ink_cards()
                for card in ink_cards:
                    legal_actions.append(("play_ink", {'card': card}))
            # Play characters
            characters = self.get_playable_characters()
            for character in characters:
                legal_actions.append(("play_character", {'card': character}))
            
            # Play actions
            actions = self.get_playable_actions()
            for action in actions:
                legal_actions.append(("play_action", {'card': action}))
            
            # Play items
            items = self.get_playable_items()
            for item in items:
                legal_actions.append(("play_item", {'card': item}))
            
            # Quest with characters
            questing = self.get_characters_that_can_quest()
            for character in questing:
                legal_actions.append(("quest_character", {'character': character}))
            
            # Challenge with characters
            challenges = self.get_possible_challenges()
            for attacker, defender in challenges:
                legal_actions.append(("challenge_character", {
                    'attacker': attacker, 
                    'defender': defender
                }))
            
            # Sing songs
            songs = self.get_singable_songs()
            for song, singer in songs:
                legal_actions.append(("sing_song", {
                    'song': song,
                    'singer': singer
                }))
            
            # Add progress and pass turn options
            legal_actions.append(("progress", {}))
            legal_actions.append(("pass_turn", {}))
        
        # Clear blocked actions if turn or phase has changed
        self._clear_blocked_actions_if_needed()
        
        # Filter out temporarily blocked actions
        filtered_actions = []
        for action, params in legal_actions:
            action_signature = self._create_action_signature(action, params)
            if action_signature not in self.temporarily_blocked_actions:
                filtered_actions.append((action, params))
        
        return filtered_actions
    
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
        return [char for char in current_player.characters_in_play 
                if char.can_quest(current_turn) and not self.game_state.has_character_acted_this_turn(char.id)]
    
    def get_possible_challenges(self) -> List[Tuple[CharacterCard, CharacterCard]]:
        """Get all possible (attacker, defender) challenge pairs."""
        current_player = self.game_state.current_player
        opponent = self.game_state.opponent
        current_turn = self.game_state.turn_number
        
        challenges = []
        # Get attackers that can challenge (considering ink drying and Rush, and haven't acted this turn)
        ready_attackers = [char for char in current_player.characters_in_play 
                          if char.can_challenge(current_turn) and not self.game_state.has_character_acted_this_turn(char.id)]
        possible_defenders = opponent.characters_in_play
        
        for attacker in ready_attackers:
            # Get valid targets for this attacker (considering targeting modification abilities)
            valid_defenders = self._get_valid_challenge_targets(attacker, possible_defenders)
            
            for defender in valid_defenders:
                if self.can_challenge(attacker, defender):
                    challenges.append((attacker, defender))
        
        return challenges
    
    def _get_valid_challenge_targets(self, attacker: CharacterCard, all_defenders: List[CharacterCard]) -> List[CharacterCard]:
        """Get valid challenge targets considering abilities that modify targeting.
        
        This method filters defenders based on:
        1. Basic challenge rules (must be exerted)
        2. Evasive ability interactions
        3. Bodyguard targeting enforcement
        """
        # Step 1: Filter for basic challengeable defenders (must be exerted and alive)
        challengeable_defenders = [
            defender for defender in all_defenders 
            if defender.exerted and defender.is_alive
        ]
        
        # Step 2: Apply Evasive filtering
        valid_targets = []
        attacker_has_evasive = self._character_has_evasive(attacker)
        
        for defender in challengeable_defenders:
            if self._character_has_evasive(defender):
                # Only attackers with Evasive can challenge Evasive defenders
                if attacker_has_evasive:
                    valid_targets.append(defender)
            else:
                # Non-Evasive defenders can be challenged by anyone
                valid_targets.append(defender)
        
        # Step 3: Apply Bodyguard targeting enforcement
        # Check if there are any exerted Bodyguard characters among valid targets
        bodyguard_targets = [
            target for target in valid_targets 
            if self._character_has_bodyguard(target)
        ]
        
        # If there are any Bodyguard characters that can be challenged, 
        # ONLY they can be targeted
        if bodyguard_targets:
            return bodyguard_targets
        
        # Otherwise, return all valid targets
        return valid_targets
    
    def _character_has_evasive(self, character: CharacterCard) -> bool:
        """Check if a character has Evasive ability."""
        if hasattr(character, 'composable_abilities'):
            for ability in character.composable_abilities:
                if hasattr(ability, 'name') and 'evasive' in ability.name.lower():
                    return True
        return False
    
    def _character_has_bodyguard(self, character: CharacterCard) -> bool:
        """Check if a character has Bodyguard ability."""
        # Check metadata first (set by BodyguardEffect)
        if hasattr(character, 'metadata') and character.metadata.get('has_bodyguard', False):
            return True
        
        # Also check composable abilities as fallback
        if hasattr(character, 'composable_abilities'):
            for ability in character.composable_abilities:
                if hasattr(ability, 'name') and 'bodyguard' in ability.name.lower():
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
        
        # Get the required cost to sing this song
        required_cost = self._get_song_singer_cost(song)
        
        # Check composable abilities for Singer
        if hasattr(singer, 'composable_abilities') and singer.composable_abilities:
            for ability in singer.composable_abilities:
                if hasattr(ability, 'can_sing_song') and ability.can_sing_song(required_cost):
                    return True
        
        # Check if character's basic cost meets the song requirement
        # Songs like "Characters with cost 3 or more can sing this song"
        if singer.cost >= required_cost:
            return True
        
        return False
    
    def _get_song_singer_cost(self, song: ActionCard) -> int:
        """Extract the singer cost requirement from a song."""
        # Try to parse the singer cost from song effects (ActionCard has effects, not abilities)
        for effect in song.effects:
            if "sing this song" in effect.lower():
                # Try to extract cost from text like "Characters with cost X or more can sing this song"
                import re
                match = re.search(r'cost (\d+)', effect.lower())
                if match:
                    return int(match.group(1))
        
        # Fallback: assume songs require a cost equal to their regular cost
        return song.cost
    
    def validate_action(self, action: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
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
    
    def block_action_temporarily(self, action: str, parameters: Dict[str, Any]) -> None:
        """Temporarily block an action that has failed."""
        action_signature = self._create_action_signature(action, parameters)
        self.temporarily_blocked_actions.add(action_signature)
        print(f"🚫 Temporarily blocked action: {action_signature}")
    
    def clear_blocked_actions(self) -> None:
        """Clear all temporarily blocked actions."""
        if self.temporarily_blocked_actions:
            print(f"🔓 Cleared {len(self.temporarily_blocked_actions)} blocked actions")
            self.temporarily_blocked_actions.clear()
    
    def _clear_blocked_actions_if_needed(self) -> None:
        """Clear blocked actions on phase transitions or turn changes."""
        current_turn = self.game_state.turn_number
        current_phase = self.game_state.current_phase.value
        
        if (current_turn != self.last_clear_turn or 
            current_phase != self.last_clear_phase):
            self.clear_blocked_actions()
            self.last_clear_turn = current_turn
            self.last_clear_phase = current_phase
    
    def _create_action_signature(self, action: str, parameters: Dict[str, Any]) -> str:
        """Create a unique signature for an action to track blocked actions."""
        # Create a signature that includes the action type and key identifying parameters
        signature_parts = [action]
        
        # Add key parameters that uniquely identify the action
        if 'card' in parameters:
            card = parameters['card']
            if hasattr(card, 'id'):
                signature_parts.append(f"card_id:{card.id}")
            elif hasattr(card, 'name'):
                signature_parts.append(f"card_name:{card.name}")
        
        if 'character' in parameters:
            character = parameters['character']
            if hasattr(character, 'id'):
                signature_parts.append(f"character_id:{character.id}")
            elif hasattr(character, 'name'):
                signature_parts.append(f"character_name:{character.name}")
        
        if 'attacker' in parameters:
            attacker = parameters['attacker']
            if hasattr(attacker, 'id'):
                signature_parts.append(f"attacker_id:{attacker.id}")
            elif hasattr(attacker, 'name'):
                signature_parts.append(f"attacker_name:{attacker.name}")
        
        if 'defender' in parameters:
            defender = parameters['defender']
            if hasattr(defender, 'id'):
                signature_parts.append(f"defender_id:{defender.id}")
            elif hasattr(defender, 'name'):
                signature_parts.append(f"defender_name:{defender.name}")
        
        return "|".join(signature_parts)