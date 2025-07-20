"""Tests for game state functionality."""

import pytest
from dataclasses import dataclass
from typing import List

from src.lorcana_sim.models.game.game_state import GameState, Phase
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.action_card import ActionCard
from src.lorcana_sim.models.cards.item_card import ItemCard
from src.lorcana_sim.models.cards.base_card import Card, CardColor, Rarity
# NOTE: Old ability system removed - commenting out old import
# from src.lorcana_sim.models.abilities.base_ability import Ability, AbilityType
from src.lorcana_sim.engine.move_validator import MoveValidator
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.engine.action_result import ActionResult
from src.lorcana_sim.engine.game_engine import ExecutionMode


@pytest.fixture
def mock_character():
    """Create a mock character card for testing."""
    return CharacterCard(
        id=1,
        name="Test Character",
        version="Test Version",
        full_name="Test Character - Test Version",
        cost=3,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test Story",
        strength=2,
        willpower=3,
        lore=1,
        subtypes=["Hero"]
    )


@pytest.fixture
def mock_action():
    """Create a mock action card for testing."""
    return ActionCard(
        id=2,
        name="Test Action",
        version=None,
        full_name="Test Action",
        cost=2,
        color=CardColor.STEEL,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=2,
        story="Test Story"
    )


@pytest.fixture
def mock_item():
    """Create a mock item card for testing."""
    return ItemCard(
        id=3,
        name="Test Item",
        version=None,
        full_name="Test Item",
        cost=1,
        color=CardColor.EMERALD,
        inkwell=False,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=3,
        story="Test Story"
    )


@pytest.fixture
def players_with_cards(mock_character, mock_action, mock_item):
    """Create two players with some cards."""
    player1 = Player(name="Player 1")
    player2 = Player(name="Player 2")
    
    # Give player1 some cards
    player1.hand = [mock_character, mock_action, mock_item]
    player1.deck = [mock_character, mock_action] * 5  # 10 cards in deck
    
    # Give player2 some cards  
    player2.hand = [mock_character, mock_action]
    player2.deck = [mock_character, mock_action] * 5  # 10 cards in deck
    
    return [player1, player2]


@pytest.fixture
def game_state(players_with_cards):
    """Create a basic game state for testing."""
    return GameState(players=players_with_cards)


