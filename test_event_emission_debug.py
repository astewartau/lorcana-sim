#!/usr/bin/env python3

"""Debug script to test event emission from QuestEffect, ChallengeEffect, etc."""

import sys
sys.path.append('/home/ashley/repos/lorcana/lorcana-sim/src')

from lorcana_sim.models.abilities.composable.effects import QuestEffect, ChallengeEffect, BanishCharacter
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.engine.event_system import GameEvent

def test_quest_effect_events():
    """Test that QuestEffect emits CHARACTER_QUESTS event."""
    print("=== Testing QuestEffect Event Emission ===")
    
    # Create a mock character
    class MockCharacter:
        def __init__(self):
            self.name = "Test Character"
            self.current_lore = 2
            self.lore = 2  # Fallback
            self.exerted = False
            self.controller = None
    
    class MockPlayer:
        def __init__(self):
            self.lore = 0
    
    character = MockCharacter()
    player = MockPlayer()
    character.controller = player
    
    # Create QuestEffect
    effect = QuestEffect(character)
    
    # Apply the effect
    context = {'player': player, 'game_state': None}
    result = effect.apply(character, context)
    
    # Get events
    events = effect.get_events(character, context, result)
    
    print(f"Number of events emitted: {len(events)}")
    for i, event in enumerate(events):
        print(f"Event {i+1}: {event}")
        if event.get('type') == GameEvent.CHARACTER_QUESTS:
            print("✅ CHARACTER_QUESTS event found!")
        else:
            print(f"❌ Wrong event type: {event.get('type')}")
    
    return events

def test_challenge_effect_events():
    """Test that ChallengeEffect emits CHARACTER_CHALLENGES event."""
    print("\n=== Testing ChallengeEffect Event Emission ===")
    
    # Create mock characters
    class MockCharacter:
        def __init__(self, name):
            self.name = name
            self.current_strength = 2
            self.strength = 2
            self.damage = 0
            self.controller = None
    
    class MockPlayer:
        pass
    
    attacker = MockCharacter("Attacker")
    defender = MockCharacter("Defender")
    player = MockPlayer()
    attacker.controller = player
    defender.controller = player
    
    # Create ChallengeEffect
    effect = ChallengeEffect(attacker, defender)
    
    # Apply the effect
    context = {'player': player, 'game_state': None}
    result = effect.apply(defender, context)
    
    # Get events
    events = effect.get_events(defender, context, result)
    
    print(f"Number of events emitted: {len(events)}")
    for i, event in enumerate(events):
        print(f"Event {i+1}: {event}")
        if event.get('type') == GameEvent.CHARACTER_CHALLENGES:
            print("✅ CHARACTER_CHALLENGES event found!")
        else:
            print(f"❌ Wrong event type: {event.get('type')}")
    
    return events

def test_banish_effect_events():
    """Test that BanishCharacter emits CHARACTER_BANISHED event."""
    print("\n=== Testing BanishCharacter Event Emission ===")
    
    # Create mock character
    class MockCharacter:
        def __init__(self):
            self.name = "Test Character"
            self.controller = None
            
        def banish(self):
            print("Character banished!")
    
    class MockPlayer:
        pass
    
    character = MockCharacter()
    player = MockPlayer()
    character.controller = player
    
    # Create BanishCharacter effect
    effect = BanishCharacter()
    
    # Apply the effect
    context = {'ability_name': 'Test Ability'}
    result = effect.apply(character, context)
    
    # Get events
    events = effect.get_events(character, context, result)
    
    print(f"Number of events emitted: {len(events)}")
    for i, event in enumerate(events):
        print(f"Event {i+1}: {event}")
        if event.get('type') == GameEvent.CHARACTER_BANISHED:
            print("✅ CHARACTER_BANISHED event found!")
        else:
            print(f"❌ Wrong event type: {event.get('type')}")
    
    return events

if __name__ == "__main__":
    quest_events = test_quest_effect_events()
    challenge_events = test_challenge_effect_events()
    banish_events = test_banish_effect_events()
    
    print(f"\n=== Summary ===")
    print(f"QuestEffect events: {len(quest_events)}")
    print(f"ChallengeEffect events: {len(challenge_events)}")
    print(f"BanishCharacter events: {len(banish_events)}")