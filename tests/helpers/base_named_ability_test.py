"""Base test class for named ability integration tests."""

from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.engine.event_system import GameEventManager


class BaseNamedAbilityTest:
    """Base class providing common setup for named ability integration tests.
    
    This class provides the standard test environment setup that's repeated
    across all named ability test files, reducing code duplication.
    """
    
    def setup_method(self):
        """Set up test environment with players and game state.
        
        Creates:
        - Two test players (player1 and player2)
        - Game state with both players
        - Event manager linked to game state
        """
        self.player1 = Player("Player 1")
        self.player2 = Player("Player 2")
        self.game_state = GameState([self.player1, self.player2])
        self.event_manager = GameEventManager(self.game_state)
        self.game_state.event_manager = self.event_manager