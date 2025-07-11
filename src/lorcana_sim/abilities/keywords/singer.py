"""Singer keyword ability implementation."""

from typing import Optional, TYPE_CHECKING
from ...models.abilities.base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState
    from ...models.cards.action_card import ActionCard

class SingerAbility(KeywordAbility):
    """Singer X - This character counts as cost X to sing songs"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure this is a keyword ability
        self.type = AbilityType.KEYWORD
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Singer is a passive ability, doesn't activate"""
        return False
    
    def get_effective_sing_cost(self) -> int:
        """Get the cost this character counts as for singing"""
        return self.value or 0
    
    def can_sing_song(self, song: 'ActionCard') -> bool:
        """Check if this character can sing the given song"""
        if not song.is_song:
            return False
        
        required_cost = song.singer_cost_reduction
        if required_cost is None:
            return False
        
        return self.get_effective_sing_cost() >= required_cost
    
    def get_cost_reduction(self, song: 'ActionCard') -> int:
        """Get the cost reduction when singing a song"""
        if self.can_sing_song(song):
            return song.cost  # Singer allows singing for free (exert instead of paying)
        return 0
    
    def allows_singing_song(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> bool:
        """Check if this singer can sing the given song."""
        if not song.is_song:
            return False
        
        # Check if this singer meets the requirements for the song
        required_cost = getattr(song, 'singer_cost_reduction', None)
        if required_cost is None:
            return False  # Song doesn't specify singer requirements
        
        return self.get_effective_sing_cost() >= required_cost
    
    def get_song_cost_modification(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> int:
        """Singer allows singing for free (reduces cost to 0)."""
        if self.allows_singing_song(singer, song, game_state):
            return -song.cost  # Reduce cost to 0
        return 0  # No modification if can't sing
    
    def allows_challenging(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Singer doesn't affect challenging ability."""
        return True
    
    def allows_being_challenged_by(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Singer doesn't affect being challenged."""
        return True
    
    def modifies_challenge_targets(self, attacker: 'CharacterCard', all_potential_targets: list, game_state: 'GameState') -> list:
        """Singer doesn't modify challenge targeting."""
        return all_potential_targets
    
    def allows_being_targeted_by(self, target: 'CharacterCard', source: 'CharacterCard', game_state: 'GameState') -> bool:
        """Singer doesn't affect targeting."""
        return True
    
    def execute(self, game_state: 'GameState', targets) -> None:
        """Singer doesn't execute, it modifies song-playing rules"""
        pass
    
    def __str__(self) -> str:
        return f"Singer {self.value}" if self.value else "Singer"