#!/usr/bin/env python3

"""Debug script to check ability registration for quest-triggered abilities."""

import sys
sys.path.append('/home/ashley/repos/lorcana/lorcana-sim/src')

from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.engine.event_system import GameEvent

def check_quest_ability_registration():
    """Check what quest-triggered abilities are registered in the system."""
    print("=== Checking Quest Ability Registration ===")
    
    # Create basic game state
    game_state = GameState(decks=[[], []])
    engine = GameEngine(game_state)
    
    # Get the event manager
    event_manager = engine.execution_engine.event_manager
    
    print(f"Event manager: {event_manager}")
    print(f"Event listeners: {event_manager.listeners}")
    
    # Check what abilities are registered for CHARACTER_QUESTS
    quest_listeners = event_manager.listeners.get(GameEvent.CHARACTER_QUESTS, [])
    print(f"Number of CHARACTER_QUESTS listeners: {len(quest_listeners)}")
    
    for i, listener in enumerate(quest_listeners):
        print(f"  Listener {i+1}: {listener}")
        if hasattr(listener, 'ability_name'):
            print(f"    Ability name: {listener.ability_name}")
        if hasattr(listener, 'source_card'):
            print(f"    Source card: {listener.source_card}")
    
    # Check other event types too
    challenge_listeners = event_manager.listeners.get(GameEvent.CHARACTER_CHALLENGES, [])
    print(f"Number of CHARACTER_CHALLENGES listeners: {len(challenge_listeners)}")
    
    banished_listeners = event_manager.listeners.get(GameEvent.CHARACTER_BANISHED, [])
    print(f"Number of CHARACTER_BANISHED listeners: {len(banished_listeners)}")
    
    enters_play_listeners = event_manager.listeners.get(GameEvent.CHARACTER_ENTERS_PLAY, [])
    print(f"Number of CHARACTER_ENTERS_PLAY listeners: {len(enters_play_listeners)}")
    
    return event_manager

if __name__ == "__main__":
    event_manager = check_quest_ability_registration()