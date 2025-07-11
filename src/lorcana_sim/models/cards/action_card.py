"""Action card implementation."""

from dataclasses import dataclass, field
from typing import List, Optional

from .base_card import Card


@dataclass
class ActionCard(Card):
    """Represents an action card (includes songs) in Lorcana."""
    
    # Action effects (derived from abilities)
    effects: List[str] = field(default_factory=list)
    
    @property
    def is_song(self) -> bool:
        """Check if this action is a song (has singer cost reduction)."""
        # Check abilities for singer cost text
        for ability in self.abilities:
            if "sing this song" in ability.effect.lower():
                return True
        return False
    
    @property
    def singer_cost_reduction(self) -> Optional[int]:
        """Get the cost reduction for singers (if this is a song)."""
        if not self.is_song:
            return None
        
        # Parse from ability text like "cost 2 or more can sing..."
        for ability in self.abilities:
            effect_text = ability.effect.lower()
            if "cost" in effect_text and "sing" in effect_text:
                # Try to extract the cost from text like "cost 2 or more"
                words = effect_text.split()
                for i, word in enumerate(words):
                    if word == "cost" and i + 1 < len(words):
                        try:
                            return int(words[i + 1])
                        except ValueError:
                            continue
        return None
    
    def can_be_sung_by_character(self, character_strength: int) -> bool:
        """Check if a character with given strength can sing this song."""
        if not self.is_song:
            return False
        
        required_strength = self.singer_cost_reduction
        if required_strength is None:
            return False
        
        return character_strength >= required_strength
    
    def get_effective_cost(self, is_being_sung: bool = False) -> int:
        """Get the effective cost to play this action."""
        if is_being_sung and self.is_song:
            reduction = self.singer_cost_reduction or 0
            return max(0, self.cost - reduction)
        return self.cost
    
    def __str__(self) -> str:
        """String representation."""
        song_indicator = " [SONG]" if self.is_song else ""
        return f"{self.full_name}{song_indicator}"