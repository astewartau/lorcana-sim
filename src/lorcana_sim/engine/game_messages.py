"""Message types for the event-stream game interface."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from ..models.game.game_state import Player, Phase
from ..models.cards.base_card import Card
from ..models.cards.character_card import CharacterCard
from .choice_system import PlayerChoice


class MessageType(Enum):
    """Types of messages in the game message stream."""
    ACTION_REQUIRED = "action_required"
    CHOICE_REQUIRED = "choice_required" 
    STEP_EXECUTED = "step_executed"
    GAME_OVER = "game_over"


@dataclass
class LegalAction:
    """Represents a legal action that can be taken."""
    action: str  # NOTE: Changed from GameAction to string in Phase 4
    target: Optional[Union[Card, CharacterCard]] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameMessage:
    """Base class for all game messages."""
    type: MessageType
    player: Player


@dataclass
class ActionRequiredMessage(GameMessage):
    """Message indicating player needs to choose an action."""
    phase: Optional[Phase] = None
    legal_actions: List[LegalAction] = field(default_factory=list)


@dataclass
class ChoiceRequiredMessage(GameMessage):
    """Message indicating player needs to make a choice."""
    choice: Optional[PlayerChoice] = None
    ability_source: Optional[CharacterCard] = None


@dataclass
class StepExecutedMessage(GameMessage):
    """Message indicating a game step was executed."""
    step: Optional[Any] = None  # GameEvent enum object (not .value)
    deferred_action: Optional[Any] = None  # Store action to apply when message is fetched
    event_data: Optional[Dict[str, Any]] = None  # Raw event data with GameEvent enum and context


@dataclass
class GameOverMessage(GameMessage):
    """Message indicating the game has ended."""
    winner: Optional[Player] = None
    reason: str = ""