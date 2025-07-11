"""Location card implementation."""

from dataclasses import dataclass, field
from typing import List, Optional

from .base_card import Card


@dataclass
class LocationCard(Card):
    """Represents a location card in Lorcana."""
    
    # Location Properties (from JSON)
    move_cost: int = 0
    willpower: int = 0
    lore: Optional[int] = None  # Some locations provide lore
    
    # Runtime State
    damage: int = 0
    characters: List[str] = field(default_factory=list)  # Character names at this location
    
    def __post_init__(self) -> None:
        """Validate location card data after creation."""
        super().__post_init__()
        
        if self.move_cost < 0:
            raise ValueError(f"Location move cost cannot be negative: {self.move_cost}")
        if self.willpower < 0:
            raise ValueError(f"Location willpower cannot be negative: {self.willpower}")
        if self.damage < 0:
            raise ValueError(f"Location damage cannot be negative: {self.damage}")
        if self.lore is not None and self.lore < 0:
            raise ValueError(f"Location lore cannot be negative: {self.lore}")
    
    @property
    def is_destroyed(self) -> bool:
        """Check if location is destroyed (damage >= willpower)."""
        return self.damage >= self.willpower
    
    @property
    def current_willpower(self) -> int:
        """Get current willpower (may be modified by abilities later)."""
        # TODO: Apply ability modifiers
        return self.willpower
    
    @property
    def provides_lore(self) -> bool:
        """Check if this location provides lore when quested at."""
        return self.lore is not None and self.lore > 0
    
    def deal_damage(self, amount: int) -> None:
        """Deal damage to this location."""
        if amount < 0:
            raise ValueError("Damage amount cannot be negative")
        self.damage += amount
    
    def heal_damage(self, amount: int) -> None:
        """Heal damage from this location."""
        if amount < 0:
            raise ValueError("Heal amount cannot be negative")
        self.damage = max(0, self.damage - amount)
    
    def add_character(self, character_name: str) -> None:
        """Add a character to this location."""
        if character_name not in self.characters:
            self.characters.append(character_name)
    
    def remove_character(self, character_name: str) -> None:
        """Remove a character from this location."""
        if character_name in self.characters:
            self.characters.remove(character_name)
    
    def has_character(self, character_name: str) -> bool:
        """Check if a character is at this location."""
        return character_name in self.characters
    
    def get_character_count(self) -> int:
        """Get the number of characters at this location."""
        return len(self.characters)
    
    def can_move_character_here(self, player_available_ink: int) -> bool:
        """Check if a player can afford to move a character here."""
        return player_available_ink >= self.move_cost
    
    def __str__(self) -> str:
        """String representation."""
        status_parts = []
        
        if self.damage > 0:
            status_parts.append(f"{self.damage} damage")
        
        if self.characters:
            character_count = len(self.characters)
            status_parts.append(f"{character_count} character{'s' if character_count != 1 else ''}")
        
        status = f" [{', '.join(status_parts)}]" if status_parts else ""
        lore_info = f" (provides {self.lore} lore)" if self.provides_lore else ""
        
        return f"{self.full_name}{lore_info}{status}"