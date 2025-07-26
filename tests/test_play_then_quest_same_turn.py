"""Test that reproduces the issue where characters can quest/challenge immediately after being played."""

import sys
sys.path.insert(0, 'src')

from lorcana_sim.models.game.game_state import GameState, Phase
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.engine.game_moves import PlayMove, QuestMove, ChallengeMove
from lorcana_sim.engine.game_messages import MessageType


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


def test_play_then_quest_same_turn_using_moves():
    """Test playing a character and immediately questing with it using the move system."""
    print("\n=== Testing Play then Quest in Same Turn ===")
    
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create test character
    test_char = create_test_character("Test Character", cost=1, strength=2, willpower=2, lore=1)
    test_char.controller = player1
    
    # Give the character to player1's hand
    player1.hand = [test_char]
    
    # Set up game state
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = Phase.PLAY
    game_state.turn_number = 2  # Not first turn
    
    # Give players enough ink
    for i in range(3):
        ink_card = create_test_character(f"Ink{i}", cost=1)
        player1.inkwell.append(ink_card)
    
    # Give players some deck cards
    for i in range(10):
        deck_card = create_test_character(f"Deck{i}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    # Create game engine (execution_mode=PAUSE_ON_INPUT is default production mode)
    
    engine = GameEngine(game_state)
    
    print(f"Initial state - Character in hand: {test_char.name}")
    print(f"Turn number: {game_state.turn_number}")
    
    # Get initial legal actions
    initial_msg = engine.next_message()
    print(f"\nInitial message type: {initial_msg.type}")
    if initial_msg.type == MessageType.ACTION_REQUIRED:
        print(f"Legal actions count: {len(initial_msg.legal_actions)}")
        play_actions = [la for la in initial_msg.legal_actions if la.action == 'play_character']
        print(f"Can play character: {len(play_actions) > 0}")
    
    # Play the character
    play_move = PlayMove(test_char)
    play_result = engine.next_message(play_move)
    print(f"\nPlay result type: {play_result.type}")
    if play_result.type == MessageType.STEP_EXECUTED:
        print(f"Play successful: {play_result.step}")
    
    # Check character state
    print(f"\nAfter playing:")
    print(f"Character in play: {test_char in player1.characters_in_play}")
    print(f"Character is_dry: {test_char.is_dry}")
    print(f"Current turn number: {game_state.turn_number}")
    print(f"Character can_quest: {test_char.can_quest(game_state.turn_number)}")
    print(f"DEBUG: Character should have wet ink (is_dry=False) when just played")
    
    # Process any triggered abilities
    while True:
        msg = engine.next_message()
        if msg.type == MessageType.ACTION_REQUIRED:
            break
        elif msg.type == MessageType.STEP_EXECUTED:
            print(f"Processing triggered ability: {msg.step}")
    
    # Check legal actions after playing
    print(f"\nLegal actions after playing:")
    quest_actions = [la for la in msg.legal_actions if la.action == 'quest_character' and la.parameters.get('character') == test_char]
    print(f"Can quest with just-played character: {len(quest_actions) > 0}")
    
    # Try to quest with the freshly played character - this should fail
    initial_lore = player1.lore
    initial_exerted = test_char.exerted
    
    print(f"\nBefore quest attempt: lore={initial_lore}, exerted={initial_exerted}")
    
    # Send quest move and process ALL resulting effects
    engine.next_message(QuestMove(test_char))
    
    # Process all queued effects until ready for next action
    effect_count = 0
    while True:
        msg = engine.next_message()
        if msg.type == MessageType.ACTION_REQUIRED:
            break
        elif msg.type == MessageType.STEP_EXECUTED:
            effect_count += 1
            print(f"Processing effect {effect_count}: {msg.step}")
    
    print(f"After quest attempt: lore={player1.lore}, exerted={test_char.exerted}")
    
    # Character should NOT gain lore or be exerted (wet ink restriction should prevent the effect)
    assert player1.lore == initial_lore, \
        f"ISSUE CONFIRMED: Character gained lore with wet ink! Lore: {initial_lore} → {player1.lore}"
    assert test_char.exerted == initial_exerted, \
        f"ISSUE CONFIRMED: Character exertion changed with wet ink! Exerted: {initial_exerted} → {test_char.exerted}"
    
    print(f"✅ SUCCESS: Wet ink correctly prevented quest effects (no lore gained, no exertion change)")


def test_play_then_challenge_same_turn_using_moves():
    """Test playing a character and immediately challenging with it using the move system."""
    print("\n=== Testing Play then Challenge in Same Turn ===")
    
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Create test character and defender
    test_char = create_test_character("Test Character", cost=1, strength=2, willpower=2, lore=1)
    test_char.controller = player1
    
    defender = create_test_character("Defender", cost=1, strength=1, willpower=3, lore=1)
    defender.controller = player2
    defender.exerted = True  # Must be exerted to be challengeable
    defender.is_dry = True
    player2.characters_in_play = [defender]
    
    # Give the character to player1's hand
    player1.hand = [test_char]
    
    # Set up game state
    game_state = GameState([player1, player2])
    game_state.current_player_index = 0  # Player 1's turn
    game_state.current_phase = Phase.PLAY
    game_state.turn_number = 2  # Not first turn
    
    # Give players enough ink
    for i in range(3):
        ink_card = create_test_character(f"Ink{i}", cost=1)
        player1.inkwell.append(ink_card)
    
    # Give players some deck cards
    for i in range(10):
        deck_card = create_test_character(f"Deck{i}", cost=2)
        player1.deck.append(deck_card)
        player2.deck.append(deck_card)
    
    # Create game engine (execution_mode=PAUSE_ON_INPUT is default production mode)
    
    engine = GameEngine(game_state)
    
    print(f"Initial state - Character in hand: {test_char.name}")
    print(f"Defender in play: {defender.name} (exerted: {defender.exerted})")
    
    # Play the character
    play_move = PlayMove(test_char)
    play_result = engine.next_message(play_move)
    print(f"\nPlay successful: {play_result.step}")
    
    # Check character state
    print(f"\nAfter playing:")
    print(f"Character in play: {test_char in player1.characters_in_play}")
    print(f"Character is_dry: {test_char.is_dry}")
    print(f"Current turn number: {game_state.turn_number}")
    print(f"Character can_challenge: {test_char.can_challenge(game_state.turn_number)}")
    print(f"DEBUG: Character should have wet ink (is_dry=False) when just played")
    
    # Process any triggered abilities
    while True:
        msg = engine.next_message()
        if msg.type == MessageType.ACTION_REQUIRED:
            break
        elif msg.type == MessageType.STEP_EXECUTED:
            print(f"Processing triggered ability: {msg.step}")
    
    # Check legal actions after playing
    print(f"\nLegal actions after playing:")
    challenge_actions = [la for la in msg.legal_actions if la.action == 'challenge_character' and la.parameters.get('attacker') == test_char]
    print(f"Can challenge with just-played character: {len(challenge_actions) > 0}")
    
    # Try to challenge with the freshly played character - this should fail
    initial_attacker_damage = test_char.damage
    initial_defender_damage = defender.damage
    initial_attacker_exerted = test_char.exerted
    
    print(f"\nBefore challenge attempt:")
    print(f"  Attacker damage: {initial_attacker_damage}, exerted: {initial_attacker_exerted}")
    print(f"  Defender damage: {initial_defender_damage}")
    
    # Send challenge move and process ALL resulting effects
    engine.next_message(ChallengeMove(test_char, defender))
    
    # Process all queued effects until ready for next action
    effect_count = 0
    while True:
        msg = engine.next_message()
        if msg.type == MessageType.ACTION_REQUIRED:
            break
        elif msg.type == MessageType.STEP_EXECUTED:
            effect_count += 1
            print(f"Processing effect {effect_count}: {msg.step}")
    
    print(f"\nAfter challenge attempt:")
    print(f"  Attacker damage: {test_char.damage}, exerted: {test_char.exerted}")
    print(f"  Defender damage: {defender.damage}")
    
    # Character should NOT be able to challenge immediately after being played (wet ink restriction)
    # Exception: Rush characters CAN challenge immediately, but regular characters cannot
    if not test_char.has_rush_ability():
        # No damage should be dealt, no exertion should change
        assert test_char.damage == initial_attacker_damage, \
            f"ISSUE CONFIRMED: Attacker took damage with wet ink! Damage: {initial_attacker_damage} → {test_char.damage}"
        assert defender.damage == initial_defender_damage, \
            f"ISSUE CONFIRMED: Defender took damage from wet ink attacker! Damage: {initial_defender_damage} → {defender.damage}"
        print(f"✅ SUCCESS: Wet ink correctly prevented challenge effects (no damage dealt)")
    else:
        # Rush characters should deal damage
        expected_damage_to_defender = test_char.strength
        expected_damage_to_attacker = defender.strength
        assert defender.damage == initial_defender_damage + expected_damage_to_defender, \
            f"Rush character should deal damage but didn't! Expected: {initial_defender_damage + expected_damage_to_defender}, Got: {defender.damage}"
        assert test_char.damage == initial_attacker_damage + expected_damage_to_attacker, \
            f"Rush character should take damage but didn't! Expected: {initial_attacker_damage + expected_damage_to_attacker}, Got: {test_char.damage}"
        print(f"✅ SUCCESS: Rush character correctly dealt damage immediately")


# Tests are now properly structured for pytest with assertions instead of returns