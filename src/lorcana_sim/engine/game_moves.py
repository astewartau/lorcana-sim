"""Move types for the event-stream game interface."""

from dataclasses import dataclass
from typing import Any, Dict
from ..models.game.game_state import GameAction
from ..models.cards.base_card import Card
from ..models.cards.character_card import CharacterCard


@dataclass
class GameMove:
    """Base class for all game moves."""
    pass


@dataclass
class ActionMove(GameMove):
    """Move representing a game action."""
    action: GameAction
    parameters: Dict[str, Any]


@dataclass
class InkMove(GameMove):
    """Move to ink a card."""
    card: Card


@dataclass
class PlayMove(GameMove):
    """Move to play a card."""
    card: Card


@dataclass
class QuestMove(GameMove):
    """Move to quest with a character."""
    character: CharacterCard


@dataclass
class ChallengeMove(GameMove):
    """Move to challenge a character."""
    attacker: CharacterCard
    defender: CharacterCard


@dataclass
class SingMove(GameMove):
    """Move to sing a song."""
    singer: CharacterCard
    song: Card


@dataclass
class ChoiceMove(GameMove):
    """Move to respond to a choice."""
    choice_id: str
    option: str


@dataclass
class PassMove(GameMove):
    """Move to pass/progress the turn."""
    pass