"""Test CARD_DRAWN events using proper game flow."""

from tests.helpers import GameEngineTestBase
from lorcana_sim.models.abilities.composable.named_abilities.triggered.heavily_armed import create_heavily_armed
from lorcana_sim.engine.game_moves import PlayMove
from lorcana_sim.engine.message_engine import MessageType


def test_heavily_armed_proper_flow():
    """Test HEAVILY ARMED using the proper game flow."""
    
    # Create a basic test setup
    test_base = GameEngineTestBase()
    test_base.setup_method()
    
    # Create character with HEAVILY ARMED
    armed_character = test_base.create_test_character(
        name="Armed Character",
        cost=3,
        strength=2,
        willpower=3
    )
    
    # Add the HEAVILY ARMED ability
    ability_data = {"name": "HEAVILY ARMED", "type": "triggered"}
    heavily_armed_ability = create_heavily_armed(armed_character, ability_data)
    armed_character.composable_abilities = [heavily_armed_ability]
    
    # Setup game state - put character in hand, not in play
    test_base.player1.hand = [armed_character]
    test_base.setup_player_ink(test_base.player1, ink_count=5)
    
    # Add cards to deck for drawing
    dummy_card1 = test_base.create_test_character(name="Dummy Card 1")
    dummy_card2 = test_base.create_test_character(name="Dummy Card 2")
    test_base.player1.deck = [dummy_card1, dummy_card2]
    
    print("=== Initial Setup ===")
    print(f"Player1 hand: {len(test_base.player1.hand)} cards")
    print(f"Player1 deck: {len(test_base.player1.deck)} cards")
    print(f"Characters in play: {len(test_base.player1.characters_in_play)}")
    
    # Step 1: Play the character using proper game flow
    print("\n=== Step 1: Play Character ===")
    play_move = PlayMove(armed_character)
    play_message = test_base.game_engine.next_message(play_move)
    
    print(f"Play message: {play_message.type}")
    print(f"Characters in play: {len(test_base.player1.characters_in_play)}")
    
    # Check if ability was registered
    event_manager = test_base.game_engine.execution_engine.event_manager
    from lorcana_sim.engine.event_system import GameEvent
    card_drawn_listeners = event_manager._composable_listeners.get(GameEvent.CARD_DRAWN, [])
    print(f"CARD_DRAWN listeners after play: {len(card_drawn_listeners)}")
    
    # Step 2: Trigger a card draw via the DrawCards effect
    print("\n=== Step 2: Trigger Card Draw ===")
    from lorcana_sim.models.abilities.composable.effects import DrawCards
    
    # Queue a DrawCards effect
    action_queue = test_base.game_engine.execution_engine.action_queue
    draw_effect = DrawCards(1)
    action_queue.enqueue(
        effect=draw_effect,
        target=test_base.player1,
        context={
            'source': None,
            'game_state': test_base.game_state,
            'player': test_base.player1
        },
        source_description="Manual draw for testing"
    )
    
    print(f"Actions in queue before: {len(action_queue._queue)}")
    
    # Process the draw
    draw_message = test_base.game_engine.next_message()
    print(f"Draw message: {draw_message.type}")
    print(f"Player1 hand after draw: {len(test_base.player1.hand)} cards")
    
    # Step 3: Check for ability trigger
    print("\n=== Step 3: Check Ability Trigger ===")
    print(f"Actions in queue after draw: {len(action_queue._queue)}")
    
    if len(action_queue._queue) > 0:
        trigger_message = test_base.game_engine.next_message()
        print(f"Trigger message: {trigger_message.type}")
        print(f"Trigger details: {trigger_message}")
        
        # Check for follow-up effect
        if len(action_queue._queue) > 0:
            effect_message = test_base.game_engine.next_message()
            print(f"Effect message: {effect_message.type}")
            print(f"Effect details: {effect_message}")
    else:
        print("❌ No ability trigger - CARD_DRAWN event not processed correctly")


if __name__ == "__main__":
    test_heavily_armed_proper_flow()