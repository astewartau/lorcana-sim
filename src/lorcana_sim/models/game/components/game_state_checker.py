"""Game state checking component for GameState."""

from typing import Tuple, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState, GameResult
    from ..player import Player


class GameStateCheckerComponent:
    """Handles game state checking operations for the game state."""
    
    def check_game_state(self, game_state: "GameState") -> None:
        """Check and update game state for win/loss/draw conditions."""
        from ....engine.event_system import GameEvent
        from ..game_state import GameResult
        
        if game_state.game_result != GameResult.ONGOING:
            return  # Game already over
        
        # Check lore victory (20 lore wins)
        for player in game_state.players:
            if player.lore >= 20:
                game_state.game_result = GameResult.LORE_VICTORY
                game_state.winner = player
                game_state.game_over_data = {
                    'event': GameEvent.GAME_ENDS,
                    'context': {
                        'result': 'lore_victory',
                        'winner_name': player.name,
                        'lore': player.lore
                    }
                }
                return
        
        # Check deck exhaustion (only after game has actually started)
        # Only check after turn 1 to avoid triggering on initialization
        if game_state.turn_number > 1:
            for player in game_state.players:
                if not player.deck and not player.hand:
                    # This player has no cards left
                    opponent = self._get_opponent(player, game_state)
                    game_state.game_result = GameResult.DECK_EXHAUSTION
                    game_state.winner = opponent
                    game_state.game_over_data = {
                        'event': GameEvent.GAME_ENDS,
                        'context': {
                            'result': 'deck_exhaustion',
                            'winner_name': opponent.name,
                            'loser_name': player.name
                        }
                    }
                    return
        
        # Check for stalemate (too many consecutive passes)
        if game_state.consecutive_passes >= game_state.max_consecutive_passes:
            game_state.game_result = GameResult.STALEMATE
            game_state.winner = None
            game_state.game_over_data = {
                'event': GameEvent.GAME_ENDS,
                'context': {
                    'result': 'stalemate',
                    'consecutive_passes': game_state.consecutive_passes
                }
            }
            return
    
    def is_game_over(self, game_state: "GameState") -> bool:
        """Check if the game is over."""
        from ..game_state import GameResult
        self.check_game_state(game_state)
        return game_state.game_result != GameResult.ONGOING
    
    def get_game_result(self, game_state: "GameState") -> Tuple["GameResult", Optional["Player"], Dict[str, Any]]:
        """Get the current game result."""
        self.check_game_state(game_state)
        return game_state.game_result, game_state.winner, game_state.game_over_data
    
    def _get_opponent(self, player: "Player", game_state: "GameState") -> "Player":
        """Get the opponent of the given player (assumes 2-player game)."""
        for p in game_state.players:
            if p != player:
                return p
        raise ValueError("Opponent not found")