"""Shift keyword ability implementation."""

from typing import TYPE_CHECKING, List, Optional
from ...models.abilities.base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState
    from ...models.cards.character_card import CharacterCard
    from ...models.game.player import Player

class ShiftAbility(KeywordAbility):
    """Shift X - You may pay X ink to play this on top of one of your characters 
    with the same name (instead of paying the character's normal cost)."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure this is a keyword ability
        self.type = AbilityType.KEYWORD
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Shift is a passive ability that provides an alternative play cost"""
        return False
    
    def get_shift_cost(self) -> int:
        """Get the cost to shift this character"""
        return self.value or 0
    
    def can_shift_onto(self, target_character: 'CharacterCard', owner: 'Player') -> bool:
        """Check if this character can shift onto the target character"""
        # Must be same name
        if not hasattr(target_character, 'name') or not hasattr(self, 'character_name'):
            return False
        
        # For now, we'll use a simplified check - in a real implementation,
        # we'd need access to the character this ability belongs to
        return True
    
    def get_valid_shift_targets(self, game_state: 'GameState', player: 'Player') -> List['CharacterCard']:
        """Get all valid targets for shifting this character"""
        valid_targets = []
        
        # Find all characters in play owned by the player with the same base name
        for character in player.characters_in_play:
            if self.can_shift_onto(character, player):
                valid_targets.append(character)
        
        return valid_targets
    
    def provides_alternative_play_cost(self) -> bool:
        """This ability provides an alternative way to play the character"""
        return True
    
    def get_alternative_cost(self) -> int:
        """Get the alternative cost (shift cost) for playing this character"""
        return self.get_shift_cost()
    
    def requires_target_for_play(self) -> bool:
        """Shift requires targeting a character to shift onto"""
        return True
    
    def allows_challenging(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Shift doesn't affect challenging ability."""
        return True
    
    def allows_being_challenged_by(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Shift doesn't affect being challenged."""
        return True
    
    def modifies_challenge_targets(self, attacker: 'CharacterCard', all_potential_targets: list, game_state: 'GameState') -> list:
        """Shift doesn't modify challenge targeting."""
        return all_potential_targets
    
    def allows_singing_song(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> bool:
        """Shift doesn't affect singing."""
        return True
    
    def get_song_cost_modification(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> int:
        """Shift doesn't modify song costs."""
        return 0
    
    def allows_being_targeted_by(self, target: 'CharacterCard', source: 'CharacterCard', game_state: 'GameState') -> bool:
        """Shift doesn't affect targeting."""
        return True
    
    def execute(self, game_state: 'GameState', targets) -> None:
        """Shift doesn't execute, it modifies how the character is played"""
        pass
    
    def __str__(self) -> str:
        return f"Shift {self.value}" if self.value else "Shift"