class TestGameState:
    """Test GameState functionality."""
    
    def test_game_state_creation(self, players_with_cards):
        """Test creating a valid game state."""
        game_state = GameState(players=players_with_cards)
        
        assert len(game_state.players) == 2
        assert game_state.current_player_index == 0
        assert game_state.turn_number == 1
        assert game_state.current_phase == Phase.READY
        assert not game_state.ink_played_this_turn
        assert len(game_state.actions_this_turn) == 0
    
    def test_game_state_validation(self):
        """Test game state validation."""
        # Should raise error with too few players
        with pytest.raises(ValueError, match="Game must have at least 2 players"):
            GameState(players=[Player("Only Player")])
        
        # Should raise error with invalid player index
        with pytest.raises(ValueError, match="Current player index out of range"):
            GameState(
                players=[Player("Player 1"), Player("Player 2")],
                current_player_index=5
            )
    
    def test_current_player_property(self, game_state):
        """Test current player property."""
        assert game_state.current_player.name == "Player 1"
        
        game_state.current_player_index = 1
        assert game_state.current_player.name == "Player 2"
    
    def test_opponent_property(self, game_state):
        """Test opponent property for 2-player game."""
        assert game_state.opponent.name == "Player 2"
        
        game_state.current_player_index = 1
        assert game_state.opponent.name == "Player 1"
    
    def test_phase_advancement(self, game_state):
        """Test phase advancement."""
        # Start in READY phase
        assert game_state.current_phase == Phase.READY
        
        # Advance to SET
        game_state.advance_phase()
        assert game_state.current_phase == Phase.SET
        
        # Advance to DRAW
        game_state.advance_phase()
        assert game_state.current_phase == Phase.DRAW
        
        # Advance to PLAY
        game_state.advance_phase()
        assert game_state.current_phase == Phase.PLAY
        
        # Advance should end turn and go back to READY for next player
        game_state.advance_phase()
        assert game_state.current_phase == Phase.READY
        assert game_state.current_player_index == 1
        assert game_state.turn_number == 1  # Still turn 1 until we cycle back to player 1
    
    def test_turn_advancement(self, game_state):
        """Test turn number advancement."""
        # Complete player 1's turn
        game_state.advance_phase()  # READY -> SET
        game_state.advance_phase()  # SET -> DRAW
        game_state.advance_phase()  # DRAW -> PLAY
        game_state.advance_phase()  # PLAY -> end turn, switch to player 2
        
        assert game_state.current_player_index == 1
        assert game_state.turn_number == 1
        
        # Complete player 2's turn
        game_state.advance_phase()  # READY -> SET
        game_state.advance_phase()  # SET -> DRAW
        game_state.advance_phase()  # DRAW -> PLAY
        game_state.advance_phase()  # PLAY -> end turn, switch to player 1
        
        assert game_state.current_player_index == 0
        assert game_state.turn_number == 2  # Now turn 2
    
    def test_game_over_condition(self, game_state):
        """Test game over conditions."""
        # Initially no one has won
        assert not game_state.is_game_over()
        result, winner, reason = game_state.get_game_result()
        assert winner is None
        
        # Give player 1 enough lore to win
        game_state.current_player.lore = 20
        assert game_state.is_game_over()
        result, winner, reason = game_state.get_game_result()
        assert winner == game_state.current_player
    
    def test_can_play_ink(self, game_state):
        """Test ink playing restrictions."""
        # Can't play ink in READY phase
        assert game_state.current_phase == Phase.READY
        assert not game_state.can_play_ink()
        
        # Can play ink in PLAY phase
        game_state.current_phase = Phase.PLAY
        assert game_state.can_play_ink()
        
        # Can't play ink after already playing ink
        game_state.ink_played_this_turn = True
        assert not game_state.can_play_ink()
        
        # Can't play ink in other phases
        game_state.ink_played_this_turn = False
        game_state.current_phase = Phase.SET
        assert not game_state.can_play_ink()
    
    def test_can_perform_action(self, game_state):
        """Test action validation by phase."""
        # READY phase - progress and pass turn
        assert game_state.current_phase == Phase.READY
        assert game_state.can_perform_action("progress")
        assert game_state.can_perform_action("pass_turn")
        assert not game_state.can_perform_action("play_character")
        assert not game_state.can_perform_action("play_ink")
        
        # SET phase - progress and pass turn
        game_state.current_phase = Phase.SET
        assert game_state.can_perform_action("progress")
        assert game_state.can_perform_action("pass_turn")
        assert not game_state.can_perform_action("play_character")
        assert not game_state.can_perform_action("play_ink")
        
        # DRAW phase - progress and pass turn
        game_state.current_phase = Phase.DRAW
        assert game_state.can_perform_action("progress")
        assert game_state.can_perform_action("pass_turn")
        assert not game_state.can_perform_action("play_character")
        assert not game_state.can_perform_action("play_ink")
        
        # PLAY phase - most actions
        game_state.current_phase = Phase.PLAY
        assert game_state.can_perform_action("play_character")
        assert game_state.can_perform_action("play_action")
        assert game_state.can_perform_action("quest_character")
        assert game_state.can_perform_action("challenge_character")
        assert game_state.can_perform_action("play_ink")
        assert game_state.can_perform_action("progress")
        assert game_state.can_perform_action("pass_turn")


