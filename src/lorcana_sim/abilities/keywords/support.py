"""Support keyword ability implementation."""

from typing import TYPE_CHECKING, List, Optional
from ...models.abilities.base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState
    from ...models.cards.character_card import CharacterCard
    from ...models.game.player import Player
    from ...engine.event_system import GameEvent, EventContext

class SupportAbility(KeywordAbility):
    """Support - Whenever this character quests, you may add their lore value
    to another chosen character's lore value this turn."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure this is a keyword ability
        self.type = AbilityType.KEYWORD
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Support triggers when the character quests"""
        return False  # This is a triggered ability, not an activated one
    
    def triggers_on_quest(self) -> bool:
        """This ability triggers when the character quests"""
        return True
    
    def can_support_character(self, target_character: 'CharacterCard', 
                            supporting_character: 'CharacterCard') -> bool:
        """Check if the supporting character can support the target"""
        # Support can target any other character you control
        # Cannot target self
        return target_character != supporting_character
    
    def get_valid_support_targets(self, game_state: 'GameState', 
                                 player: 'Player', 
                                 supporting_character: 'CharacterCard') -> List['CharacterCard']:
        """Get all valid targets for support"""
        valid_targets = []
        
        for character in player.characters_in_play:
            if self.can_support_character(character, supporting_character):
                valid_targets.append(character)
        
        return valid_targets
    
    def get_support_lore_bonus(self, supporting_character: 'CharacterCard') -> int:
        """Get the lore bonus this character provides when supporting"""
        return getattr(supporting_character, 'lore', 0)
    
    def apply_support_bonus(self, target_character: 'CharacterCard', 
                          supporting_character: 'CharacterCard',
                          game_state: 'GameState') -> None:
        """Apply the support bonus to the target character"""
        bonus = self.get_support_lore_bonus(supporting_character)
        
        # In a full implementation, this would add a temporary lore modifier
        # For now, we'll just document the intended effect
        pass
    
    def modifies_quest_effects(self) -> bool:
        """This ability modifies the effects of questing"""
        return True
    
    def is_optional(self) -> bool:
        """Support is optional - you may choose to use it"""
        return True
    
    def allows_challenging(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Support doesn't affect challenging ability."""
        return True
    
    def allows_being_challenged_by(self, attacker: 'CharacterCard', defender: 'CharacterCard', game_state: 'GameState') -> bool:
        """Support doesn't affect being challenged."""
        return True
    
    def modifies_challenge_targets(self, attacker: 'CharacterCard', all_potential_targets: list, game_state: 'GameState') -> list:
        """Support doesn't modify challenge targeting."""
        return all_potential_targets
    
    def allows_singing_song(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> bool:
        """Support doesn't affect singing."""
        return True
    
    def get_song_cost_modification(self, singer: 'CharacterCard', song: 'ActionCard', game_state: 'GameState') -> int:
        """Support doesn't modify song costs."""
        return 0
    
    def allows_being_targeted_by(self, target: 'CharacterCard', source: 'CharacterCard', game_state: 'GameState') -> bool:
        """Support doesn't affect targeting."""
        return True
    
    # ===== TRIGGERED ABILITY METHODS =====
    
    def get_trigger_events(self) -> List['GameEvent']:
        """Support triggers when this character quests."""
        from ...engine.event_system import GameEvent
        return [GameEvent.CHARACTER_QUESTS]
    
    def should_trigger(self, event_context: 'EventContext') -> bool:
        """Support triggers when this specific character quests."""
        # Support triggers when the character that has this ability quests
        # Use identity check (is) rather than equality check (in) to ensure
        # this exact ability instance is on the questing character
        if not (hasattr(event_context, 'source') and event_context.source):
            return False
        
        questing_character = event_context.source
        if not hasattr(questing_character, 'abilities'):
            return False
        
        # Check if this exact ability instance is on the questing character
        for ability in questing_character.abilities:
            if ability is self:  # identity check, not equality
                return True
        
        return False
    
    def execute_trigger(self, event_context: 'EventContext') -> Optional[str]:
        """Execute Support when this character quests."""
        if not event_context.source or not event_context.game_state:
            return None
        
        supporting_character = event_context.source
        game_state = event_context.game_state
        
        # Find the player who controls this character
        player = None
        for p in game_state.players:
            if supporting_character in p.characters_in_play:
                player = p
                break
        
        if not player:
            return None
        
        # Get valid support targets (other characters controlled by same player)
        valid_targets = self.get_valid_support_targets(game_state, player, supporting_character)
        
        if not valid_targets:
            return f"{supporting_character.name} has no valid support targets"
        
        # For now, auto-select the first valid target (in a full game, player would choose)
        target_character = valid_targets[0]
        lore_bonus = self.get_support_lore_bonus(supporting_character)
        
        # Apply the support bonus (add temporary lore modifier)
        # In a full implementation, this would use a proper temporary effect system
        if hasattr(target_character, 'temporary_lore_bonus'):
            target_character.temporary_lore_bonus += lore_bonus
        else:
            target_character.temporary_lore_bonus = lore_bonus
        
        return f"{supporting_character.name} supported {target_character.name} (+{lore_bonus} lore this turn)"
    
    def execute(self, game_state: 'GameState', targets) -> None:
        """Support executes via trigger system, not direct execution"""
        # This method is kept for backwards compatibility but Support now uses triggers
        pass
    
    def __str__(self) -> str:
        return "Support"