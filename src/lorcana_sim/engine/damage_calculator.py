"""Damage calculation system that integrates with abilities."""

from enum import Enum
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..models.cards.character_card import CharacterCard
    from ..models.game.game_state import GameState
    from ..models.abilities.base_ability import BaseAbility


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
        
        # Apply damage modifiers from source's abilities (if any)
        if source:
            current_damage = self._apply_source_damage_modifiers(
                source, target, current_damage, damage_type
            )
        
        # Apply global damage modifiers (from other characters, items, etc.)
        current_damage = self._apply_global_damage_modifiers(
            source, target, current_damage, damage_type
        )
        
        # Damage cannot go below 0
        return max(0, current_damage)
    
    def _apply_target_damage_modifiers(self, 
                                     source: Optional['CharacterCard'],
                                     target: 'CharacterCard', 
                                     damage: int, 
                                     damage_type: DamageType) -> int:
        """Apply damage modifiers from the target's abilities."""
        current_damage = damage
        
        for ability in target.abilities:
            if hasattr(ability, 'modifies_damage_calculation') and ability.modifies_damage_calculation():
                # Check if this ability applies to this damage type
                if self._ability_applies_to_damage_type(ability, damage_type):
                    if hasattr(ability, 'reduce_incoming_damage'):
                        # Apply damage reduction (like Resist)
                        current_damage = ability.reduce_incoming_damage(current_damage)
                    elif hasattr(ability, 'modify_incoming_damage'):
                        # Apply custom damage modification
                        current_damage = ability.modify_incoming_damage(
                            source, target, current_damage, damage_type, self.game_state
                        )
        
        return current_damage
    
    def _apply_source_damage_modifiers(self, 
                                     source: 'CharacterCard',
                                     target: 'CharacterCard', 
                                     damage: int, 
                                     damage_type: DamageType) -> int:
        """Apply damage modifiers from the source's abilities."""
        current_damage = damage
        
        for ability in source.abilities:
            if hasattr(ability, 'modifies_damage_calculation') and ability.modifies_damage_calculation():
                if hasattr(ability, 'modify_outgoing_damage'):
                    # Apply outgoing damage modification
                    current_damage = ability.modify_outgoing_damage(
                        source, target, current_damage, damage_type, self.game_state
                    )
        
        return current_damage
    
    def _apply_global_damage_modifiers(self, 
                                     source: Optional['CharacterCard'],
                                     target: 'CharacterCard', 
                                     damage: int, 
                                     damage_type: DamageType) -> int:
        """Apply damage modifiers from other sources (items, global effects, etc.)."""
        # For now, no global modifiers
        # Future abilities could modify damage globally
        return damage
    
    def _ability_applies_to_damage_type(self, ability: 'BaseAbility', damage_type: DamageType) -> bool:
        """Check if an ability applies to the given damage type."""
        # Most abilities apply to all damage types unless specified otherwise
        if hasattr(ability, 'applies_to_damage_type'):
            return ability.applies_to_damage_type(damage_type)
        
        # Default: ability applies to all damage types
        return True
    
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
        
        # Track target modifiers
        for ability in target.abilities:
            if hasattr(ability, 'modifies_damage_calculation') and ability.modifies_damage_calculation():
                if self._ability_applies_to_damage_type(ability, damage_type):
                    if hasattr(ability, 'reduce_incoming_damage'):
                        original = current_damage
                        current_damage = ability.reduce_incoming_damage(current_damage)
                        if current_damage != original:
                            modifiers.append({
                                'ability': str(ability),
                                'type': 'damage_reduction',
                                'change': original - current_damage,
                                'from': original,
                                'to': current_damage
                            })
        
        final_damage = max(0, current_damage)
        
        return {
            'base_damage': base_damage,
            'final_damage': final_damage,
            'modifiers': modifiers,
            'prevented': final_damage == 0 and base_damage > 0
        }