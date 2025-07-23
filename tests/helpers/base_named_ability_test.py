"""Base test class for named ability integration tests."""

from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.engine.event_system import GameEventManager
from src.lorcana_sim.engine.action_queue import ActionQueue
from src.lorcana_sim.engine.choice_system import GameChoiceManager


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
        - Action queue for ability effects
        - Choice manager for player choices
        """
        self.player1 = Player("Player 1")
        self.player2 = Player("Player 2")
        self.game_state = GameState([self.player1, self.player2])
        self.event_manager = GameEventManager(self.game_state)
        self.action_queue = ActionQueue(self.event_manager)
        self.choice_manager = GameChoiceManager()
        self.game_state.event_manager = self.event_manager
    
    def create_event_context_with_action_queue(self, event_type, source=None, target=None, 
                                              player=None, additional_data=None):
        """Create EventContext with proper action queue and choice manager context.
        
        This helper ensures all integration tests have consistent context setup for 
        triggering composable abilities that require action queue access.
        """
        from src.lorcana_sim.engine.event_system import EventContext
        
        # Base context data with required components
        base_data = {
            'action_queue': self.action_queue,
            'choice_manager': self.choice_manager
        }
        
        # Merge with any additional data provided
        if additional_data:
            base_data.update(additional_data)
        
        return EventContext(
            event_type=event_type,
            source=source,
            target=target,
            player=player or self.game_state.current_player,
            game_state=self.game_state,
            additional_data=base_data
        )
    
    def trigger_event_with_context(self, event_type, source=None, target=None, 
                                  player=None, additional_data=None):
        """Trigger an event with proper action queue context and process any queued effects.
        
        This is the preferred method for triggering events in integration tests.
        """
        event_context = self.create_event_context_with_action_queue(
            event_type, source, target, player, additional_data
        )
        
        # Trigger the event
        self.event_manager.trigger_event(event_context)
        
        # Process any queued ability effects
        while self.action_queue.has_pending_actions():
            result = self.action_queue.process_next_action(apply_effect=True)
            if not result:
                break
        
        return event_context