class TestPlayer:
    """Test Player functionality."""
    
    def test_player_creation(self):
        """Test creating a player."""
        player = Player(name="Test Player")
        
        assert player.name == "Test Player"
        assert len(player.hand) == 0
        assert len(player.deck) == 0
        assert player.lore == 0
        assert player.ink_used_this_turn == 0
    
    def test_ink_calculations(self, mock_character, mock_action):
        """Test ink calculation properties."""
        player = Player(name="Test Player")
        
        # No ink initially
        assert player.total_ink == 0
        assert player.available_ink == 0
        
        # Add some ink
        player.inkwell = [mock_character, mock_action]
        assert player.total_ink == 2
        assert player.available_ink == 2
        
        # Spend some ink
        player.spend_ink(1)
        assert player.total_ink == 2
        assert player.available_ink == 1
        assert player.ink_used_this_turn == 1
    
    def test_can_afford(self, mock_character):
        """Test affordability checking."""
        player = Player(name="Test Player")
        
        # Can't afford with no ink
        assert not player.can_afford(mock_character)
        
        # Add enough ink
        player.inkwell = [mock_character] * 3  # 3 ink
        assert player.can_afford(mock_character)  # Costs 3
        
        # Spend ink so can't afford
        player.spend_ink(1)
        assert not player.can_afford(mock_character)  # Now only 2 available
    
    def test_draw_card(self, mock_character, mock_action):
        """Test drawing cards."""
        player = Player(name="Test Player")
        player.deck = [mock_character, mock_action]
        
        # Draw first card
        drawn = player.draw_card()
        assert drawn == mock_character
        assert len(player.hand) == 1
        assert len(player.deck) == 1
        
        # Draw second card
        drawn = player.draw_card()
        assert drawn == mock_action
        assert len(player.hand) == 2
        assert len(player.deck) == 0
        
        # Try to draw from empty deck
        drawn = player.draw_card()
        assert drawn is None
        assert len(player.hand) == 2
    
    def test_play_ink(self, mock_character):
        """Test playing cards as ink."""
        player = Player(name="Test Player")
        player.hand = [mock_character]
        
        # Should succeed
        result = player.play_ink(mock_character)
        assert result
        assert len(player.hand) == 0
        assert len(player.inkwell) == 1
        assert mock_character in player.inkwell
        
        # Try to play non-inkable card
        non_inkable = CharacterCard(
            id=99, name="Non-Inkable", version=None, full_name="Non-Inkable",
            cost=1, color=CardColor.AMBER, inkwell=False, rarity=Rarity.COMMON,
            set_code="TEST", number=99, story="Test"
        )
        player.hand = [non_inkable]
        result = player.play_ink(non_inkable)
        assert not result
        assert len(player.hand) == 1
        assert len(player.inkwell) == 1
    
    def test_play_character(self, mock_character):
        """Test playing character cards."""
        player = Player(name="Test Player")
        player.hand = [mock_character]
        player.inkwell = [mock_character] * 3  # Enough ink
        
        result = player.play_character(mock_character, mock_character.cost)
        assert result
        assert len(player.hand) == 0
        assert len(player.characters_in_play) == 1
        assert mock_character in player.characters_in_play
        assert player.ink_used_this_turn == 3
    
    def test_ready_characters(self, mock_character):
        """Test readying characters."""
        player = Player(name="Test Player")
        
        # Add exerted character
        mock_character.exerted = True
        player.characters_in_play = [mock_character]
        
        # Ready all characters
        player.ready_all_characters()
        assert not mock_character.exerted
    
    def test_get_ready_characters(self, mock_character):
        """Test getting ready characters."""
        player = Player(name="Test Player")
        
        ready_char = CharacterCard(
            id=1, name="Ready", version=None, full_name="Ready",
            cost=1, color=CardColor.AMBER, inkwell=True, rarity=Rarity.COMMON,
            set_code="TEST", number=1, story="Test"
        )
        
        exerted_char = CharacterCard(
            id=2, name="Exerted", version=None, full_name="Exerted", 
            cost=1, color=CardColor.AMBER, inkwell=True, rarity=Rarity.COMMON,
            set_code="TEST", number=2, story="Test"
        )
        exerted_char.exerted = True
        
        player.characters_in_play = [ready_char, exerted_char]
        
        ready_characters = player.get_ready_characters()
        assert len(ready_characters) == 1
        assert ready_char in ready_characters
        assert exerted_char not in ready_characters


