"""Character card implementation."""

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from .base_card import Card

if TYPE_CHECKING:
    from ...engine.damage_calculator import DamageCalculator, DamageType
    from ..game.game_state import GameState


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
    location: Optional[str] = None
    turn_played: Optional[int] = None  # Track when character was played for ink drying
    
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
        """Get current strength (may be modified by abilities later)."""
        # TODO: Apply ability modifiers
        return self.strength
    
    @property
    def current_willpower(self) -> int:
        """Get current willpower (may be modified by abilities later)."""
        # TODO: Apply ability modifiers
        return self.willpower
    
    @property
    def current_lore(self) -> int:
        """Get current lore value (may be modified by abilities later)."""
        # TODO: Apply ability modifiers
        return self.lore
    
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
        
        # If no damage calculator provided, use simple damage
        if damage_calculator is None or damage_type is None:
            self.damage += amount
            return amount
        
        # Calculate final damage with ability modifications
        final_damage = damage_calculator.calculate_damage(source, self, amount, damage_type)
        
        # Apply the calculated damage
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
        """Ready this character."""
        self.exerted = False
    
    def is_dry(self, current_turn: int) -> bool:
        """Check if character's ink is dry (can act normally).
        
        Characters have wet ink when played and cannot quest or challenge
        until the start of their owner's next turn (when ink dries).
        """
        if self.turn_played is None:
            return True  # Character wasn't played this game (already dry)
        
        # Ink dries at start of owner's next turn
        return current_turn > self.turn_played
    
    def has_rush_ability(self) -> bool:
        """Check if character has Rush ability."""
        from ...abilities.keywords.rush import RushAbility
        return any(isinstance(ability, RushAbility) for ability in self.abilities)
    
    def can_quest(self, current_turn: int) -> bool:
        """Check if this character can quest.
        
        Questing requires dry ink - Rush does not affect questing.
        """
        return not self.exerted and self.is_alive and self.is_dry(current_turn)
    
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
        return self.is_dry(current_turn)
    
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