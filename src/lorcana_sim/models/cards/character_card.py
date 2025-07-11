"""Character card implementation."""

from dataclasses import dataclass, field
from typing import List, Optional

from .base_card import Card


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
    
    def deal_damage(self, amount: int) -> None:
        """Deal damage to this character."""
        if amount < 0:
            raise ValueError("Damage amount cannot be negative")
        self.damage += amount
    
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
    
    def can_quest(self) -> bool:
        """Check if this character can quest."""
        return not self.exerted and self.is_alive
    
    def can_challenge(self) -> bool:
        """Check if this character can challenge."""
        return not self.exerted and self.is_alive
    
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