"""Test challenge mechanics including exertion and restrictions."""

import pytest

from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.engine.game_moves import ChallengeMove, QuestMove


def create_test_character(name: str, cost: int = 3, strength: int = 2, willpower: int = 3, lore: int = 1) -> CharacterCard:
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


def test_character_becomes_exerted_after_challenging():
    """Test that a character becomes exerted after successfully challenging another character."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    attacker = create_test_character("Brave Knight", cost=3, strength=4, willpower=3, lore=1)
    defender = create_test_character("Guard", cost=2, strength=2, willpower=2, lore=1)
    
    # Set up game state
    attacker.controller = player1
    defender.controller = player2
    
    # Make attacker ready and dry (can act)
    attacker.exerted = False
    attacker.is_dry = True
    
    # Defender must be exerted to be challengeable
    defender.exerted = True
    defender.is_dry = True
    
    # Put characters in play
    player1.characters_in_play = [attacker]
    player2.characters_in_play = [defender]
    
    # Set up game
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn so characters can act
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    engine = GameEngine(game_state)
    
    # Verify initial state
    assert not attacker.exerted, "Attacker should start ready (not exerted)"
    assert defender.exerted, "Defender should be exerted (challengeable)"
    
    # Execute challenge using the same path as the game (ChallengeMove)
    challenge_move = ChallengeMove(attacker=attacker, defender=defender)
    
    # Process the move through the game engine (this is what the UI does)
    message = engine.next_message(challenge_move)
    assert message is not None, "Should get a message after processing challenge move"
    
    # MAIN TEST: Verify attacker is now exerted
    assert attacker.exerted, "Attacker should be exerted after challenging"


def test_exerted_character_cannot_initiate_challenge():
    """Test that an exerted character cannot start a challenge."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    attacker = create_test_character("Tired Warrior", cost=3, strength=3, willpower=4, lore=1)
    defender = create_test_character("Fresh Guard", cost=2, strength=2, willpower=3, lore=1)
    
    # Set up game state
    attacker.controller = player1
    defender.controller = player2
    
    # MAIN SETUP: Attacker is already exerted
    attacker.exerted = True
    attacker.is_dry = True
    
    # Defender is exerted (challengeable)
    defender.exerted = True
    defender.is_dry = True
    
    # Put characters in play
    player1.characters_in_play = [attacker]
    player2.characters_in_play = [defender]
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    # Set up game
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn
    
    engine = GameEngine(game_state)
    
    # Verify initial state
    assert attacker.exerted, "Attacker should be exerted"
    assert defender.exerted, "Defender should be exerted (challengeable)"
    
    # Try to challenge with exerted character - should FAIL
    challenge_result = engine.execute_action("challenge_character", {
        'attacker': attacker, 
        'defender': defender
    })
    
    # MAIN TEST: Verify challenge failed
    assert not challenge_result.success, "Exerted character should not be able to initiate a challenge"
    
    # Verify error message mentions the issue
    assert "not legal" in challenge_result.error_message.lower(), \
        f"Error message should mention action not being legal: {challenge_result.error_message}"
    
    # Verify no damage was dealt
    assert defender.current_willpower == defender.willpower, "No damage should be dealt when challenge fails"
    assert attacker.current_willpower == attacker.willpower, "No damage should be dealt when challenge fails"


