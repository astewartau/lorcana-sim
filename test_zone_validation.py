#!/usr/bin/env python3

"""Debug script to verify zone validation works correctly."""

import sys
sys.path.append('/home/ashley/repos/lorcana/lorcana-sim/src')

from tests.named_abilities.triggered.test_grasping_trunk import TestGraspingTrunkIntegration
from lorcana_sim.engine.event_system import get_card_current_zone
from lorcana_sim.models.abilities.composable.conditional_effects import ActivationZone

def debug_zone_validation():
    """Debug zone validation for quest abilities."""
    print("=== Zone Validation Debug ===")
    
    # Create test instance
    test = TestGraspingTrunkIntegration()
    test.setUp()
    
    # Create character
    trunk_character = test.create_grasping_trunk_character(name="Debug Character", lore=2)
    
    print(f"Character: {trunk_character.name}")
    print(f"Character abilities: {len(trunk_character.composable_abilities)}")
    
    if trunk_character.composable_abilities:
        ability = trunk_character.composable_abilities[0]
        print(f"Ability name: {ability.name}")
        print(f"Ability activation zones: {ability.activation_zones}")
    
    # Put character directly into play (like the test does)
    test.player1.characters_in_play = [trunk_character]
    trunk_character.controller = test.player1
    
    # Check what zone the character is detected to be in
    current_zone = get_card_current_zone(trunk_character, test.game_state)
    print(f"Character detected zone: {current_zone}")
    print(f"Is in PLAY zone? {current_zone == ActivationZone.PLAY}")
    
    # Check if ability should be active
    if trunk_character.composable_abilities:
        ability = trunk_character.composable_abilities[0]
        zone_valid = current_zone in ability.activation_zones
        print(f"Zone validation passes? {zone_valid}")
    
    # Check event manager registration
    event_manager = test.game_engine.execution_engine.event_manager
    from lorcana_sim.engine.event_system import GameEvent
    quest_listeners = event_manager.listeners.get(GameEvent.CHARACTER_QUESTS, [])
    print(f"Total CHARACTER_QUESTS listeners: {len(quest_listeners)}")
    
    # Check if our ability is registered
    our_ability_registered = False
    for listener in quest_listeners:
        if hasattr(listener, 'character') and listener.character == trunk_character:
            print(f"✅ Our ability IS registered for CHARACTER_QUESTS")
            our_ability_registered = True
            break
    
    if not our_ability_registered:
        print(f"❌ Our ability NOT registered for CHARACTER_QUESTS")
    
    return test, trunk_character

if __name__ == "__main__":
    test, character = debug_zone_validation()