"""Base ability classes for Lorcana cards."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..game.game_state import GameState


class AbilityType(Enum):
    """Types of abilities in Lorcana."""
    KEYWORD = "keyword"
    TRIGGERED = "triggered"
    STATIC = "static"
    ACTIVATED = "activated"


@dataclass
class Ability:
    """Base class for all card abilities."""
    name: str
    type: AbilityType
    effect: str
    full_text: str
    
    def can_activate(self, game_state: "GameState") -> bool:
        """Check if this ability can be activated (override in subclasses)."""
        return False
    
    def execute(self, game_state: "GameState", targets: List[Any]) -> None:
        """Execute this ability (override in subclasses)."""
        raise NotImplementedError("Ability execution not implemented")
    
    def __str__(self) -> str:
        """String representation of the ability."""
        return f"{self.name}: {self.effect}"


@dataclass
class KeywordAbility(Ability):
    """Keyword abilities like Shift, Evasive, etc."""
    keyword: str
    value: Optional[int] = None  # For abilities like "Singer 5"
    
    def __post_init__(self) -> None:
        """Set ability type."""
        self.type = AbilityType.KEYWORD


@dataclass
class StaticAbility(Ability):
    """Always-active abilities."""
    
    def __post_init__(self) -> None:
        """Set ability type."""
        self.type = AbilityType.STATIC


@dataclass
class TriggeredAbility(Ability):
    """Abilities that trigger on specific events."""
    trigger_condition: str = ""  # Will be structured later
    
    def __post_init__(self) -> None:
        """Set ability type."""
        self.type = AbilityType.TRIGGERED


@dataclass
class ActivatedAbility(Ability):
    """Abilities that require manual activation and costs."""
    costs: List[str] = field(default_factory=list)  # Will be structured later
    
    def __post_init__(self) -> None:
        """Set ability type."""
        self.type = AbilityType.ACTIVATED