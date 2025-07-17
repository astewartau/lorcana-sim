"""Test that quest and challenge rules are enforced correctly."""

import pytest

from lorcana_sim.models.game.game_state import GameState, GameAction
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.engine.step_system import ExecutionMode


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


def test_character_cannot_quest_and_challenge_same_turn():
    """Test that a character cannot both quest and challenge in the same turn."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    attacker = create_test_character("Attacker", cost=1, strength=2, willpower=2, lore=1)
    defender = create_test_character("Defender", cost=1, strength=1, willpower=3, lore=1)
    
    # Set up game state
    attacker.controller = player1
    defender.controller = player2
    
    # Make characters ready and dry (can act)
    attacker.exerted = False
    attacker.is_dry = True
    defender.exerted = False
    defender.is_dry = True
    
    # Put characters in play
    player1.characters_in_play = [attacker]
    player2.characters_in_play = [defender]
    
    # Set up game
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn so characters can act
    
    # Give players enough ink by adding cards to inkwell
    for _ in range(5):
        ink_card = create_test_character(f"Ink{_}", cost=1)
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    # First action: Quest with the attacker
    quest_result = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': attacker})
    assert quest_result.success, f"Quest should succeed: {quest_result.error_message}"
    assert attacker.exerted, "Character should be exerted after questing"
    
    # Second action: Try to challenge with the same character - this should FAIL
    challenge_result = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
        'attacker': attacker, 
        'defender': defender
    })
    
    # This should fail because the character is already exerted from questing
    assert not challenge_result.success, "Character should not be able to challenge after questing in the same turn"
    # Now that we have explicit tracking, the error message should mention already acted
    assert ("not legal" in challenge_result.error_message.lower() or 
            "already acted" in challenge_result.error_message.lower()), \
        f"Error message should mention not legal or already acted: {challenge_result.error_message}"


def test_character_cannot_challenge_and_quest_same_turn():
    """Test that a character cannot challenge then quest in the same turn."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    attacker = create_test_character("Attacker", cost=1, strength=2, willpower=2, lore=1)
    defender = create_test_character("Defender", cost=1, strength=1, willpower=3, lore=1)
    
    # Set up game state
    attacker.controller = player1
    defender.controller = player2
    
    # Make attacker ready and defender exerted (challengeable)
    attacker.exerted = False
    attacker.is_dry = True
    defender.exerted = True  # Defender must be exerted to be challengeable
    defender.is_dry = True
    
    # Put characters in play
    player1.characters_in_play = [attacker]
    player2.characters_in_play = [defender]
    
    # Set up game
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn so characters can act
    
    # Give players enough ink by adding cards to inkwell
    for _ in range(5):
        ink_card = create_test_character(f"Ink{_}", cost=1)
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    # First action: Challenge with the attacker
    challenge_result = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
        'attacker': attacker, 
        'defender': defender
    })
    assert challenge_result.success, f"Challenge should succeed: {challenge_result.error_message}"
    assert attacker.exerted, "Character should be exerted after challenging"
    
    # Second action: Try to quest with the same character - this should FAIL
    quest_result = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': attacker})
    
    # This should fail because the character is already exerted from challenging
    assert not quest_result.success, "Character should not be able to quest after challenging in the same turn"
    assert "exerted" in quest_result.error_message.lower() or "already acted" in quest_result.error_message.lower(), \
        f"Error message should mention exertion: {quest_result.error_message}"


def test_exerted_character_cannot_quest():
    """Test that an exerted character cannot quest."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create character
    character = create_test_character("Test Character", cost=1, strength=2, willpower=2, lore=1)
    character.controller = player1
    character.exerted = True  # Already exerted
    character.is_dry = True
    
    # Put character in play
    player1.characters_in_play = [character]
    
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
    
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    # Try to quest with exerted character - should fail
    quest_result = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': character})
    assert not quest_result.success, "Exerted character should not be able to quest"
    assert "not legal" in quest_result.error_message.lower(), \
        f"Error message should mention action not being legal: {quest_result.error_message}"


def test_exerted_character_cannot_challenge():
    """Test that an exerted character cannot challenge."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    attacker = create_test_character("Attacker", cost=1, strength=2, willpower=2, lore=1)
    defender = create_test_character("Defender", cost=1, strength=1, willpower=3, lore=1)
    
    attacker.controller = player1
    defender.controller = player2
    
    # Attacker is exerted, defender is ready
    attacker.exerted = True  # Already exerted
    attacker.is_dry = True
    defender.exerted = False
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
    
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    # Try to challenge with exerted character - should fail
    challenge_result = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
        'attacker': attacker, 
        'defender': defender
    })
    assert not challenge_result.success, "Exerted character should not be able to challenge"
    assert "not legal" in challenge_result.error_message.lower(), \
        f"Error message should mention action not being legal: {challenge_result.error_message}"


