"""Test that freshly played characters cannot quest or challenge on the same turn."""

import pytest

from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_engine import GameEngine

from lorcana_sim.models.abilities.composable.keyword_abilities import create_rush_ability


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


def test_freshly_played_character_cannot_quest():
    """Test that a character played this turn cannot quest."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    fresh_char = create_test_character("Fresh Character", cost=1, strength=2, willpower=2, lore=1)
    fresh_char.controller = player1
    
    # Give the character to player1's hand
    player1.hand = [fresh_char]
    
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
        'card': fresh_char
    })
    assert play_result.success, f"Play should succeed: {play_result.error_message}"
    assert fresh_char in player1.characters_in_play, "Character should be in play"
    
    # Verify character has wet ink (is_dry = False)
    assert not fresh_char.is_dry, "Freshly played character should have wet ink"
    
    # Try to quest with the freshly played character - should fail
    quest_result = engine.execute_action("quest_character", {'character': fresh_char})
    assert not quest_result.success, "Freshly played character should not be able to quest"
    assert "not legal" in quest_result.error_message.lower(), \
        f"Error message should mention action not being legal: {quest_result.error_message}"
    
    # Verify character cannot quest due to wet ink
    assert not fresh_char.can_quest(game_state.turn_number), "Character should not be able to quest with wet ink"


def test_freshly_played_character_cannot_challenge():
    """Test that a character played this turn cannot challenge."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    fresh_char = create_test_character("Fresh Character", cost=1, strength=2, willpower=2, lore=1)
    fresh_char.controller = player1
    defender = create_test_character("Defender", cost=1, strength=1, willpower=3, lore=1)
    
    # Give the character to player1's hand
    player1.hand = [fresh_char]
    
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
        'card': fresh_char
    })
    assert play_result.success, f"Play should succeed: {play_result.error_message}"
    assert fresh_char in player1.characters_in_play, "Character should be in play"
    
    # Verify character has wet ink (is_dry = False)
    assert not fresh_char.is_dry, "Freshly played character should have wet ink"
    
    # Try to challenge with the freshly played character - should fail
    challenge_result = engine.execute_action("challenge_character", {
        'attacker': fresh_char,
        'defender': defender
    })
    assert not challenge_result.success, "Freshly played character should not be able to challenge"
    assert "not legal" in challenge_result.error_message.lower(), \
        f"Error message should mention action not being legal: {challenge_result.error_message}"
    
    # Verify character cannot challenge due to wet ink
    assert not fresh_char.can_challenge(game_state.turn_number), "Character should not be able to challenge with wet ink"


def test_rush_character_can_challenge_when_freshly_played():
    """Test that a character with Rush can challenge on the turn it's played."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    rush_char = create_test_character("Rush Character", cost=1, strength=2, willpower=2, lore=1)
    rush_char.controller = player1
    defender = create_test_character("Defender", cost=1, strength=1, willpower=3, lore=1)
    
    # Give the character Rush ability
    rush_char.composable_abilities = [create_rush_ability(rush_char)]
    
    # Give the character to player1's hand
    player1.hand = [rush_char]
    
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
        'card': rush_char
    })
    assert play_result.success, f"Play should succeed: {play_result.error_message}"
    assert rush_char in player1.characters_in_play, "Character should be in play"
    
    # Verify character has wet ink but Rush ability
    assert not rush_char.is_dry, "Freshly played character should have wet ink"
    assert rush_char.has_rush_ability(), "Character should have Rush ability"
    
    # Verify character CAN challenge due to Rush despite wet ink
    assert rush_char.can_challenge(game_state.turn_number), "Rush character should be able to challenge with wet ink"
    
    # Try to challenge with the Rush character - should succeed
    challenge_result = engine.execute_action("challenge_character", {
        'attacker': rush_char,
        'defender': defender
    })
    assert challenge_result.success, f"Rush character should be able to challenge: {challenge_result.error_message}"
    assert rush_char.exerted, "Character should be exerted after challenging"


def test_rush_character_cannot_quest_when_freshly_played():
    """Test that a character with Rush still cannot quest on the turn it's played."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    rush_char = create_test_character("Rush Character", cost=1, strength=2, willpower=2, lore=1)
    rush_char.controller = player1
    
    # Give the character Rush ability
    rush_char.composable_abilities = [create_rush_ability(rush_char)]
    
    # Give the character to player1's hand
    player1.hand = [rush_char]
    
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
        'card': rush_char
    })
    assert play_result.success, f"Play should succeed: {play_result.error_message}"
    assert rush_char in player1.characters_in_play, "Character should be in play"
    
    # Verify character has wet ink
    assert not rush_char.is_dry, "Freshly played character should have wet ink"
    assert rush_char.has_rush_ability(), "Character should have Rush ability"
    
    # Try to quest with the Rush character - should still fail
    quest_result = engine.execute_action("quest_character", {'character': rush_char})
    assert not quest_result.success, "Rush character should not be able to quest with wet ink"
    assert "not legal" in quest_result.error_message.lower(), \
        f"Error message should mention action not being legal: {quest_result.error_message}"
    
    # Verify character cannot quest due to wet ink (Rush doesn't help with questing)
    assert not rush_char.can_quest(game_state.turn_number), "Rush character should not be able to quest with wet ink"