def test_character_cannot_challenge_same_turn_as_playing():
    """Test that a character cannot challenge on the same turn it was played (without Rush)."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    new_char = create_test_character("Eager Fighter", cost=2, strength=3, willpower=2, lore=1)
    new_char.controller = player1
    defender = create_test_character("Defender", cost=2, strength=2, willpower=3, lore=1)
    
    # Give the new character to player1's hand
    player1.hand = [new_char]
    
    # Set up defender
    defender.controller = player2
    defender.exerted = True  # Defender must be exerted to be challengeable
    defender.is_dry = True
    player2.characters_in_play = [defender]
    
    # Set up game state
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn
    
    # Give players enough ink by adding cards to inkwell
    for _ in range(3):
        ink_card = create_test_character(f"Ink{_}", cost=1)
        player1.inkwell.append(ink_card)
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    engine = GameEngine(game_state)
    
    # Play the character
    play_result = engine.execute_action("play_character", {
        'card': new_char
    })
    assert play_result.success, f"Play should succeed: {play_result.error_message}"
    assert new_char in player1.characters_in_play, "Character should be in play"
    
    # Verify character has wet ink (is_dry = False)
    assert not new_char.is_dry, "Freshly played character should have wet ink"
    assert not new_char.exerted, "Freshly played character should not be exerted"
    
    # Try to challenge with the freshly played character - should FAIL
    challenge_result = engine.execute_action("challenge_character", {
        'attacker': new_char,
        'defender': defender
    })
    
    # MAIN TEST: Verify challenge failed
    assert not challenge_result.success, "Freshly played character should not be able to challenge"
    assert "not legal" in challenge_result.error_message.lower(), \
        f"Error message should mention action not being legal: {challenge_result.error_message}"
    
    # Verify character is still not exerted (since challenge didn't happen)
    assert not new_char.exerted, "Character should not be exerted since challenge failed"
    
    # Verify no damage was dealt
    assert defender.current_willpower == defender.willpower, "No damage should be dealt when challenge fails"
    assert new_char.current_willpower == new_char.willpower, "No damage should be dealt when challenge fails"


def test_multiple_challenges_in_one_turn():
    """Test that multiple different characters can challenge in the same turn."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create multiple attackers and defenders
    attacker1 = create_test_character("Knight 1", cost=2, strength=3, willpower=2, lore=1)
    attacker2 = create_test_character("Knight 2", cost=3, strength=4, willpower=3, lore=1)
    defender1 = create_test_character("Guard 1", cost=2, strength=2, willpower=2, lore=1)
    defender2 = create_test_character("Guard 2", cost=2, strength=2, willpower=3, lore=1)
    
    # Set up game state
    attacker1.controller = player1
    attacker2.controller = player1
    defender1.controller = player2
    defender2.controller = player2
    
    # Make all characters ready and dry
    for char in [attacker1, attacker2, defender1, defender2]:
        char.is_dry = True
    
    # Attackers ready, defenders exerted (challengeable)
    attacker1.exerted = False
    attacker2.exerted = False
    defender1.exerted = True
    defender2.exerted = True
    
    # Put characters in play
    player1.characters_in_play = [attacker1, attacker2]
    player2.characters_in_play = [defender1, defender2]
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    # Set up game
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn
    
    engine = GameEngine(game_state)
    
    # First challenge: attacker1 vs defender1
    challenge1_result = engine.execute_action("challenge_character", {
        'attacker': attacker1, 
        'defender': defender1
    })
    assert challenge1_result.success, f"First challenge should succeed: {challenge1_result.error_message}"
    assert attacker1.exerted, "First attacker should be exerted after challenging"
    
    # Second challenge: attacker2 vs defender2
    challenge2_result = engine.execute_action("challenge_character", {
        'attacker': attacker2, 
        'defender': defender2
    })
    assert challenge2_result.success, f"Second challenge should succeed: {challenge2_result.error_message}"
    assert attacker2.exerted, "Second attacker should be exerted after challenging"
    
    # Verify first attacker cannot challenge again
    challenge3_result = engine.execute_action("challenge_character", {
        'attacker': attacker1, 
        'defender': defender2
    })
    assert not challenge3_result.success, "Exerted character should not be able to challenge again"


def test_character_cannot_quest_after_challenging_same_turn():
    """Test that a character cannot quest after challenging in the same turn using game moves."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    attacker = create_test_character("Versatile Hero", cost=3, strength=3, willpower=4, lore=2)
    defender = create_test_character("Guard", cost=2, strength=2, willpower=2, lore=1)
    
    # Set up game state
    attacker.controller = player1
    defender.controller = player2
    
    # Make attacker ready and dry (can act)
    attacker.exerted = False
    attacker.is_dry = True
    
    # Defender must be exerted to be challengeable
    defender.exerted = True
    defender.is_dry = True
    
    # Put characters in play
    player1.characters_in_play = [attacker]
    player2.characters_in_play = [defender]
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    # Set up game
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn
    
    engine = GameEngine(game_state)
    
    # First action: Challenge with the attacker
    challenge_move = ChallengeMove(attacker=attacker, defender=defender)
    challenge_message = engine.next_message(challenge_move)
    assert challenge_message is not None, "Should get a message after challenge"
    
    # Verify attacker is exerted
    assert attacker.exerted, "Attacker should be exerted after challenging"
    
    # Second action: Try to quest with the same character - should FAIL
    # Check if character is marked as having acted
    assert game_state.has_character_acted_this_turn(attacker.id), "Character should be marked as having acted"
    
    # Try to get legal actions - quest should not be available for this character
    legal_actions = engine.validator.get_all_legal_actions()
    quest_actions = [a for a, p in legal_actions if a == "quest_character" and p.get('character') == attacker]
    
    assert len(quest_actions) == 0, "Character should not be able to quest after challenging in the same turn"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])