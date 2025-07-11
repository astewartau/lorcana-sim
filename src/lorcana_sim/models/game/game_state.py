"""Game state model for Lorcana simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Any, Dict

from .player import Player
from ..cards.location_card import LocationCard


class Phase(Enum):
    """Lorcana turn phases."""
    READY = "ready"      # Ready step (ready all cards)
    SET = "set"          # Set step (draw card, play ink)
    MAIN = "main"        # Main phase (play cards, quest, challenge)


class GameAction(Enum):
    """Possible player actions."""
    PLAY_INK = "play_ink"
    PLAY_CHARACTER = "play_character"
    PLAY_ACTION = "play_action"
    PLAY_ITEM = "play_item"
    QUEST_CHARACTER = "quest_character"
    CHALLENGE_CHARACTER = "challenge_character"
    SING_SONG = "sing_song"
    ACTIVATE_ABILITY = "activate_ability"
    PASS_TURN = "pass_turn"


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
    actions_this_turn: List[GameAction] = field(default_factory=list)
    
    # Global Game Elements
    locations_in_play: List[LocationCard] = field(default_factory=list)
    
    # Game Rules State
    first_turn_draw_skipped: bool = False  # Track if first player skipped draw
    
    # Game over state
    winner: Optional[Player] = None
    game_over: bool = False
    
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
    
    def is_game_over(self) -> Tuple[bool, Optional[Player]]:
        """Check if game is over and return winner if any."""
        for player in self.players:
            if player.lore >= 20:
                return True, player
        return False, None
    
    def advance_phase(self) -> None:
        """Advance to the next phase."""
        if self.current_phase.value == 'ready':
            self.current_phase = Phase.SET
        elif self.current_phase.value == 'set':
            self.current_phase = Phase.MAIN
        elif self.current_phase.value == 'main':
            # End turn, move to next player
            self.end_turn()
    
    def end_turn(self) -> None:
        """End current player's turn and start next player's turn."""
        # Reset turn state
        self.ink_played_this_turn = False
        self.actions_this_turn.clear()
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # If back to first player, increment turn number
        if self.current_player_index == 0:
            self.turn_number += 1
        
        # Start ready phase for new player
        self.current_phase = Phase.READY
        self.ready_step()
    
    def ready_step(self) -> None:
        """Execute the ready step (ready all cards)."""
        current_player = self.current_player
        
        # Ready all characters
        for character in current_player.characters_in_play:
            character.ready()
        
        # Ready all items
        for item in current_player.items_in_play:
            if hasattr(item, 'exerted'):
                item.exerted = False
    
    def set_step(self) -> None:
        """Execute the set step (draw card, play ink)."""
        current_player = self.current_player
        
        # Draw card (skip on first turn for first player)
        should_draw = not (self.turn_number == 1 and 
                          self.current_player_index == 0 and 
                          not self.first_turn_draw_skipped)
        
        if should_draw:
            current_player.draw_card()
        elif self.turn_number == 1 and self.current_player_index == 0:
            self.first_turn_draw_skipped = True
    
    def can_play_ink(self) -> bool:
        """Check if current player can play ink."""
        return not self.ink_played_this_turn and self.current_phase.value == 'set'
    
    def can_perform_action(self, action: GameAction) -> bool:
        """Check if current player can perform the given action."""
        # Use value comparison to avoid enum identity issues
        if self.current_phase.value == 'main':
            return action in [
                GameAction.PLAY_CHARACTER,
                GameAction.PLAY_ACTION, 
                GameAction.PLAY_ITEM,
                GameAction.QUEST_CHARACTER,
                GameAction.CHALLENGE_CHARACTER,
                GameAction.SING_SONG,
                GameAction.ACTIVATE_ABILITY,
                GameAction.PASS_TURN
            ]
        elif self.current_phase.value == 'set':
            return action in [GameAction.PLAY_INK, GameAction.PASS_TURN]
        elif self.current_phase.value == 'ready':
            return action == GameAction.PASS_TURN
        
        return False
    
    def __str__(self) -> str:
        """String representation of the game state."""
        return f"Turn {self.turn_number} - {self.current_phase.value.title()} Phase - {self.current_player.name}'s turn"