def test_character_can_act_after_ink_dries():
    """Test that a character can quest and challenge after ink dries (manually set)."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters - manually set with dry ink to simulate dried character
    char = create_test_character("Test Character", cost=1, strength=2, willpower=2, lore=1)
    char.controller = player1
    char.is_dry = True  # Manually set to dry to simulate after ink drying event
    player1.characters_in_play = [char]
    
    defender = create_test_character("Defender", cost=1, strength=1, willpower=3, lore=1)
    defender.controller = player2
    defender.exerted = True  # Defender must be exerted to be challengeable
    defender.is_dry = True
    player2.characters_in_play = [defender]
    
    # Set up game state
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 3
    
    # Give players enough ink by adding cards to inkwell
    for _ in range(3):
        ink_card = create_test_character(f"Ink{_}", cost=1)
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    engine = GameEngine(game_state)
    
    # Verify character has dry ink
    assert char.is_dry, "Character should have dry ink"
    
    # Now character should be able to quest
    assert char.can_quest(game_state.turn_number), "Character should be able to quest after ink dries"
    
    quest_result = engine.execute_action("quest_character", {'character': char})
    assert quest_result.success, f"Character should be able to quest after ink dries: {quest_result.error_message}"
    assert char.exerted, "Character should be exerted after questing"
    
    # Verify that character can also challenge after ink dries (without actually doing it since we already quested)
    char_copy = create_test_character("Test Character Copy", cost=1, strength=2, willpower=2, lore=1)
    char_copy.controller = player1
    char_copy.is_dry = True  # Dry ink
    
    assert char_copy.can_challenge(game_state.turn_number), "Character should be able to challenge after ink dries"


def test_legal_actions_exclude_wet_ink_characters():
    """Test that get_all_legal_actions excludes quest/challenge for wet ink characters."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    fresh_char = create_test_character("Fresh Character", cost=1, strength=2, willpower=2, lore=1)
    fresh_char.controller = player1
    dry_char = create_test_character("Dry Character", cost=1, strength=2, willpower=2, lore=1)
    defender = create_test_character("Defender", cost=1, strength=1, willpower=3, lore=1)
    
    # Give fresh character to player1's hand
    player1.hand = [fresh_char]
    
    # Set up dry character already in play
    dry_char.controller = player1
    dry_char.is_dry = True
    dry_char.exerted = False
    player1.characters_in_play = [dry_char]
    
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
    
    # Get legal actions before playing fresh character
    legal_actions_before = engine.validator.get_all_legal_actions()
    dry_quest_actions = [a for a, p in legal_actions_before if a == "quest_character" and p.get('character') == dry_char]
    dry_challenge_actions = [a for a, p in legal_actions_before if a == "challenge_character" and p.get('attacker') == dry_char]
    
    assert len(dry_quest_actions) == 1, "Dry character should be able to quest"
    assert len(dry_challenge_actions) == 1, "Dry character should be able to challenge"
    
    # Play the fresh character
    play_result = engine.execute_action("play_character", {
        'card': fresh_char
    })
    assert play_result.success, f"Play should succeed: {play_result.error_message}"
    assert fresh_char in player1.characters_in_play, "Character should be in play"
    assert not fresh_char.is_dry, "Freshly played character should have wet ink"
    
    # Get legal actions after playing fresh character
    legal_actions_after = engine.validator.get_all_legal_actions()
    fresh_quest_actions = [a for a, p in legal_actions_after if a == "quest_character" and p.get('character') == fresh_char]
    fresh_challenge_actions = [a for a, p in legal_actions_after if a == "challenge_character" and p.get('attacker') == fresh_char]
    
    # Fresh character should NOT appear in legal actions
    assert len(fresh_quest_actions) == 0, "Fresh character should NOT be able to quest"
    assert len(fresh_challenge_actions) == 0, "Fresh character should NOT be able to challenge"
    
    # Dry character should still be able to act
    dry_quest_actions_after = [a for a, p in legal_actions_after if a == "quest_character" and p.get('character') == dry_char]
    dry_challenge_actions_after = [a for a, p in legal_actions_after if a == "challenge_character" and p.get('attacker') == dry_char]
    
    assert len(dry_quest_actions_after) == 1, "Dry character should still be able to quest"
    assert len(dry_challenge_actions_after) == 1, "Dry character should still be able to challenge"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])