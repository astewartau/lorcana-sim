"""Conditional effects system for continuous ability evaluation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ...cards.character_card import CharacterCard
    from ...game.game_state import GameState
    from ...game.player import Player


class ActivationZone(Enum):
    """Zones where abilities can be active."""
    HAND = "hand"
    PLAY = "play"
    DISCARD = "discard"
    DECK = "deck"
    INK_WELL = "ink_well"


class ConditionType(Enum):
    """Types of conditions that can be evaluated."""
    TURN_BASED = "turn_based"          # During controller's turn, opponent's turn
    ZONE_BASED = "zone_based"          # When specific cards are in specific zones
    STAT_BASED = "stat_based"          # When stats meet certain criteria
    GAME_STATE = "game_state"          # When game state matches criteria
    TIMING = "timing"                  # During specific phases/steps


@dataclass
class ConditionalEffect:
    """Represents an effect that applies when certain conditions are met."""
    
    # Core identification
    effect_id: str
    source_card: 'CharacterCard'
    ability_name: str = ""  # Human-readable name like "QUICK REFLEXES"
    
    # Zone and timing control
    activation_zones: Set[ActivationZone] = field(default_factory=lambda: {ActivationZone.PLAY})
    priority: int = 0  # Higher priority effects apply first
    
    # Condition evaluation
    condition_type: ConditionType = ConditionType.TURN_BASED
    condition_func: Callable[['GameState', 'CharacterCard'], bool] = field(default=lambda gs, sc: True)
    
    # Effect application
    effect_func: Callable[['GameState', 'CharacterCard'], Dict[str, Any]] = field(default=lambda gs, sc: {})
    removal_func: Optional[Callable[['GameState', 'CharacterCard'], None]] = None
    
    # State tracking
    is_active: bool = False
    last_evaluation_turn: int = -1
    last_evaluation_phase: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate conditional effect after creation."""
        if not self.effect_id:
            raise ValueError("ConditionalEffect must have a non-empty effect_id")
        if not self.source_card:
            raise ValueError("ConditionalEffect must have a source_card")
    
    def __hash__(self):
        """Make ConditionalEffect hashable based on effect_id and source_card."""
        return hash((self.effect_id, id(self.source_card)))
    
    def __eq__(self, other):
        """Compare ConditionalEffect based on effect_id and source_card."""
        if not isinstance(other, ConditionalEffect):
            return False
        return (self.effect_id == other.effect_id and 
                self.source_card == other.source_card)
    
    def should_evaluate(self, game_state: 'GameState') -> bool:
        """Check if this effect should be evaluated based on timing."""
        current_turn = game_state.turn_number
        current_phase = game_state.current_phase.value
        
        # Always evaluate on first check
        if self.last_evaluation_turn == -1:
            return True
        
        # Re-evaluate if turn or phase changed
        if (current_turn != self.last_evaluation_turn or 
            current_phase != self.last_evaluation_phase):
            return True
        
        # For timing-sensitive conditions, evaluate more frequently
        if self.condition_type == ConditionType.TIMING:
            return True
        
        return False
    
    def evaluate_condition(self, game_state: 'GameState') -> bool:
        """Evaluate whether the condition is currently met."""
        try:
            result = self.condition_func(game_state, self.source_card)
            
            # Update evaluation tracking
            self.last_evaluation_turn = game_state.turn_number
            self.last_evaluation_phase = game_state.current_phase.value
            
            return result
        except Exception as e:
            # Log error but don't crash the game
            print(f"Error evaluating condition for {self.effect_id}: {e}")
            return False
    
    def apply_effect(self, game_state: 'GameState') -> Optional[Dict[str, Any]]:
        """Apply the effect and return any events to queue."""
        if self.is_active:
            return None  # Already active
        
        try:
            result = self.effect_func(game_state, self.source_card)
            self.is_active = True
            
            # Create application event
            event = {
                'type': 'CONDITIONAL_EFFECT_APPLIED',
                'effect_id': self.effect_id,
                'source': self.source_card.name,
                'ability_name': self.ability_name,
                'details': result,
                'timestamp': getattr(game_state, 'turn_number', 0) * 1000 + getattr(game_state, '_event_counter', 0)
            }
            return event
        except Exception as e:
            print(f"Error applying effect {self.effect_id}: {e}")
            return None
    
    def remove_effect(self, game_state: 'GameState') -> Optional[Dict[str, Any]]:
        """Remove the effect and return any events to queue."""
        if not self.is_active:
            return None  # Not active
        
        try:
            removal_details = None
            if self.removal_func:
                # Check if removal_func returns details (new pattern) or None (old pattern)
                result = self.removal_func(game_state, self.source_card)
                if isinstance(result, dict):
                    removal_details = result
            
            self.is_active = False
            
            # Create removal event
            removal_event = {
                'type': 'CONDITIONAL_EFFECT_REMOVED',
                'effect_id': self.effect_id,
                'source': self.source_card.name,
                'ability_name': self.ability_name,
                'timestamp': getattr(game_state, 'turn_number', 0) * 1000 + getattr(game_state, '_event_counter', 0)
            }
            
            # Include removal details if provided
            if removal_details:
                removal_event.update(removal_details)
            
            return removal_event
        except Exception as e:
            print(f"Error removing effect {self.effect_id}: {e}")
            return None
    
    def is_in_valid_zone(self, game_state: 'GameState') -> bool:
        """Check if the source card is in a valid activation zone."""
        source_zone = self._get_card_zone(game_state)
        return source_zone in self.activation_zones
    
    def _get_card_zone(self, game_state: 'GameState') -> Optional[ActivationZone]:
        """Determine which zone the source card is currently in."""
        # Find the card's owner
        owner = None
        for player in game_state.players:
            if self.source_card in player.characters_in_play:
                return ActivationZone.PLAY
            elif self.source_card in player.hand:
                return ActivationZone.HAND
            elif self.source_card in player.discard_pile:
                return ActivationZone.DISCARD
            elif self.source_card in player.deck:
                return ActivationZone.DECK
            elif self.source_card in player.inkwell:
                return ActivationZone.INK_WELL
        
        return None


