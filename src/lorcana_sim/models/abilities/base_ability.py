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
    
    # ===== VALIDATION DELEGATION METHODS =====
    # These methods allow abilities to participate in game rule validation
    
    def allows_being_challenged_by(self, attacker: 'Any', defender: 'Any', game_state: 'GameState') -> bool:
        """Check if this ability allows the defender to be challenged by the attacker.
        
        Return False to prevent the challenge, True to allow it.
        Default: Allow all challenges (no restriction).
        """
        return True
    
    def allows_challenging(self, attacker: 'Any', defender: 'Any', game_state: 'GameState') -> bool:
        """Check if this ability allows the attacker to challenge the defender.
        
        Return False to prevent the challenge, True to allow it.
        Default: Allow all challenges (no restriction).
        """
        return True
    
    def modifies_challenge_targets(self, attacker: 'Any', all_potential_targets: List['Any'], game_state: 'GameState') -> List['Any']:
        """Modify the list of valid challenge targets.
        
        This is for abilities like Bodyguard that change targeting rules.
        Return the filtered list of valid targets.
        Default: Return all targets unchanged.
        """
        return all_potential_targets
    
    def allows_singing_song(self, singer: 'Any', song: 'Any', game_state: 'GameState') -> bool:
        """Check if this ability allows the singer to sing the song.
        
        Return False to prevent singing, True to allow it.
        Default: Allow all singing (no restriction).
        """
        return True
    
    def get_song_cost_modification(self, singer: 'Any', song: 'Any', game_state: 'GameState') -> int:
        """Get the cost modification this ability provides for singing a song.
        
        Return negative number for cost reduction, positive for cost increase.
        Default: No cost modification.
        """
        return 0
    
    def allows_being_targeted_by(self, target: 'Any', source: 'Any', game_state: 'GameState') -> bool:
        """Check if this ability allows the target to be targeted by the source.
        
        This covers ability targeting, not challenges.
        Return False to prevent targeting, True to allow it.
        Default: Allow all targeting (no restriction).
        """
        return True
    
    # ===== TRIGGERED ABILITY METHODS =====
    # These methods support the event-driven trigger system
    
    def get_trigger_events(self) -> List['Any']:
        """Get the list of game events this ability listens for.
        
        Return empty list for non-triggered abilities.
        Override in subclasses to specify which events trigger this ability.
        """
        return []
    
    def should_trigger(self, event_context: 'Any') -> bool:
        """Check if this ability should trigger for the given event context.
        
        This allows for fine-grained control beyond just event type.
        For example, "when this character quests" vs "when any character quests".
        Default: Don't trigger (for non-triggered abilities).
        """
        return False
    
    def execute_trigger(self, event_context: 'Any') -> Optional[str]:
        """Execute this ability in response to a trigger event.
        
        Return a string describing what happened, or None.
        Default: Do nothing (for non-triggered abilities).
        """
        return None
    
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