class TestMoveValidator:
    """Test MoveValidator functionality."""
    
    def test_validator_creation(self, game_state):
        """Test creating a move validator."""
        validator = MoveValidator(game_state)
        assert validator.game_state == game_state
    
    def test_get_playable_ink_cards(self, game_state):
        """Test getting playable ink cards."""
        validator = MoveValidator(game_state)
        
        inkable_cards = validator.get_playable_ink_cards()
        # Only 2 cards are inkable (character and action, not item)
        assert len(inkable_cards) == 2
        # Verify only inkable cards are returned
        for card in inkable_cards:
            assert card.can_be_inked()
    
    def test_get_legal_actions_by_phase(self, game_state):
        """Test legal actions vary by phase."""
        validator = MoveValidator(game_state)
        
        # READY phase
        game_state.current_phase = Phase.READY
        actions = validator.get_all_legal_actions()
        action_types = [action for action, _ in actions]
        assert "progress" in action_types
        assert "pass_turn" in action_types
        assert "play_ink" not in action_types
        
        # SET phase
        game_state.current_phase = Phase.SET
        actions = validator.get_all_legal_actions()
        action_types = [action for action, _ in actions]
        assert "progress" in action_types
        assert "pass_turn" in action_types
        assert "play_ink" not in action_types
        
        # DRAW phase
        game_state.current_phase = Phase.DRAW
        actions = validator.get_all_legal_actions()
        action_types = [action for action, _ in actions]
        assert "progress" in action_types
        assert "pass_turn" in action_types
        assert "play_ink" not in action_types
        
        # PLAY phase - give player enough ink to play cards
        game_state.current_phase = Phase.PLAY
        game_state.current_player.inkwell = [game_state.current_player.hand[0]] * 5  # Enough ink
        actions = validator.get_all_legal_actions()
        action_types = [action for action, _ in actions]
        assert "progress" in action_types
        assert "pass_turn" in action_types
        assert "play_character" in action_types
        assert "play_ink" in action_types


class TestGameEngine:
    """Test GameEngine functionality."""
    
    def test_engine_creation(self, game_state):
        """Test creating a game engine."""
        engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
        assert engine.game_state == game_state
        assert isinstance(engine.validator, MoveValidator)
    
    def test_execute_play_ink(self, game_state, mock_character):
        """Test executing play ink action."""
        engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
        game_state.current_phase = Phase.PLAY
        
        # Should succeed
        result = engine.execute_action(
            "play_ink",
            {'card': mock_character}
        )
        
        assert result.success
        assert result.action_type == "play_ink"
        assert game_state.ink_played_this_turn
        assert mock_character in game_state.current_player.inkwell
    
    def test_execute_play_character(self, game_state, mock_character):
        """Test executing play character action."""
        engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
        game_state.current_phase = Phase.PLAY
        
        # Give player enough ink
        game_state.current_player.inkwell = [mock_character] * 3
        
        # Should succeed
        result = engine.execute_action(
            "play_character",
            {'card': mock_character}
        )
        
        assert result.success
        assert result.action_type == "play_character"
        assert mock_character in game_state.current_player.characters_in_play
    
    def test_execute_invalid_action(self, game_state, mock_character):
        """Test executing invalid action fails."""
        engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
        game_state.current_phase = Phase.READY  # Can't play characters in ready phase
        
        result = engine.execute_action(
            "play_character",
            {'card': mock_character}
        )
        
        assert not result.success
        assert result.error_message is not None