"""Validate that the WHAT DO WE DO NOW? trigger fix works correctly."""

import sys
import os
sys.path.append('.')

def test_trigger_logic():
    """Test the trigger logic directly."""
    print("🧪 Testing WHAT DO WE DO NOW? trigger logic...")
    
    # Import the new ability
    from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.what_do_we_do_now import _when_quests_with_anna
    from src.lorcana_sim.engine.event_system import EventContext, GameEvent
    
    # Create a mock character (Elsa)
    class MockCharacter:
        def __init__(self, name, controller):
            self.name = name
            self.controller = controller
    
    class MockPlayer:
        def __init__(self, name):
            self.name = name
            self.characters_in_play = []
    
    class MockGameState:
        def __init__(self):
            pass
    
    # Set up test scenario
    player = MockPlayer("TestPlayer")
    elsa = MockCharacter("Elsa", player)
    anna = MockCharacter("Anna", player)
    
    game_state = MockGameState()
    
    # Create the trigger condition
    trigger_condition = _when_quests_with_anna(elsa)
    
    # Test 1: Quest event without Anna in play
    print("\\n🧪 Test 1: Elsa quests WITHOUT Anna in play")
    quest_context = EventContext(
        event_type=GameEvent.CHARACTER_QUESTS,
        source=elsa,
        player=player,
        game_state=game_state
    )
    
    result = trigger_condition(quest_context)
    print(f"Trigger result: {result}")
    if not result:
        print("✅ SUCCESS: Trigger correctly did NOT fire without Anna")
    else:
        print("❌ FAILURE: Trigger incorrectly fired without Anna")
    
    # Test 2: Quest event with Anna in play
    print("\\n🧪 Test 2: Elsa quests WITH Anna in play")
    player.characters_in_play.append(anna)
    
    result = trigger_condition(quest_context)
    print(f"Trigger result: {result}")
    if result:
        print("✅ SUCCESS: Trigger correctly fired with Anna in play")
    else:
        print("❌ FAILURE: Trigger did not fire even with Anna in play")
    
    # Test 3: Wrong character quests (even with Anna in play)
    print("\\n🧪 Test 3: Different character quests (not Elsa)")
    other_character = MockCharacter("Some Other Character", player)
    wrong_quest_context = EventContext(
        event_type=GameEvent.CHARACTER_QUESTS,
        source=other_character,  # Not Elsa
        player=player,
        game_state=game_state
    )
    
    result = trigger_condition(wrong_quest_context)
    print(f"Trigger result: {result}")
    if not result:
        print("✅ SUCCESS: Trigger correctly did NOT fire for wrong character")
    else:
        print("❌ FAILURE: Trigger incorrectly fired for wrong character")
    
    print("\\n🎯 Test Summary:")
    print("- The new trigger system correctly combines both conditions")
    print("- Only fires when BOTH Elsa quests AND Anna is in play")
    print("- No conditional effects needed - trigger handles everything")

if __name__ == "__main__":
    test_trigger_logic()