"""Rush keyword ability implementation."""

from typing import TYPE_CHECKING
from ...models.abilities.base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState
    from ...models.cards.character_card import CharacterCard

class RushAbility(KeywordAbility):
    """Rush - This character can challenge the turn they're played."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure this is a keyword ability
        self.type = AbilityType.KEYWORD
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Rush is a passive ability, doesn't activate"""
        return False
    
    def can_challenge_immediately(self) -> bool:
        """Check if this character can challenge the turn it's played"""
        return True
    
    def ignores_summoning_sickness_for_challenges(self) -> bool:
        """Rush allows challenging immediately, ignoring normal summoning sickness"""
        return True
    
    def allows_quest_immediately(self) -> bool:
        """Rush only affects challenges, not questing (still need to wait a turn to quest)"""
        return False
    
    def modifies_challenge_timing(self) -> bool:
        """This ability modifies when the character can challenge"""
        return True
    
    def is_passive_modifier(self) -> bool:
        """Rush is a passive ability that modifies play rules"""
        return True
    
    def allows_challenging(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Rush allows challenging immediately when played (ignores summoning sickness)."""
        # Rush removes the restriction on challenging the turn a character is played
        # In a full implementation, we'd check if the character was played this turn
        # For now, Rush just allows all challenges (the timing check would be elsewhere)
        return True
    
    def allows_being_challenged_by(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Rush doesn't affect being challenged by others."""
        return True
    
    def modifies_challenge_targets(self, attacker: 'CharacterCard', all_potential_targets: list, game_state: 'GameState') -> list:
        """Rush doesn't modify challenge targeting."""
        return all_potential_targets
    
    def allows_singing_song(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> bool:
        """Rush doesn't affect singing."""
        return True
    
    def get_song_cost_modification(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> int:
        """Rush doesn't modify song costs."""
        return 0
    
    def allows_being_targeted_by(self, target: 'CharacterCard', source: 'CharacterCard', game_state: 'GameState') -> bool:
        """Rush doesn't affect targeting."""
        return True
    
    def execute(self, game_state: 'GameState', targets) -> None:
        """Rush is a passive ability that modifies challenge timing"""
        pass
    
    def __str__(self) -> str:
        return "Rush"