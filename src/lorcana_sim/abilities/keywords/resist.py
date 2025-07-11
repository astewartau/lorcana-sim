"""Resist keyword ability implementation."""

from typing import TYPE_CHECKING
from ...models.abilities.base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState

class ResistAbility(KeywordAbility):
    """Resist +X - Damage dealt to this character is reduced by X."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure this is a keyword ability
        self.type = AbilityType.KEYWORD
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Resist is a passive ability, doesn't activate"""
        return False
    
    def get_damage_reduction(self) -> int:
        """Get the amount of damage reduction this character has"""
        return self.value or 0
    
    def reduce_incoming_damage(self, damage_amount: int) -> int:
        """Calculate the reduced damage amount after applying resist"""
        reduction = self.get_damage_reduction()
        reduced_damage = max(0, damage_amount - reduction)
        return reduced_damage
    
    def modifies_damage_calculation(self) -> bool:
        """This ability modifies damage calculations"""
        return True
    
    def is_passive_damage_modifier(self) -> bool:
        """Resist is a passive ability that modifies incoming damage"""
        return True
    
    def applies_to_all_damage_sources(self) -> bool:
        """Resist applies to damage from challenges, abilities, and other sources"""
        return True
    
    def allows_challenging(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Resist doesn't affect challenging ability."""
        return True
    
    def allows_being_challenged_by(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Resist doesn't affect being challenged."""
        return True
    
    def modifies_challenge_targets(self, attacker: 'CharacterCard', all_potential_targets: list, game_state: 'GameState') -> list:
        """Resist doesn't modify challenge targeting."""
        return all_potential_targets
    
    def allows_singing_song(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> bool:
        """Resist doesn't affect singing."""
        return True
    
    def get_song_cost_modification(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> int:
        """Resist doesn't modify song costs."""
        return 0
    
    def allows_being_targeted_by(self, target: 'CharacterCard', source: 'CharacterCard', game_state: 'GameState') -> bool:
        """Resist doesn't affect targeting."""
        return True
    
    def execute(self, game_state: 'GameState', targets) -> None:
        """Resist is a passive ability that modifies damage calculations"""
        pass
    
    def __str__(self) -> str:
        if self.value:
            return f"Resist +{self.value}"
        return "Resist"