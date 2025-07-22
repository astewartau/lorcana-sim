"""Debug script to understand CARD_DRAWN event flow."""

from tests.helpers import GameEngineTestBase
from lorcana_sim.models.abilities.composable.effects import DrawCards
from lorcana_sim.models.abilities.composable.named_abilities.triggered.heavily_armed import create_heavily_armed
from lorcana_sim.engine.game_moves import PlayMove


def test_card_drawn_flow():
    """Test how DrawCards effect emits CARD_DRAWN events."""
    
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
    
    # Setup game state
    test_base.player1.characters_in_play = [armed_character]
    armed_character.controller = test_base.player1
    
    # IMPORTANT: Register the ability with the event manager
    event_manager = test_base.game_engine.execution_engine.event_manager
    for ability in armed_character.composable_abilities:
        ability.register_with_event_manager(event_manager)
    
    # Add cards to deck
    dummy_card = test_base.create_test_character(name="Dummy Card")
    test_base.player1.deck = [dummy_card]
    
    print("=== Initial Setup ===")
    print(f"Player1 hand: {len(test_base.player1.hand)} cards")
    print(f"Player1 deck: {len(test_base.player1.deck)} cards")
    print(f"Armed character abilities: {len(armed_character.composable_abilities)}")
    
    # Test 1: Use DrawCards effect directly
    print("\n=== Test 1: Direct DrawCards Effect ===")
    draw_effect = DrawCards(1)
    context = {
        'source': armed_character,
        'game_state': test_base.game_state,
        'player': test_base.player1
    }
    
    # Apply the effect
    result = draw_effect.apply(test_base.player1, context)
    events = draw_effect.get_events(test_base.player1, context, result)
    
    print(f"Effect result: {result}")
    print(f"Events generated: {len(events)}")
    for event in events:
        print(f"  - Event: {event['type']} by {event.get('player', 'Unknown')}")
    
    print(f"Player1 hand after: {len(test_base.player1.hand)} cards")
    print(f"Player1 deck after: {len(test_base.player1.deck)} cards")
    
    # Test 2: Check if the ability is properly registered
    print("\n=== Test 2: Ability Registration ===")
    event_manager = test_base.game_engine.execution_engine.event_manager
    print(f"Event manager has {len(event_manager._composable_listeners)} event types registered")
    
    from lorcana_sim.engine.event_system import GameEvent
    card_drawn_listeners = event_manager._composable_listeners.get(GameEvent.CARD_DRAWN, [])
    print(f"CARD_DRAWN listeners: {len(card_drawn_listeners)}")
    
    for listener in card_drawn_listeners:
        print(f"  - Listener: {listener}")
    
    # Test 3: Manual event triggering
    print("\n=== Test 3: Manual Event Triggering ===")
    from lorcana_sim.engine.event_system import EventContext
    
    if events:
        # Trigger the first CARD_DRAWN event
        event_data = events[0]
        event_context = EventContext(
            event_type=event_data['type'],
            source=dummy_card,  # The card that was drawn
            target=None,
            player=test_base.player1,
            game_state=test_base.game_state,
            additional_data=event_data.get('additional_data', {})
        )
        
        print(f"Triggering event: {event_context.event_type}")
        print(f"Event player: {event_context.player}")
        print(f"Event source: {event_context.source}")
        
        # Manually trigger the event
        event_manager.trigger_event(event_context)
        
        # Check if there are any actions in the queue
        action_queue = test_base.game_engine.execution_engine.action_queue
        print(f"Actions in queue: {len(action_queue._queue)}")
        
        if len(action_queue._queue) > 0:
            print("Getting next message...")
            message = test_base.game_engine.next_message()
            print(f"Message type: {message.type}")
            print(f"Message: {message}")


if __name__ == "__main__":
    test_card_drawn_flow()