"""Test ink drying across turns to verify event-driven wet ink system works properly."""

import sys
sys.path.insert(0, 'src')

from lorcana_sim.models.game.game_state import GameState, Phase
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.engine.game_moves import PlayMove, PassMove
from lorcana_sim.engine.game_messages import MessageType


def create_test_character(name: str, cost: int = 1, strength: int = 2, willpower: int = 3, lore: int = 1) -> CharacterCard:
    """Create a test character card."""
    return CharacterCard(
        id=hash(name) % 10000,
        name=name,
        version="Test Version",
        full_name=f"{name} - Test Version",
        cost=cost,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test",
        strength=strength,
        willpower=willpower,
        lore=lore,
        subtypes=["Hero"]
    )


def test_ink_dries_after_owners_next_ready_phase():
    """Test that character ink dries during the owner's next ready phase."""
    print("\n=== Testing Ink Drying Across Turns ===")
    
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create test character
    test_char = create_test_character("Test Character", cost=1, strength=2, willpower=2, lore=1)
    test_char.controller = player1
    
    # Give the character to player1's hand
    player1.hand = [test_char]
    
    # Set up game state starting on player1's turn
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = Phase.PLAY
    game_state.turn_number = 2  # Not first turn
    
    # Give players enough ink
    for i in range(3):
        ink_card = create_test_character(f"Ink{i}", cost=1)
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    # Give players some deck cards
    for i in range(10):
        deck_card = create_test_character(f"Deck{i}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    # Create game engine
    engine = GameEngine(game_state)
    
    print(f"Turn {game_state.turn_number}, Player 1's turn")
    print(f"Initial state - Character in hand: {test_char.name}")
    
    # === PLAYER 1's TURN: Play the character ===
    
    # Get initial message
    initial_msg = engine.next_message()
    assert initial_msg.type == MessageType.ACTION_REQUIRED
    
    # Play the character
    play_move = PlayMove(test_char)
    play_result = engine.next_message(play_move)
    
    # Process all effects until we get ACTION_REQUIRED
    print("Processing effects after playing character...")
    while True:
        msg = engine.next_message()
        print(f"  Message: {msg.type} - {getattr(msg, 'step', 'no step')}")
        if msg.type == MessageType.ACTION_REQUIRED:
            break
    
    # Character should be in play with wet ink
    assert test_char in player1.characters_in_play, "Character should be in play"
    assert not test_char.is_dry, "Character should have wet ink when just played"
    print(f"✅ Character played with wet ink: is_dry={test_char.is_dry}")
    
    # Pass turn (end player 1's turn)
    pass_move = PassMove()
    engine.next_message(pass_move)
    
    # Process all effects until we get ACTION_REQUIRED (player 2's turn)
    print("Processing effects during turn transition to player 2...")
    while True:
        msg = engine.next_message()
        print(f"  Message: {msg.type} - {getattr(msg, 'step', 'no step')}")
        if msg.type == MessageType.ACTION_REQUIRED:
            break
    
    print(f"Turn {game_state.turn_number}, Player 2's turn")
    print(f"After player 1 ended turn: is_dry={test_char.is_dry}")
    
    # Character should still have wet ink (it's player 2's turn)
    assert not test_char.is_dry, "Character should still have wet ink during opponent's turn"
    
    # === PLAYER 2's TURN: Pass ===
    
    # Pass turn (end player 2's turn)
    pass_move = PassMove()
    pass_result = engine.next_message(pass_move)
    print(f"Pass turn result: {pass_result.type} - {getattr(pass_result, 'step', 'no step')}")
    
    # Process all effects until we get ACTION_REQUIRED (back to player 1's turn)
    print("Processing effects during turn transition back to player 1 (where ink should dry)...")
    while True:
        msg = engine.next_message()
        print(f"  Message: {msg.type} - {getattr(msg, 'step', 'no step')}")
        if msg.type == MessageType.ACTION_REQUIRED:
            break
    
    print(f"Turn {game_state.turn_number}, Player 1's turn again")
    print(f"After player 2 ended turn: is_dry={test_char.is_dry}")
    
    # === CRITICAL TEST: Character should now have dry ink ===
    # This is where the test should pass but currently fails
    assert test_char.is_dry, f"Character should have dry ink after owner's next ready phase! is_dry={test_char.is_dry}"
    
    print(f"✅ SUCCESS: Character ink dried after owner's next ready phase")


def test_ink_drying_detailed_phases():
    """More detailed test that tracks ink status through each phase."""
    print("\n=== Testing Ink Drying Through Detailed Phases ===")
    
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create test character
    test_char = create_test_character("Test Character", cost=1)
    test_char.controller = player1
    player1.hand = [test_char]
    
    # Set up game state
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0
    game_state.current_phase = Phase.PLAY
    game_state.turn_number = 2
    
    # Give players ink and deck
    for i in range(5):
        player1.inkwell.append(create_test_character(f"Ink{i}"))
        player2.inkwell.append(create_test_character(f"Ink{i}"))
        player1.deck.append(create_test_character(f"Deck{i}"))
        player2.deck.append(create_test_character(f"Deck{i}"))
    
    engine = GameEngine(game_state)
    
    # Play character on player 1's turn
    initial_msg = engine.next_message()
    assert initial_msg.type == MessageType.ACTION_REQUIRED
    
    play_move = PlayMove(test_char)
    engine.next_message(play_move)
    
    # Process all effects
    while True:
        msg = engine.next_message()
        if msg.type == MessageType.ACTION_REQUIRED:
            break
    
    print(f"Character played on turn {game_state.turn_number}: is_dry={test_char.is_dry}")
    assert not test_char.is_dry, "Character should start with wet ink"
    
    # Pass through player 1's turn and player 2's entire turn
    # to get back to player 1's ready phase
    
    # End player 1's turn
    engine.next_message(PassMove())
    while True:
        msg = engine.next_message()
        if msg.type == MessageType.ACTION_REQUIRED:
            break
    
    print(f"Player 2's turn (turn {game_state.turn_number}): is_dry={test_char.is_dry}")
    assert not test_char.is_dry, "Character should still have wet ink during opponent's turn"
    
    # End player 2's turn - this should trigger player 1's ready phase with ink drying
    engine.next_message(PassMove())
    while True:
        msg = engine.next_message()
        if msg.type == MessageType.ACTION_REQUIRED:
            break
    
    print(f"Back to player 1's turn (turn {game_state.turn_number}): is_dry={test_char.is_dry}")
    print(f"Current phase: {game_state.current_phase}")
    
    # This is the key assertion - character should have dry ink now
    assert test_char.is_dry, f"Character should have dry ink after owner's next ready phase! is_dry={test_char.is_dry}"
    
    print("✅ SUCCESS: Character ink dried correctly")


if __name__ == "__main__":
    test_ink_dries_after_owners_next_ready_phase()
    test_ink_drying_detailed_phases()