"""Character card implementation."""

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING, Dict, Any, Tuple

from .base_card import Card

if TYPE_CHECKING:
    from ..game.game_state import GameState
    from ...engine.event_system import GameEventManager
    from ..abilities.composable import ComposableAbility
    from ..game.player import Player


@dataclass
class CharacterCard(Card):
    """Represents a character card in Lorcana."""
    
    # Combat Stats (from JSON)
    strength: int = 0
    willpower: int = 0
    lore: int = 0
    
    # Character Classification
    subtypes: List[str] = field(default_factory=list)
    
    # Runtime State (not from JSON - game state)
    damage: int = 0
    exerted: bool = False
    is_dry: bool = False  # Ink drying status - False means wet ink (can't act), True means dry (can act)
    location: Optional[str] = None
    
    def __setattr__(self, name, value):
        if name == 'damage' and hasattr(self, 'damage'):
            old_damage = self.damage
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)
    
    # Composable Ability Integration
    composable_abilities: List['ComposableAbility'] = field(default_factory=list)
    controller: Optional['Player'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    
    def __post_init__(self) -> None:
        """Validate character card data after creation."""
        super().__post_init__()
        
        if self.strength < 0:
            raise ValueError(f"Character strength cannot be negative: {self.strength}")
        if self.willpower < 0:
            raise ValueError(f"Character willpower cannot be negative: {self.willpower}")
        if self.lore < 0:
            raise ValueError(f"Character lore cannot be negative: {self.lore}")
        if self.damage < 0:
            raise ValueError(f"Character damage cannot be negative: {self.damage}")
    
    @property
    def is_alive(self) -> bool:
        """Check if character is still alive (damage < willpower)."""
        return self.damage < self.willpower
    
    @property
    def current_strength(self) -> int:
        """Get current strength including ability modifiers."""
        return max(0, self.strength)
    
    @property
    def current_willpower(self) -> int:
        """Get current willpower including ability modifiers and damage."""
        return self.willpower - self.damage
    
    @property
    def current_lore(self) -> int:
        """Get current lore value including ability modifiers."""
        return max(0, self.lore)
    
    
    def deal_damage(self, 
                   amount: int, 
                   source: Optional['CharacterCard'] = None,
                   damage_calculator: Optional['DamageCalculator'] = None,
                   damage_type: Optional['DamageType'] = None) -> int:
        """Deal damage to this character with ability modifications.
        
        Args:
            amount: Base damage amount
            source: Character dealing the damage (None for non-character sources)
            damage_calculator: Calculator to apply ability modifiers
            damage_type: Type of damage being dealt
            
        Returns:
            Actual damage dealt after ability modifications
        """
        if amount < 0:
            raise ValueError("Damage amount cannot be negative")
        
        if amount == 0:
            return 0
        
        # Note: This method is now primarily for backwards compatibility.
        # New code should use DamageEffect for proper event handling and damage modification.
        # Apply damage directly - modifications happen through events
        final_damage = max(0, amount)
        self.damage += final_damage
        
        return final_damage
    
    def heal_damage(self, amount: int) -> None:
        """Heal damage from this character."""
        if amount < 0:
            raise ValueError("Heal amount cannot be negative")
        self.damage = max(0, self.damage - amount)
    
    def exert(self) -> None:
        """Exert this character."""
        self.exerted = True
    
    def ready(self) -> None:
        """Ready this character using effect-based system."""
        from ..abilities.composable.effects import ReadyCharacter
        ready_effect = ReadyCharacter(self)
        ready_effect.apply(self, {'reason': 'manual_ready'})
    
    
    def has_rush_ability(self) -> bool:
        """Check if character has Rush ability."""
        # Check composable abilities for Rush
        for ability in self.composable_abilities:
            if 'rush' in ability.name.lower():
                return True
        # Check metadata set by Rush ability
        return self.metadata.get('can_challenge_with_wet_ink', False)
    
    def has_evasive_ability(self) -> bool:
        """Check if character has Evasive ability."""
        # Check composable abilities for Evasive
        for ability in self.composable_abilities:
            if 'evasive' in ability.name.lower():
                return True
        # Check metadata set by temporary effects
        return self.metadata.get('has_evasive', False)
    
    def can_quest(self, current_turn: int) -> bool:
        """Check if this character can quest.
        
        Questing requires dry ink - Rush does not affect questing.
        """
        return not self.exerted and self.is_alive and self.is_dry
    
    def can_challenge(self, current_turn: int) -> bool:
        """Check if this character can challenge.
        
        Challenging normally requires dry ink, but Rush bypasses this restriction.
        """
        if not self.is_alive or self.exerted:
            return False
        
        # Rush bypasses ink drying requirement for challenges
        if self.has_rush_ability():
            return True
        
        # Normal characters need dry ink to challenge
        return self.is_dry
    
    def has_subtype(self, subtype: str) -> bool:
        """Check if this character has a specific subtype."""
        return subtype in self.subtypes
    
    def get_origin_type(self) -> Optional[str]:
        """Get the origin type (Storyborn, Dreamborn, Floodborn)."""
        origin_types = {"Storyborn", "Dreamborn", "Floodborn"}
        for subtype in self.subtypes:
            if subtype in origin_types:
                return subtype
        return None
    
    def __str__(self) -> str:
        """String representation including stats."""
        status = ""
        if self.exerted:
            status += " [EXERTED]"
        if self.damage > 0:
            status += f" [{self.damage} damage]"
        return f"{self.full_name} ({self.strength}/{self.willpower}){status}"
    
    def __repr__(self) -> str:
        """Use the same representation as __str__ for cleaner output in collections."""
        return self.__str__()
    
    
    def add_temporary_modifier(self, **kwargs) -> None:
        """Add temporary modifiers to this character."""
        if 'evasive' in kwargs:
            self.metadata['has_evasive'] = kwargs['evasive']
        if 'rush' in kwargs:
            self.metadata['has_rush'] = kwargs['rush']
        if 'bodyguard' in kwargs:
            self.metadata['has_bodyguard'] = kwargs['bodyguard']
        if 'ward' in kwargs:
            self.metadata['has_ward'] = kwargs['ward']
    
    
    # Composable Ability Integration Methods
    def register_composable_abilities(self, event_manager: 'GameEventManager') -> None:
        """Register all composable abilities with the event manager."""
        for ability in self.composable_abilities:
            ability.register_with_event_manager(event_manager)
    
    def unregister_composable_abilities(self, event_manager: 'GameEventManager') -> None:
        """Unregister all composable abilities from the event manager."""
        for ability in self.composable_abilities:
            ability.unregister_from_event_manager()
    
    def add_composable_ability(self, ability: 'ComposableAbility') -> None:
        """Add a composable ability to this character."""
        self.composable_abilities.append(ability)
    
    
    def get_active_abilities(self, game_state: Optional['GameState'] = None) -> List[str]:
        """Get all currently active abilities including conditionally-granted ones.
        
        Args:
            game_state: Current game state for context-aware abilities
            
        Returns:
            List of ability names currently active on this character
        """
        # Start with permanent abilities
        abilities = []
        
        # Add named abilities
        for ability in self.composable_abilities:
            if hasattr(ability, 'name') and ability.name:
                abilities.append(ability.name)
        
        # Add conditionally-granted keyword abilities based on metadata
        keyword_properties = {
            'has_evasive': 'Evasive',
            'has_rush': 'Rush',
            'has_ward': 'Ward',
            'has_bodyguard': 'Bodyguard',
            'has_challenger': 'Challenger',
            'has_resist': lambda: f"Resist {self.metadata.get('resist_value', 1)}",
            'has_support': 'Support'
        }
        
        for property_key, ability_name in keyword_properties.items():
            if self.metadata.get(property_key, False):
                # Handle dynamic ability names (like Resist X)
                if callable(ability_name):
                    abilities.append(ability_name())
                else:
                    abilities.append(ability_name)
        
        return abilities

    def get_display_info(self, game_state: Optional['GameState'] = None) -> Dict[str, Any]:
        """Get comprehensive display information for this character.
        
        Returns dict with:
        - name: Character name
        - stats: Current strength/willpower
        - abilities: List of active abilities
        - status: Exerted, damage, etc.
        """
        return {
            'name': self.full_name,
            'stats': f"{self.strength}/{self.willpower}",
            'abilities': self.get_active_abilities(game_state),
            'status': {
                'exerted': self.exerted,
                'damage': self.damage,
                'dry': self.is_dry
            }
        }