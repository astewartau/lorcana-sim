"""Item card implementation."""

from dataclasses import dataclass
from typing import Optional

from .base_card import Card


@dataclass
class ItemCard(Card):
    """Represents an item card in Lorcana."""
    
    # Runtime State
    attached_to: Optional[str] = None  # Character this is attached to (if any)
    
    @property
    def is_permanent(self) -> bool:
        """Check if item stays in play (vs single-use)."""
        # Determine from ability text - items with ongoing effects typically stay in play
        for ability in self.abilities:
            effect_text = ability.effect.lower()
            # Look for indicators of permanent effects
            if any(keyword in effect_text for keyword in ["while", "as long as", "whenever", "during"]):
                return True
        # Default to permanent for now
        return True
    
    @property
    def is_attachment(self) -> bool:
        """Check if this item attaches to characters."""
        # Look for attachment indicators in ability text
        for ability in self.abilities:
            effect_text = ability.effect.lower()
            if any(keyword in effect_text for keyword in ["attach", "equipped", "bearer"]):
                return True
        return False
    
    def attach_to_character(self, character_name: str) -> None:
        """Attach this item to a character."""
        if not self.is_attachment:
            raise ValueError(f"Item {self.full_name} cannot be attached to characters")
        self.attached_to = character_name
    
    def detach(self) -> None:
        """Detach this item from its character."""
        self.attached_to = None
    
    def is_attached(self) -> bool:
        """Check if this item is currently attached to a character."""
        return self.attached_to is not None
    
    def __str__(self) -> str:
        """String representation."""
        attachment_info = ""
        if self.is_attached():
            attachment_info = f" [attached to {self.attached_to}]"
        elif self.is_attachment:
            attachment_info = " [unattached]"
        
        return f"{self.full_name}{attachment_info}"