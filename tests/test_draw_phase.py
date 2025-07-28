"""Tests for draw phase mechanics."""

import pytest
from src.lorcana_sim.models.game.game_state import GameState, Phase
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.engine.game_moves import PassMove
from src.lorcana_sim.engine.message_engine import MessageType


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
def game_with_decks(mock_character):
    """Create a game with players that have cards in their decks."""
    player1 = Player("Alice")
    player2 = Player("Bob")
    
    # Give each player a deck with several cards
    deck_cards = []
    for i in range(10):
        card = CharacterCard(
            id=100 + i,
            name=f"Deck Card {i}",
            version=None,
            full_name=f"Deck Card {i}",
            cost=1,
            color=CardColor.AMBER,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=100 + i,
            story="",
            strength=1,
            willpower=1,
            lore=1,
            subtypes=[]
        )
        deck_cards.append(card)
    
    # Split deck cards between players
    player1.deck = deck_cards[:5].copy()
    player2.deck = deck_cards[5:].copy()
    
    # Give players initial hands (7 cards each)
    for i in range(7):
        hand_card1 = CharacterCard(
            id=200 + i,
            name=f"Hand Card P1 {i}",
            version=None,
            full_name=f"Hand Card P1 {i}",
            cost=1,
            color=CardColor.AMBER,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=200 + i,
            story="",
            strength=1,
            willpower=1,
            lore=1,
            subtypes=[]
        )
        hand_card2 = CharacterCard(
            id=300 + i,
            name=f"Hand Card P2 {i}",
            version=None,
            full_name=f"Hand Card P2 {i}",
            cost=1,
            color=CardColor.AMBER,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=300 + i,
            story="",
            strength=1,
            willpower=1,
            lore=1,
            subtypes=[]
        )
        player1.hand.append(hand_card1)
        player2.hand.append(hand_card2)
    
    game_state = GameState([player1, player2])
    return GameEngine(game_state)


def advance_to_phase(game_engine: GameEngine, target_phase: Phase, max_attempts: int = 20):
    """Helper to advance game to a specific phase."""
    attempts = 0
    while game_engine.game_state.current_phase != target_phase and attempts < max_attempts:
        try:
            message = game_engine.next_message()
            if message.type == MessageType.ACTION_REQUIRED:
                # Pass to advance phase
                game_engine.next_message(PassMove())
        except:
            break
        attempts += 1
    
    if attempts >= max_attempts:
        raise RuntimeError(f"Failed to reach {target_phase} after {max_attempts} attempts. "
                         f"Current phase: {game_engine.game_state.current_phase}")


def test_first_player_skips_draw_on_first_turn(game_with_decks):
    """Test that the first player doesn't draw a card on their first turn."""
    game_engine = game_with_decks
    game_state = game_engine.game_state
    
    # Start the game
    game_engine.start_game()
    
    # Record initial state
    player1 = game_state.players[0]
    initial_hand_size = len(player1.hand)
    initial_deck_size = len(player1.deck)
    
    # Advance to draw phase
    advance_to_phase(game_engine, Phase.DRAW)
    
    # Verify we're in draw phase and it's player 1's first turn
    assert game_state.current_phase == Phase.DRAW
    assert game_state.current_player_index == 0
    assert game_state.turn_number == 1
    
    # Process draw phase
    message = game_engine.next_message()
    
    # Player 1 should not have drawn a card on first turn
    assert len(player1.hand) == initial_hand_size
    assert len(player1.deck) == initial_deck_size


def test_second_player_draws_on_first_turn(game_with_decks):
    """Test that the second player draws a card on their first turn."""
    game_engine = game_with_decks
    game_state = game_engine.game_state
    
    # Start the game
    game_engine.start_game()
    
    # Complete player 1's first turn (should skip draw)
    while game_state.current_player_index == 0:
        try:
            message = game_engine.next_message()
            if message.type == MessageType.ACTION_REQUIRED:
                game_engine.next_message(PassMove())
        except:
            break
    
    # Now it should be player 2's turn
    assert game_state.current_player_index == 1
    player2 = game_state.players[1]
    
    # Record initial state for player 2
    initial_hand_size = len(player2.hand)
    initial_deck_size = len(player2.deck)
    
    # Advance to draw phase for player 2
    advance_to_phase(game_engine, Phase.DRAW)
    
    # Verify we're in draw phase
    assert game_state.current_phase == Phase.DRAW
    assert game_state.current_player_index == 1
    
    # Process draw phase - player 2 should draw
    message = game_engine.next_message()
    
    # Player 2 should have drawn a card
    assert len(player2.hand) == initial_hand_size + 1
    assert len(player2.deck) == initial_deck_size - 1


