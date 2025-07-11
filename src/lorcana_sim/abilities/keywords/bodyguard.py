"""Bodyguard keyword ability implementation."""

from typing import TYPE_CHECKING, List
from ...models.abilities.base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState
    from ...models.cards.character_card import CharacterCard
    from ...models.game.player import Player

class BodyguardAbility(KeywordAbility):
    """Bodyguard - This character may enter play exerted. 
    An opposing character who challenges one of your characters must choose one with Bodyguard if able."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure this is a keyword ability
        self.type = AbilityType.KEYWORD
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Bodyguard is a passive ability, doesn't activate"""
        return False
    
    def can_enter_play_exerted(self) -> bool:
        """Check if this character can enter play exerted (optional for bodyguard)"""
        return True
    
    def must_be_challenged_first(self, defending_player: 'Player', 
                                potential_targets: List['CharacterCard']) -> bool:
        """Check if this bodyguard character must be challenged before other characters"""
        # If there are bodyguard characters available, they must be challenged first
        bodyguard_characters = []
        for character in potential_targets:
            if self._has_bodyguard(character):
                bodyguard_characters.append(character)
        
        # If there are bodyguard characters and this is one of them, it can be challenged
        # If there are bodyguard characters and this is NOT one of them, it cannot be challenged
        if bodyguard_characters:
            return self._has_bodyguard_ability(potential_targets[0])  # Simplified logic
        
        return True  # No bodyguard restriction
    
    def _has_bodyguard(self, character: 'CharacterCard') -> bool:
        """Check if a character has bodyguard"""
        for ability in character.abilities:
            if (hasattr(ability, 'keyword') and 
                ability.keyword == 'Bodyguard'):
                return True
        return False
    
    def _has_bodyguard_ability(self, character: 'CharacterCard') -> bool:
        """Check if this specific character has bodyguard"""
        return self._has_bodyguard(character)
    
    def modifies_challenge_targeting(self) -> bool:
        """This ability modifies challenge targeting rules"""
        return True
    
    def modifies_challenge_targets(self, attacker: 'CharacterCard', all_potential_targets: List['CharacterCard'], game_state: 'GameState') -> List['CharacterCard']:
        """Bodyguard forces attackers to challenge bodyguards first."""
        # Find all bodyguard characters in the potential targets
        bodyguard_characters = []
        non_bodyguard_characters = []
        
        for character in all_potential_targets:
            if self._has_bodyguard(character):
                bodyguard_characters.append(character)
            else:
                non_bodyguard_characters.append(character)
        
        # If there are bodyguard characters, they must be challenged first
        if bodyguard_characters:
            return bodyguard_characters  # Can only challenge bodyguards
        else:
            return all_potential_targets  # No bodyguards, can challenge anyone
    
    def execute(self, game_state: 'GameState', targets) -> None:
        """Bodyguard is a passive ability that modifies challenge targeting"""
        pass
    
    def __str__(self) -> str:
        return "Bodyguard"