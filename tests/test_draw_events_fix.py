"""Test that draw events are properly generated and queued."""

import pytest
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.models.game.game_state import GameState, Phase
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_engine import ExecutionMode
from lorcana_sim.engine.event_system import GameEvent
from lorcana_sim.engine.game_moves import PassMove


class TestDrawEventsFix:
    """Test that draw events are properly generated and queued."""
    
    def setup_method(self):
        """Set up test game with players and cards."""
        # Create players
        self.player1 = Player("Alice")
        self.player2 = Player("Bob")
        
        # Create simple test cards
        for i in range(5):
            card = CharacterCard(
                id=i,
                name=f"Test Card {i}",
                version=None,
                full_name=f"Test Card {i}",
                cost=i+1,
                color=CardColor.AMBER,
                inkwell=True,
                rarity=Rarity.COMMON,
                set_code="TEST",
                number=i,
                story="",
                strength=1,
                willpower=1,
                lore=1
            )
            self.player1.deck.append(card)
            
        for i in range(5):
            card = CharacterCard(
                id=i+10,
                name=f"Player2 Card {i}",
                version=None,
                full_name=f"Player2 Card {i}",
                cost=i+1,
                color=CardColor.SAPPHIRE,
                inkwell=True,
                rarity=Rarity.COMMON,
                set_code="TEST",
                number=i+10,
                story="",
                strength=1,
                willpower=1,
                lore=1
            )
            self.player2.deck.append(card)
        
        # Create game state and engine
        self.game_state = GameState([self.player1, self.player2])
        self.game_engine = GameEngine(self.game_state, ExecutionMode.MANUAL)
        
        # Start the game (this was missing!)
        self.game_engine.start_game()
    
    def test_first_player_skips_first_draw(self):
        """Test that first player correctly skips draw on first turn."""
        # Progress to draw phase
        self._progress_to_phase(Phase.DRAW)
        
        # Check initial state
        assert self.game_state.current_player == self.player1
        assert len(self.player1.deck) == 5
        assert len(self.player1.hand) == 0
        
        # Execute draw phase using message-based API
        initial_deck_size = len(self.player1.deck)
        initial_hand_size = len(self.player1.hand)
        
        # Process the draw phase message
        message = self.game_engine.next_message()
        
        # Auto-progress through the draw phase
        self.game_engine.next_message(PassMove())
        
        # No cards should have been drawn (first player skips first draw)
        assert len(self.player1.deck) == initial_deck_size
        assert len(self.player1.hand) == initial_hand_size
    
    def test_second_player_draws_on_first_turn(self):
        """Test that second player draws a card on their first turn."""
        # Progress to second player's draw phase
        self._progress_to_phase(Phase.DRAW)  # First player's draw
        
        # Complete first player's turn and get to second player's draw
        self._progress_to_phase(Phase.PLAY)  # First player's play phase
        # Pass through play phase to end first player's turn
        message = self.game_engine.next_message(PassMove())
        
        # Now should be second player's turn, progress to their draw phase
        self._progress_to_phase(Phase.DRAW)
        
        # Check we're on second player's draw phase
        assert self.game_state.current_player == self.player2
        assert self.game_state.current_phase == Phase.DRAW
        assert len(self.player2.deck) == 5
        assert len(self.player2.hand) == 0
        
        # No need to clear message queue in new architecture
        
        # Execute draw phase using message-based API
        initial_deck_size = len(self.player2.deck)
        initial_hand_size = len(self.player2.hand)
        
        # Process the draw phase message
        message = self.game_engine.next_message()
        
        # Auto-progress through the draw phase
        self.game_engine.next_message(PassMove())
        
        # Card should have been drawn (second player draws on first turn)
        assert len(self.player2.deck) == initial_deck_size - 1
        assert len(self.player2.hand) == initial_hand_size + 1
    
    def test_player_draws_on_second_turn(self):
        """Test that first player draws on their second turn."""
        # Complete one full round and get to first player's second turn
        self._complete_full_round()
        
        # Progress to draw phase on second turn
        self._progress_to_phase(Phase.DRAW)
        
        # Check we're on first player's second turn
        assert self.game_state.current_player == self.player1
        assert self.game_state.turn_number == 2
        assert len(self.player1.deck) == 5
        assert len(self.player1.hand) == 0
        
        # No need to clear message queue in new architecture
        
        # Execute draw phase using message-based API
        initial_deck_size = len(self.player1.deck)
        initial_hand_size = len(self.player1.hand)
        
        # Process the draw phase message
        message = self.game_engine.next_message()
        
        # Auto-progress through the draw phase
        self.game_engine.next_message(PassMove())
        
        # Card should have been drawn (first player draws on second turn)
        assert len(self.player1.deck) == initial_deck_size - 1
        assert len(self.player1.hand) == initial_hand_size + 1
    
    def test_set_last_event_method_exists(self):
        """Test that the set_last_event method exists and works."""
        # This was the root cause of the bug
        assert hasattr(self.game_state, 'set_last_event')
        assert hasattr(self.game_state, 'get_last_event')
        assert hasattr(self.game_state, 'clear_last_event')
        
        # Test setting and getting an event
        self.game_state.set_last_event('TEST_EVENT', test_data='value')
        last_event = self.game_state.get_last_event()
        
        assert last_event is not None
        assert last_event['type'] == 'TEST_EVENT'
        assert last_event['test_data'] == 'value'
        assert 'timestamp' in last_event
        
        # Test clearing the event
        self.game_state.clear_last_event()
        assert self.game_state.get_last_event() is None
    
    def _progress_to_phase(self, target_phase: Phase):
        """Helper to progress to a specific phase."""
        max_iterations = 20  # Safety limit
        iterations = 0
        
        while self.game_state.current_phase != target_phase and iterations < max_iterations:
            # Use the message-based API like full_game_example.py
            message = self.game_engine.next_message()
            
            # Auto-progress through non-play phases by passing
            if hasattr(message, 'phase') and message.phase != Phase.PLAY:
                self.game_engine.next_message(PassMove())
            
            iterations += 1
        
        if iterations >= max_iterations:
            raise RuntimeError(f"Failed to reach {target_phase} after {max_iterations} iterations, stuck at {self.game_state.current_phase}")
    
    def _complete_full_round(self):
        """Helper to complete a full round (both players complete their turns)."""
        max_iterations = 50  # Safety limit for full round
        iterations = 0
        starting_player = self.game_state.current_player
        
        # Complete current player's turn
        while self.game_state.current_player == starting_player and iterations < max_iterations:
            message = self.game_engine.next_message()
            if hasattr(message, 'phase') and message.phase == Phase.PLAY:
                # In play phase, need to pass the turn
                self.game_engine.next_message(PassMove())
            iterations += 1
        
        # Complete second player's turn  
        second_player = self.game_state.current_player
        while self.game_state.current_player == second_player and iterations < max_iterations:
            message = self.game_engine.next_message()
            if hasattr(message, 'phase') and message.phase == Phase.PLAY:
                # In play phase, need to pass the turn
                self.game_engine.next_message(PassMove())
            iterations += 1
        
        if iterations >= max_iterations:
            raise RuntimeError(f"Failed to complete full round after {max_iterations} iterations")