def test_multiple_actions_in_sequence():
    """Test that demonstrates the bug: using get_all_legal_actions like the full game example does."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    helga = create_test_character("Helga Sinclair", cost=3, strength=4, willpower=3, lore=1)
    anna = create_test_character("Anna", cost=3, strength=2, willpower=4, lore=1)
    
    # Set up game state
    helga.controller = player1
    anna.controller = player2
    
    # Make characters ready and dry (can act)
    helga.exerted = False
    helga.is_dry = True
    anna.exerted = False
    anna.is_dry = True
    
    # Put characters in play
    player1.characters_in_play = [helga]
    player2.characters_in_play = [anna]
    
    # Set up game
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn so characters can act
    
    # Give players enough ink by adding cards to inkwell
    for _ in range(5):
        ink_card = create_test_character(f"Ink{_}", cost=1)
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    # Check initial legal actions - should include both quest and challenge for Helga
    legal_actions = engine.validator.get_all_legal_actions()
    quest_actions = [a for a, p in legal_actions if a == GameAction.QUEST_CHARACTER and p.get('character') == helga]
    challenge_actions = [a for a, p in legal_actions if a == GameAction.CHALLENGE_CHARACTER and p.get('attacker') == helga]
    
    print(f"Initial quest actions for Helga: {len(quest_actions)}")
    print(f"Initial challenge actions for Helga: {len(challenge_actions)}")
    
    # Action 1: Quest with Helga (simulating game loop)
    quest_result = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': helga})
    assert quest_result.success, f"Quest should succeed: {quest_result.error_message}"
    assert helga.exerted, "Character should be exerted after questing"
    print(f"After quest: Helga exerted = {helga.exerted}")
    
    # Check legal actions again - should NOT include challenge for Helga since she's exerted
    legal_actions = engine.validator.get_all_legal_actions()
    quest_actions = [a for a, p in legal_actions if a == GameAction.QUEST_CHARACTER and p.get('character') == helga]
    challenge_actions = [a for a, p in legal_actions if a == GameAction.CHALLENGE_CHARACTER and p.get('attacker') == helga]
    
    print(f"After quest - quest actions for Helga: {len(quest_actions)}")
    print(f"After quest - challenge actions for Helga: {len(challenge_actions)}")
    
    # This is where the bug would manifest - if challenge_actions > 0, that's the bug
    if len(challenge_actions) > 0:
        print("🚨 BUG DETECTED: Challenge actions still available for exerted character!")
        # Try to execute the challenge to see if it actually works
        challenge_params = next(p for a, p in legal_actions if a == GameAction.CHALLENGE_CHARACTER and p.get('attacker') == helga)
        challenge_result = engine.execute_action(GameAction.CHALLENGE_CHARACTER, challenge_params)
        print(f"Challenge result: {challenge_result.success}, message: {challenge_result.error_message}")
        
        assert False, "BUG: Challenge actions are available for exerted character"
    else:
        print("✅ Rule correctly enforced: No challenge actions available for exerted character")


def test_rush_character_cannot_act_twice():
    """Test that a character with Rush still cannot quest and challenge in the same turn."""
    from lorcana_sim.models.abilities.composable.keyword_abilities import create_rush_ability
    
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters
    rush_char = create_test_character("Rush Character", cost=3, strength=4, willpower=3, lore=1)
    defender = create_test_character("Defender", cost=3, strength=2, willpower=4, lore=1)
    
    # Give the character Rush ability
    rush_char.composable_abilities = [create_rush_ability(rush_char)]
    
    # Set up game state
    rush_char.controller = player1
    defender.controller = player2
    
    # Make characters ready and dry (can act)
    rush_char.exerted = False
    rush_char.is_dry = True
    defender.exerted = False
    defender.is_dry = True
    
    # Put characters in play
    player1.characters_in_play = [rush_char]
    player2.characters_in_play = [defender]
    
    # Set up game
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2  # Not first turn so characters can act
    
    # Give players enough ink by adding cards to inkwell
    for _ in range(5):
        ink_card = create_test_character(f"Ink{_}", cost=1)
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    # Give players some deck cards to avoid game over
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    # Verify Rush character can challenge initially
    assert rush_char.has_rush_ability(), "Character should have Rush ability"
    assert rush_char.can_challenge(game_state.turn_number), "Rush character should be able to challenge"
    
    # Action 1: Quest with Rush character
    quest_result = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': rush_char})
    assert quest_result.success, f"Quest should succeed: {quest_result.error_message}"
    assert rush_char.exerted, "Character should be exerted after questing"
    print(f"After quest: Rush character exerted = {rush_char.exerted}")
    
    # Check if character can still challenge after being exerted (this would be the bug)
    can_challenge_after_quest = rush_char.can_challenge(game_state.turn_number)
    print(f"Can challenge after quest: {can_challenge_after_quest}")
    
    if can_challenge_after_quest:
        print("🚨 BUG DETECTED: Rush character can challenge while exerted!")
        # Try to execute the challenge
        challenge_result = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': rush_char, 
            'defender': defender
        })
        print(f"Challenge result: {challenge_result.success}")
        
        if challenge_result.success:
            assert False, "BUG: Rush character should not be able to challenge after questing (exerted characters cannot act)"
    else:
        print("✅ Rule correctly enforced: Rush character cannot challenge while exerted")


def test_fix_prevents_double_action_bug():
    """Test that the fix prevents the double action bug that was occurring in the full game example."""
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create characters (simulating Helga Sinclair and Anna from the example)
    helga = create_test_character("Helga Sinclair", cost=3, strength=4, willpower=3, lore=1)
    anna = create_test_character("Anna", cost=3, strength=2, willpower=4, lore=1)
    
    # Set up game state
    helga.controller = player1
    anna.controller = player2
    
    helga.exerted = False
    helga.is_dry = True
    anna.exerted = True  # Anna must be exerted to be challengeable
    anna.is_dry = True
    
    player1.characters_in_play = [helga]
    player2.characters_in_play = [anna]
    
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0
    game_state.current_phase = game_state.current_phase.PLAY
    game_state.turn_number = 2
    
    # Give players ink and deck cards
    for _ in range(5):
        ink_card = create_test_character(f"Ink{_}", cost=1)
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    for _ in range(10):
        deck_card = create_test_character(f"Deck{_}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    # Simulate the game loop that was causing the bug:
    # 1. Get legal actions (should include quest and challenge for Helga)
    # 2. Execute quest
    # 3. Get legal actions again (should NOT include any actions for Helga)
    
    # Step 1: Get initial legal actions
    legal_actions_1 = engine.validator.get_all_legal_actions()
    helga_quest_actions_1 = [a for a, p in legal_actions_1 if a == GameAction.QUEST_CHARACTER and p.get('character') == helga]
    helga_challenge_actions_1 = [a for a, p in legal_actions_1 if a == GameAction.CHALLENGE_CHARACTER and p.get('attacker') == helga]
    
    assert len(helga_quest_actions_1) == 1, "Helga should be able to quest initially"
    assert len(helga_challenge_actions_1) == 1, "Helga should be able to challenge initially"
    
    # Step 2: Execute quest
    quest_result = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': helga})
    assert quest_result.success, "Quest should succeed"
    assert helga.exerted, "Helga should be exerted after questing"
    assert game_state.has_character_acted_this_turn(helga.id), "Helga should be marked as having acted"
    
    # Step 3: Get legal actions again - THIS IS WHERE THE BUG WAS
    legal_actions_2 = engine.validator.get_all_legal_actions()
    helga_quest_actions_2 = [a for a, p in legal_actions_2 if a == GameAction.QUEST_CHARACTER and p.get('character') == helga]
    helga_challenge_actions_2 = [a for a, p in legal_actions_2 if a == GameAction.CHALLENGE_CHARACTER and p.get('attacker') == helga]
    
    # With the fix, both should be 0
    assert len(helga_quest_actions_2) == 0, "Helga should NOT be able to quest after already acting"
    assert len(helga_challenge_actions_2) == 0, "Helga should NOT be able to challenge after already acting"
    
    # Step 4: Try to execute challenge anyway (should fail with specific error)
    challenge_result = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
        'attacker': helga, 
        'defender': anna
    })
    
    assert not challenge_result.success, "Challenge should fail"
    # Either the validator prevents it (not legal) or the engine prevents it (already acted)
    assert ("already acted" in challenge_result.error_message.lower() or 
            "not legal" in challenge_result.error_message.lower()), \
        f"Error should mention not legal or already acted: {challenge_result.error_message}"
    
    print("✅ Fix successfully prevents double action bug")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])