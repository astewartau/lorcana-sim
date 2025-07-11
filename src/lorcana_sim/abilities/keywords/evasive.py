"""Evasive keyword ability implementation."""

from typing import TYPE_CHECKING
from ...models.abilities.base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState
    from ...models.cards.character_card import CharacterCard

class EvasiveAbility(KeywordAbility):
    """Evasive - Only characters with Evasive can challenge this character"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure this is a keyword ability
        self.type = AbilityType.KEYWORD
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Evasive is a passive ability, doesn't activate"""
        return False
    
    def can_be_challenged_by(self, challenger: 'CharacterCard') -> bool:
        """Check if the given character can challenge this evasive character"""
        # Check if challenger has evasive
        for ability in challenger.abilities:
            if (hasattr(ability, 'keyword') and 
                ability.keyword == 'Evasive'):
                return True
        return False
    
    def modifies_challenge_rules(self) -> bool:
        """This ability modifies who can challenge this character"""
        return True
    
    def allows_being_challenged_by(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Evasive characters can only be challenged by other evasive characters."""
        # Check if attacker has evasive
        attacker_has_evasive = any(
            hasattr(ability, 'keyword') and ability.keyword == 'Evasive'
            for ability in attacker.abilities
        )
        return attacker_has_evasive
    
    def execute(self, game_state: 'GameState', targets) -> None:
        """Evasive is a passive ability that modifies challenge rules"""
        pass
    
    def __str__(self) -> str:
        return "Evasive"