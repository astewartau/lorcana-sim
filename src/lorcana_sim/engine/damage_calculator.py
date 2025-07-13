"""Damage calculation system that integrates with abilities."""

from enum import Enum
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..models.cards.character_card import CharacterCard
    from ..models.game.game_state import GameState


class DamageType(Enum):
    """Types of damage that can be dealt."""
    CHALLENGE = "challenge"      # Damage from character challenges
    ABILITY = "ability"          # Damage from ability effects
    DIRECT = "direct"           # Direct damage (unmodifiable)


class DamageCalculator:
    """Calculates damage with ability modifications."""
    
    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state
    
    def calculate_damage(self, 
                        source: Optional['CharacterCard'], 
                        target: 'CharacterCard', 
                        base_damage: int, 
                        damage_type: DamageType) -> int:
        """Calculate final damage after ability modifications.
        
        Args:
            source: The character dealing damage (None for non-character sources)
            target: The character receiving damage
            base_damage: The base amount of damage before modifications
            damage_type: The type of damage being dealt
            
        Returns:
            Final damage amount after all ability modifications
        """
        if base_damage <= 0:
            return 0
        
        current_damage = base_damage
        
        # Apply damage modifiers from target's abilities (like Resist)
        current_damage = self._apply_target_damage_modifiers(
            source, target, current_damage, damage_type
        )
        
        # TODO: Apply damage modifiers from source's abilities (if any)
        # Currently no source abilities modify outgoing damage in the new framework
        
        # TODO: Apply global damage modifiers (from other characters, items, etc.)
        # Currently no global damage modifiers in the new framework
        
        # Damage cannot go below 0
        return max(0, current_damage)
    
    def _apply_target_damage_modifiers(self, 
                                     source: Optional['CharacterCard'],
                                     target: 'CharacterCard', 
                                     damage: int, 
                                     damage_type: DamageType) -> int:
        """Apply damage modifiers from composable abilities via event system."""
        # Damage modification is now handled through the event system
        # and composable abilities when CHARACTER_TAKES_DAMAGE event is triggered
        # This method is kept for compatibility but does minimal processing
        return max(0, damage)
    
    def preview_damage(self, 
                      source: Optional['CharacterCard'], 
                      target: 'CharacterCard', 
                      base_damage: int, 
                      damage_type: DamageType) -> dict:
        """Preview damage calculation without applying it.
        
        Returns a dictionary with breakdown of damage calculation.
        """
        if base_damage <= 0:
            return {
                'base_damage': base_damage,
                'final_damage': 0,
                'modifiers': [],
                'prevented': False
            }
        
        modifiers = []
        current_damage = base_damage
        
        # Track target modifiers - composable abilities handle this via events
        # For preview, we don't need to modify damage as events will handle it
        
        final_damage = max(0, current_damage)
        
        return {
            'base_damage': base_damage,
            'final_damage': final_damage,
            'modifiers': modifiers,
            'prevented': final_damage == 0 and base_damage > 0
        }