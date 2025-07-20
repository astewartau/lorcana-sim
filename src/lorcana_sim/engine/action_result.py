"""Action result system for structured game engine responses."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
# NOTE: GameAction import removed in Phase 4


class ActionResultType(Enum):
    """Types of action results."""
    # Phase transitions
    PHASE_ADVANCED = "phase_advanced"
    TURN_ENDED = "turn_ended" 
    TURN_BEGAN = "turn_began"
    
    # Card actions
    INK_PLAYED = "ink_played"
    CHARACTER_PLAYED = "character_played"
    ACTION_PLAYED = "action_played"
    ITEM_PLAYED = "item_played"
    CHARACTER_QUESTED = "character_quested"
    CHARACTER_CHALLENGED = "character_challenged"
    SONG_SUNG = "song_sung"
    
    # State changes
    CHARACTERS_READIED = "characters_readied"
    CARD_DRAWN = "card_drawn"
    ABILITIES_TRIGGERED = "abilities_triggered"
    CHARACTER_BANISHED = "character_banished"
    
    # Errors
    ACTION_FAILED = "action_failed"


@dataclass
class ActionResult:
    """Structured result from executing a game action."""
    success: bool
    action_type: str  # NOTE: Changed from GameAction to string in Phase 4
    result_type: ActionResultType
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    @classmethod
    def success_result(cls, action_type: str, result_type: ActionResultType, **data) -> 'ActionResult':
        """Create a successful action result."""
        return cls(
            success=True,
            action_type=action_type,
            result_type=result_type,
            data=data
        )
    
    @classmethod
    def failure_result(cls, action_type: str, error_message: str) -> 'ActionResult':
        """Create a failed action result."""
        return cls(
            success=False,
            action_type=action_type,
            result_type=ActionResultType.ACTION_FAILED,
            error_message=error_message
        )