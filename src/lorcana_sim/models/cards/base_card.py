"""Base card class and common enums for Lorcana cards."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class CardColor(Enum):
    """Card colors/ink types in Lorcana."""
    AMBER = "Amber"
    AMETHYST = "Amethyst"
    EMERALD = "Emerald"
    RUBY = "Ruby"
    SAPPHIRE = "Sapphire"
    STEEL = "Steel"


class Rarity(Enum):
    """Card rarities in Lorcana."""
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    SUPER_RARE = "Super Rare"
    LEGENDARY = "Legendary"
    SPECIAL = "Special"
    ENCHANTED = "Enchanted"


@dataclass
class Card:
    """Base class for all Lorcana cards."""
    
    # Core Identity
    id: int
    name: str
    version: Optional[str]
    full_name: str
    
    # Game Properties
    cost: int
    color: CardColor
    inkwell: bool
    
    # Metadata
    rarity: Rarity
    set_code: str
    number: int
    story: str
    
    # Text
    flavor_text: Optional[str] = None
    full_text: str = ""
    
    # Visual (optional for simulation)
    artists: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate card data after creation."""
        if self.cost < 0:
            raise ValueError(f"Card cost cannot be negative: {self.cost}")
        if not self.name:
            raise ValueError("Card name cannot be empty")
        if not self.full_name:
            self.full_name = f"{self.name} - {self.version}" if self.version else self.name
    
    @property
    def card_type(self) -> str:
        """Get the card type (implemented by subclasses)."""
        class_name = self.__class__.__name__
        if class_name == "Card":
            return "Card"
        return class_name.replace("Card", "")
    
    def can_be_inked(self) -> bool:
        """Check if this card can be played as ink."""
        return self.inkwell
    
    def __str__(self) -> str:
        """String representation of the card."""
        return self.full_name
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}(id={self.id}, name='{self.full_name}', cost={self.cost})"