# Condition Helper Functions
def during_controllers_turn(game_state: 'GameState', source_card: 'CharacterCard') -> bool:
    """Condition: Effect is active during the controller's turn."""
    # Find the card's controller
    for player in game_state.players:
        if (source_card in player.characters_in_play or 
            source_card in player.hand or 
            source_card in player.discard_pile or
            source_card in player.deck or
            source_card in player.inkwell):
            return game_state.current_player == player
    return False


def during_opponents_turn(game_state: 'GameState', source_card: 'CharacterCard') -> bool:
    """Condition: Effect is active during opponent's turn."""
    return not during_controllers_turn(game_state, source_card)


def character_in_play(character_name: str) -> Callable[['GameState', 'CharacterCard'], bool]:
    """Condition factory: Effect is active when named character is in play."""
    def condition(game_state: 'GameState', source_card: 'CharacterCard') -> bool:
        for player in game_state.players:
            for char in player.characters_in_play:
                if character_name.lower() in char.name.lower():
                    return True
        return False
    return condition


def controller_has_character_with_subtype(subtype: str) -> Callable[['GameState', 'CharacterCard'], bool]:
    """Condition factory: Effect is active when controller has character with specific subtype."""
    def condition(game_state: 'GameState', source_card: 'CharacterCard') -> bool:
        # Find the card's controller
        for player in game_state.players:
            if (source_card in player.characters_in_play or 
                source_card in player.hand or 
                source_card in player.discard_pile):
                # Check if this player has a character with the subtype
                for char in player.characters_in_play:
                    if hasattr(char, 'has_subtype') and char.has_subtype(subtype):
                        return True
                break
        return False
    return condition


def during_phase(phase_name: str) -> Callable[['GameState', 'CharacterCard'], bool]:
    """Condition factory: Effect is active during specific phase."""
    def condition(game_state: 'GameState', source_card: 'CharacterCard') -> bool:
        return game_state.current_phase.value == phase_name
    return condition