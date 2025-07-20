"""Game state model for Lorcana simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Any, Dict

from .player import Player
from ..cards.location_card import LocationCard
from .components import (
    ZoneManagementComponent,
    CostModificationComponent,
    PhaseManagementComponent,
    GameStateCheckerComponent,
    TurnManagementComponent
)


class Phase(Enum):
    """Lorcana turn phases."""
    READY = "ready"      # Ready step (ready all exerted cards)
    SET = "set"          # Set step (resolve start-of-turn effects)
    DRAW = "draw"        # Draw step (draw a card)
    PLAY = "play"        # Play phase (ink, play cards, quest, challenge)


# NOTE: GameAction enum REMOVED in Phase 4 - use direct Move→Effect conversion
class GameResult(Enum):
    """Possible game results."""
    ONGOING = "ongoing"
    LORE_VICTORY = "lore_victory"
    DECK_EXHAUSTION = "deck_exhaustion"  # Opponent runs out of cards
    STALEMATE = "stalemate"  # Both players unable to make progress


@dataclass
class GameState:
    """Tracks the complete state of a Lorcana game."""
    # Players and Turn Management
    players: List[Player]
    current_player_index: int = 0
    turn_number: int = 1
    current_phase: Phase = Phase.READY
    
    # Turn State Tracking
    ink_played_this_turn: bool = False
    card_drawn_this_turn: bool = False  # Track if mandatory draw has occurred
    # NOTE: Specific action tracking removed in Phase 4 - using effect tracking instead
    actions_this_turn: List[str] = field(default_factory=list)  # Track effect descriptions
    characters_acted_this_turn: List[int] = field(default_factory=list)  # Track character IDs that have acted
    
    # Global Game Elements
    locations_in_play: List[LocationCard] = field(default_factory=list)
    
    # Game Rules State
    first_turn_draw_skipped: bool = False  # Track if first player skipped draw
    
    # Game over state
    game_result: GameResult = GameResult.ONGOING
    winner: Optional[Player] = None
    game_over_data: Dict[str, Any] = field(default_factory=dict)
    
    # Stalemate detection
    consecutive_passes: int = 0  # Track consecutive pass actions
    max_consecutive_passes: int = 4  # Both players pass twice = stalemate
    
    # Last event tracking for inspection
    last_event: Optional[Dict[str, Any]] = None  # The most recent event that occurred
    
    # Component instances for delegated functionality
    _zone_management: ZoneManagementComponent = field(default_factory=ZoneManagementComponent)
    _cost_modification: CostModificationComponent = field(default_factory=CostModificationComponent)
    _phase_management: PhaseManagementComponent = field(default_factory=PhaseManagementComponent)
    _game_state_checker: GameStateCheckerComponent = field(default_factory=GameStateCheckerComponent)
    _turn_management: TurnManagementComponent = field(default_factory=TurnManagementComponent)
    
    def __post_init__(self) -> None:
        """Validate game state after creation."""
        if len(self.players) < 2:
            raise ValueError("Game must have at least 2 players")
        if self.current_player_index >= len(self.players):
            raise ValueError("Current player index out of range")
    
    @property
    def current_player(self) -> Player:
        """Get the currently active player."""
        return self.players[self.current_player_index]
    
    @property
    def opponent(self) -> Player:
        """Get the opponent (assumes 2-player game)."""
        opponent_index = 1 - self.current_player_index
        return self.players[opponent_index]
    
    def check_game_state(self) -> None:
        """Check and update game state for win/loss/draw conditions."""
        self._game_state_checker.check_game_state(self)
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self._game_state_checker.is_game_over(self)
    
    def get_game_result(self) -> Tuple[GameResult, Optional[Player], Dict[str, Any]]:
        """Get the current game result."""
        return self._game_state_checker.get_game_result(self)
    
    
    def advance_phase(self) -> None:
        """Advance to the next phase."""
        self._phase_management.advance_phase(self)
    
    def end_turn(self) -> None:
        """End current player's turn and start next player's turn."""
        self._phase_management.end_turn(self)
    
    def ready_step(self) -> List[Dict[str, Any]]:
        """Execute the ready step (ready all cards and start turn).
        
        Returns:
            List of event data for items that were readied.
        """
        return self._phase_management.ready_step(self)
    
    
    def set_step(self) -> None:
        """Execute the set step (resolve start-of-turn effects)."""
        self._phase_management.set_step(self)
    
    def draw_step(self) -> List[Dict[str, Any]]:
        """Execute the draw step (draw a card).
        
        Returns:
            List of event data for draw events that occurred.
        """
        return self._phase_management.draw_step(self)
    
    # Zone Management Methods
    @property
    def zone_manager(self):
        """Get or create the zone manager instance."""
        return self._zone_management.zone_manager
    
    def register_card_conditional_effects(self, card) -> None:
        """Register all conditional effects from a card with the zone manager."""
        self._zone_management.register_card_conditional_effects(card)
    
    def unregister_card_conditional_effects(self, card) -> None:
        """Unregister all conditional effects from a card."""
        self._zone_management.unregister_card_conditional_effects(card)
    
    def notify_card_zone_change(self, card, from_zone_name: Optional[str], to_zone_name: Optional[str]) -> List[Dict]:
        """Notify zone manager of card movement and return any events generated."""
        return self._zone_management.notify_card_zone_change(card, from_zone_name, to_zone_name, self)
    
    def evaluate_conditional_effects(self) -> List[Dict]:
        """Evaluate all conditional effects and return any events generated."""
        return self._zone_management.evaluate_conditional_effects(self)
    
    # Cost Modification Methods
    @property
    def cost_modification_manager(self):
        """Get or create the cost modification manager instance."""
        return self._cost_modification.cost_modification_manager
    
    def get_modified_card_cost(self, card) -> int:
        """Get the modified cost for a card after all applicable cost modifiers."""
        return self._cost_modification.get_modified_card_cost(card, self)
    
    def register_cost_modifier(self, modifier) -> None:
        """Register a cost modifier with the game state."""
        self._cost_modification.register_cost_modifier(modifier)
    
    def unregister_cost_modifier(self, modifier) -> None:
        """Unregister a cost modifier from the game state."""
        self._cost_modification.unregister_cost_modifier(modifier)
    
    def can_play_ink(self) -> bool:
        """Check if current player can play ink."""
        return self._turn_management.can_play_ink(self)
    
    def has_character_acted_this_turn(self, character_id: int) -> bool:
        """Check if a character has already acted this turn."""
        return self._turn_management.has_character_acted_this_turn(character_id, self)
    
    def mark_character_acted(self, character_id: int) -> None:
        """Mark that a character has acted this turn."""
        self._turn_management.mark_character_acted(character_id, self)
    
    def can_perform_action(self, action_description: str) -> bool:
        """Check if current player can perform the given action."""
        return self._turn_management.can_perform_action(action_description, self)
    
    def record_action(self, action_description: str) -> None:
        """Record an action for stalemate detection."""
        self.actions_this_turn.append(action_description)
        self._turn_management.record_action(action_description, self)
    
    def set_last_event(self, event_type: str, **kwargs) -> None:
        """Set the last event that occurred in the game."""
        import time
        self.last_event = {
            'type': event_type,
            'timestamp': time.time(),
            **kwargs
        }
    
    def get_last_event(self) -> Optional[Dict[str, Any]]:
        """Get the last event that occurred in the game."""
        return self.last_event
    
    def clear_last_event(self) -> None:
        """Clear the last event."""
        self.last_event = None
    
    def __str__(self) -> str:
        """String representation of the game state."""
        return f"Turn {self.turn_number} - {self.current_phase.value.title()} Phase - {self.current_player.name}'s turn"