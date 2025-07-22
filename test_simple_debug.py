#!/usr/bin/env python3

"""Simple debug to check quest trigger flow."""

import sys
sys.path.append('/home/ashley/repos/lorcana/lorcana-sim/src')

# Run an actual test and see what happens
from tests.named_abilities.triggered.test_grasping_trunk import TestGraspingTrunkIntegration

def debug_grasping_trunk_flow():
    """Debug the grasping trunk quest flow."""
    print("=== Running Grasping Trunk Debug ===")
    
    # Create test instance
    test = TestGraspingTrunkIntegration()
    test.setUp()
    
    # Create character
    trunk_character = test.create_grasping_trunk_character(name="Debug Character", lore=2)
    
    # Check if abilities are properly set
    print(f"Character has {len(trunk_character.composable_abilities)} composable abilities")
    if trunk_character.composable_abilities:
        ability = trunk_character.composable_abilities[0]
        print(f"Ability name: {ability.name}")
        print(f"Ability listeners: {len(ability.listeners)}")
        if ability.listeners:
            listener = ability.listeners[0]
            print(f"Listener trigger condition: {listener.trigger_condition}")
            if hasattr(listener.trigger_condition, 'get_relevant_events'):
                print(f"Relevant events: {listener.trigger_condition.get_relevant_events()}")
    
    # Create opponent
    opponent = test.create_test_character(name="Opponent", lore=3)
    
    # Set up game
    test.player1.characters_in_play = [trunk_character]
    test.player2.characters_in_play = [opponent]
    
    trunk_character.exerted = False
    trunk_character.is_dry = True
    trunk_character.controller = test.player1
    opponent.controller = test.player2
    
    # Check event manager registration
    event_manager = test.game_engine.execution_engine.event_manager
    print(f"\nEvent manager listeners before quest:")
    from lorcana_sim.engine.event_system import GameEvent
    quest_listeners = event_manager.listeners.get(GameEvent.CHARACTER_QUESTS, [])
    print(f"CHARACTER_QUESTS listeners: {len(quest_listeners)}")
    
    # Try quest
    from lorcana_sim.engine.game_moves import QuestMove
    quest_move = QuestMove(trunk_character)
    
    print(f"\n--- Starting Quest ---")
    print(f"Initial lore: {test.player1.lore}")
    
    # Process quest
    message = test.game_engine.next_message(quest_move)
    print(f"Quest result: {message.type}")
    print(f"Lore after quest: {test.player1.lore}")
    
    # Check for trigger
    trigger_message = test.game_engine.next_message()
    print(f"Follow-up message: {trigger_message.type}")
    
    print(f"Final lore: {test.player1.lore}")

if __name__ == "__main__":
    debug_grasping_trunk_flow()