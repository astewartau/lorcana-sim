"""Game state model for Lorcana simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Any, Dict

from .player import Player
from ..cards.location_card import LocationCard


class Phase(Enum):
    """Lorcana turn phases."""
    READY = "ready"      # Ready step (ready all exerted cards)
    SET = "set"          # Set step (resolve start-of-turn effects)
    DRAW = "draw"        # Draw step (draw a card)
    PLAY = "play"        # Play phase (ink, play cards, quest, challenge)


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
    PROGRESS = "progress"       # Progress to next phase
    PASS_TURN = "pass_turn"      # Pass turn to opponent


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
    actions_this_turn: List[GameAction] = field(default_factory=list)
    
    # Global Game Elements
    locations_in_play: List[LocationCard] = field(default_factory=list)
    
    # Game Rules State
    first_turn_draw_skipped: bool = False  # Track if first player skipped draw
    
    # Game over state
    game_result: GameResult = GameResult.ONGOING
    winner: Optional[Player] = None
    game_over_reason: str = ""
    
    # Stalemate detection
    consecutive_passes: int = 0  # Track consecutive pass actions
    max_consecutive_passes: int = 4  # Both players pass twice = stalemate
    
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
        if self.game_result != GameResult.ONGOING:
            return  # Game already over
        
        # Check lore victory (20 lore wins)
        for player in self.players:
            if player.lore >= 20:
                self.game_result = GameResult.LORE_VICTORY
                self.winner = player
                self.game_over_reason = f"{player.name} wins with {player.lore} lore!"
                return
        
        # Check deck exhaustion (only after game has actually started)
        # Only check after turn 1 to avoid triggering on initialization
        if self.turn_number > 1:
            for player in self.players:
                if not player.deck and not player.hand:
                    # This player has no cards left
                    opponent = self.get_opponent(player)
                    self.game_result = GameResult.DECK_EXHAUSTION
                    self.winner = opponent
                    self.game_over_reason = f"{opponent.name} wins - {player.name} ran out of cards!"
                    return
        
        # Check for stalemate (too many consecutive passes)
        if self.consecutive_passes >= self.max_consecutive_passes:
            self.game_result = GameResult.STALEMATE
            self.winner = None
            self.game_over_reason = "Game ended in stalemate - both players unable to make progress"
            return
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        self.check_game_state()
        return self.game_result != GameResult.ONGOING
    
    def get_game_result(self) -> Tuple[GameResult, Optional[Player], str]:
        """Get the current game result."""
        self.check_game_state()
        return self.game_result, self.winner, self.game_over_reason
    
    def get_opponent(self, player: Player) -> Player:
        """Get the opponent of the given player (assumes 2-player game)."""
        for p in self.players:
            if p != player:
                return p
        raise ValueError("Opponent not found")
    
    def advance_phase(self) -> None:
        """Advance to the next phase."""
        if self.current_phase.value == 'ready':
            self.current_phase = Phase.SET
        elif self.current_phase.value == 'set':
            self.current_phase = Phase.DRAW
        elif self.current_phase.value == 'draw':
            self.current_phase = Phase.PLAY
        elif self.current_phase.value == 'play':
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
        
        # Update character dry status after turn changes
        self._update_character_dry_status()
        
        # Start ready phase for new player
        self.current_phase = Phase.READY
        self.ready_step()
    
    def ready_step(self) -> None:
        """Execute the ready step (ready all cards and start turn)."""
        current_player = self.current_player
        
        # Start the turn (reset ink usage, ready characters)
        current_player.start_turn()
        
        # Ready all items
        for item in current_player.items_in_play:
            if hasattr(item, 'exerted'):
                item.exerted = False
    
    def set_step(self) -> None:
        """Execute the set step (resolve start-of-turn effects)."""
        # Handle any start-of-turn triggered abilities
        # TODO: Implement start-of-turn ability resolution here
        pass
    
    def draw_step(self) -> None:
        """Execute the draw step (draw a card)."""
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
        return not self.ink_played_this_turn and self.current_phase.value == 'play'
    
    def can_perform_action(self, action: GameAction) -> bool:
        """Check if current player can perform the given action."""
        # Game over - no actions allowed
        if self.is_game_over():
            return False
        
        # Use value comparison to avoid enum identity issues
        if self.current_phase.value == 'play':
            return action in [
                GameAction.PLAY_INK,
                GameAction.PLAY_CHARACTER,
                GameAction.PLAY_ACTION, 
                GameAction.PLAY_ITEM,
                GameAction.QUEST_CHARACTER,
                GameAction.CHALLENGE_CHARACTER,
                GameAction.SING_SONG,
                GameAction.ACTIVATE_ABILITY,
                GameAction.PROGRESS,
                GameAction.PASS_TURN
            ]
        elif self.current_phase.value in ['ready', 'set', 'draw']:
            return action in [GameAction.PROGRESS, GameAction.PASS_TURN]
        
        return False
    
    def record_action(self, action: GameAction) -> None:
        """Record an action for stalemate detection."""
        if action == GameAction.PASS_TURN:
            self.consecutive_passes += 1
        else:
            # Reset pass counter on any meaningful action
            self.consecutive_passes = 0
    
    def _update_character_dry_status(self) -> None:
        """Update dry status for all characters based on current turn."""
        for player in self.players:
            for char in player.characters_in_play:
                if char.turn_played is not None:
                    # Ink dries at start of owner's next turn
                    char.is_dry = self.turn_number > char.turn_played
                else:
                    # Character wasn't played this game (already dry)
                    char.is_dry = True
    
    def __str__(self) -> str:
        """String representation of the game state."""
        return f"Turn {self.turn_number} - {self.current_phase.value.title()} Phase - {self.current_player.name}'s turn"