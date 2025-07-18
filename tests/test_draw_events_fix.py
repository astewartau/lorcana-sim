"""Test that draw events are properly generated and queued."""

import pytest
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.models.game.game_state import GameState, GameAction, Phase
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.step_system import ExecutionMode


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
    
    def test_first_player_skips_first_draw(self):
        """Test that first player correctly skips draw on first turn."""
        # Progress to draw phase
        self._progress_to_phase(Phase.DRAW)
        
        # Check initial state
        assert self.game_state.current_player == self.player1
        assert len(self.player1.deck) == 5
        assert len(self.player1.hand) == 0
        
        # Execute draw phase
        result = self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})
        
        # Should succeed but not draw any cards
        assert result.success
        assert 'draw_events' in result.data
        assert len(result.data['draw_events']) == 0
        
        # No cards should have been drawn
        assert len(self.player1.deck) == 5
        assert len(self.player1.hand) == 0
        
        # No draw messages should be queued
        draw_messages = [msg for msg in self.game_engine.message_queue 
                        if "drew" in msg.description]
        assert len(draw_messages) == 0
    
    def test_second_player_draws_on_first_turn(self):
        """Test that second player draws a card on their first turn."""
        # Progress to second player's draw phase
        self._progress_to_phase(Phase.DRAW)  # First player's draw
        self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})  # DRAW -> PLAY
        self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})  # PLAY -> READY (second player)
        self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})  # READY -> SET
        self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})  # SET -> DRAW
        
        # Check we're on second player's draw phase
        assert self.game_state.current_player == self.player2
        assert self.game_state.current_phase == Phase.DRAW
        assert len(self.player2.deck) == 5
        assert len(self.player2.hand) == 0
        
        # Clear message queue before executing draw
        self.game_engine.message_queue.clear()
        
        # Execute draw phase
        result = self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})
        
        # Should succeed and draw a card
        assert result.success
        assert 'draw_events' in result.data
        assert len(result.data['draw_events']) == 1
        
        # Check draw event structure
        draw_event = result.data['draw_events'][0]
        assert draw_event['type'] == 'card_drawn'
        assert draw_event['player'] == 'Bob'
        assert len(draw_event['cards_drawn']) == 1
        assert draw_event['source'] == 'draw_phase'
        
        # Card should have been drawn
        assert len(self.player2.deck) == 4
        assert len(self.player2.hand) == 1
        
        # Draw message should be queued
        draw_messages = [msg for msg in self.game_engine.message_queue 
                        if "drew" in msg.description]
        assert len(draw_messages) == 1
        assert "Bob drew" in draw_messages[0].description
    
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
        
        # Clear message queue before executing draw
        self.game_engine.message_queue.clear()
        
        # Execute draw phase
        result = self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})
        
        # Should succeed and draw a card
        assert result.success
        assert 'draw_events' in result.data
        assert len(result.data['draw_events']) == 1
        
        # Check draw event structure
        draw_event = result.data['draw_events'][0]
        assert draw_event['type'] == 'card_drawn'
        assert draw_event['player'] == 'Alice'
        assert len(draw_event['cards_drawn']) == 1
        assert draw_event['source'] == 'draw_phase'
        
        # Card should have been drawn
        assert len(self.player1.deck) == 4
        assert len(self.player1.hand) == 1
        
        # Draw message should be queued
        draw_messages = [msg for msg in self.game_engine.message_queue 
                        if "drew" in msg.description]
        assert len(draw_messages) == 1
        assert "Alice drew" in draw_messages[0].description
    
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
        while self.game_state.current_phase != target_phase:
            self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})
    
    def _complete_full_round(self):
        """Helper to complete a full round (both players complete their turns)."""
        # Player 1's turn
        while self.game_state.current_player == self.player1:
            self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})
        
        # Player 2's turn
        while self.game_state.current_player == self.player2:
            self.game_engine.execution_engine.execute_action(GameAction.PROGRESS, {})