def test_players_draw_on_subsequent_turns(game_with_decks):
    """Test that both players draw cards on their second and subsequent turns."""
    game_engine = game_with_decks
    game_state = game_engine.game_state
    
    # Start the game
    game_engine.start_game()
    
    # Complete both players' first turns to get to turn 2
    max_cycles = 50
    cycles = 0
    while game_state.turn_number < 2 and cycles < max_cycles:
        try:
            message = game_engine.next_message()
            if message.type == MessageType.ACTION_REQUIRED:
                game_engine.next_message(PassMove())
        except:
            break
        cycles += 1
    
    # Should now be turn 2, player 1's turn
    assert game_state.turn_number == 2
    assert game_state.current_player_index == 0
    
    player1 = game_state.players[0]
    initial_hand_size = len(player1.hand)
    initial_deck_size = len(player1.deck)
    
    # Advance to draw phase
    advance_to_phase(game_engine, Phase.DRAW)
    
    # Process draw phase - player 1 should draw on turn 2
    message = game_engine.next_message()
    
    # Player 1 should have drawn a card on their second turn
    assert len(player1.hand) == initial_hand_size + 1
    assert len(player1.deck) == initial_deck_size - 1


def test_draw_phase_with_empty_deck(game_with_decks):
    """Test draw phase behavior when deck is empty."""
    game_engine = game_with_decks
    game_state = game_engine.game_state
    
    # Start the game
    game_engine.start_game()
    
    # Empty player 1's deck
    player1 = game_state.players[0]
    player1.deck.clear()
    
    # Complete player 1's first turn to get to their second turn where they should draw
    max_cycles = 50
    cycles = 0
    while game_state.turn_number < 2 and cycles < max_cycles:
        try:
            message = game_engine.next_message()
            if message.type == MessageType.ACTION_REQUIRED:
                game_engine.next_message(PassMove())
        except:
            break
        cycles += 1
    
    # Should now be turn 2, player 1's turn
    assert game_state.turn_number == 2
    assert game_state.current_player_index == 0
    
    initial_hand_size = len(player1.hand)
    
    # Advance to draw phase
    advance_to_phase(game_engine, Phase.DRAW)
    
    # Process draw phase - should handle empty deck gracefully
    message = game_engine.next_message()
    
    # Hand size should remain the same (can't draw from empty deck)
    assert len(player1.hand) == initial_hand_size
    assert len(player1.deck) == 0


def test_draw_phase_advances_to_play_phase(game_with_decks):
    """Test that the draw phase automatically advances to play phase."""
    game_engine = game_with_decks
    game_state = game_engine.game_state
    
    # Start the game and get to player 2's turn (who should draw)
    game_engine.start_game()
    
    # Complete player 1's first turn
    while game_state.current_player_index == 0:
        try:
            message = game_engine.next_message()
            if message.type == MessageType.ACTION_REQUIRED:
                game_engine.next_message(PassMove())
        except:
            break
    
    # Advance to draw phase for player 2
    advance_to_phase(game_engine, Phase.DRAW)
    assert game_state.current_phase == Phase.DRAW
    
    # Process the draw phase
    message = game_engine.next_message()
    
    # Should automatically advance to play phase
    # Continue processing until we get to PLAY phase or ACTION_REQUIRED
    max_attempts = 10
    attempts = 0
    while game_state.current_phase != Phase.PLAY and attempts < max_attempts:
        try:
            message = game_engine.next_message()
            if message.type == MessageType.ACTION_REQUIRED:
                break
        except:
            break
        attempts += 1
    
    # Should now be in PLAY phase or waiting for player action
    assert game_state.current_phase == Phase.PLAY or message.type == MessageType.ACTION_REQUIRED