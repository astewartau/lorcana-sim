"""Ward keyword ability implementation."""

from typing import TYPE_CHECKING
from ...models.abilities.base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState
    from ...models.cards.character_card import CharacterCard
    from ...models.game.player import Player

class WardAbility(KeywordAbility):
    """Ward - Opponents can't choose this character except to challenge."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure this is a keyword ability
        self.type = AbilityType.KEYWORD
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Ward is a passive ability, doesn't activate"""
        return False
    
    def can_be_targeted_by_opponent(self, effect_source: 'CharacterCard', 
                                  targeting_player: 'Player',
                                  owner: 'Player') -> bool:
        """Check if this character can be targeted by an opponent's effect"""
        # If the targeting player is an opponent (not the owner)
        if targeting_player != owner:
            return False  # Opponents can't target this character with abilities
        return True  # Owner can still target their own character
    
    def can_be_challenged_by_opponent(self, challenger: 'CharacterCard',
                                    challenging_player: 'Player',
                                    owner: 'Player') -> bool:
        """Check if this character can be challenged by an opponent"""
        # Opponents CAN challenge this character (Ward doesn't prevent challenges)
        return True
    
    def protects_from_targeting(self) -> bool:
        """This ability protects from opponent targeting (except challenges)"""
        return True
    
    def allows_challenges(self) -> bool:
        """Ward still allows the character to be challenged"""
        return True
    
    def allows_owner_targeting(self) -> bool:
        """The owner can still target their own character with Ward"""
        return True
    
    def modifies_targeting_rules(self) -> bool:
        """This ability modifies targeting rules for abilities"""
        return True
    
    def allows_being_targeted_by(self, target: 'CharacterCard', source: 'CharacterCard', game_state: 'GameState') -> bool:
        """Ward prevents opponents from targeting this character (except for challenges)."""
        # For now, we'll use a simple check - in a full implementation we'd check player ownership
        target_owner = getattr(target, 'owner', None)
        source_owner = getattr(source, 'owner', None)
        
        # If we can determine ownership, prevent opponent targeting
        if target_owner and source_owner and target_owner != source_owner:
            return False  # Opponents can't target ward characters with abilities
        
        return True  # Owner can target their own ward character
    
    def allows_challenging(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Ward doesn't affect challenging ability."""
        return True
    
    def allows_being_challenged_by(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Ward allows being challenged by anyone."""
        return True
    
    def modifies_challenge_targets(self, attacker: 'CharacterCard', all_potential_targets: list, game_state: 'GameState') -> list:
        """Ward doesn't modify challenge targeting."""
        return all_potential_targets
    
    def allows_singing_song(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> bool:
        """Ward doesn't affect singing."""
        return True
    
    def get_song_cost_modification(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> int:
        """Ward doesn't modify song costs."""
        return 0
    
    def execute(self, game_state: 'GameState', targets) -> None:
        """Ward is a passive ability that modifies targeting rules"""
        pass
    
    def __str__(self) -> str:
        return "Ward"