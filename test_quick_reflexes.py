#!/usr/bin/env python3
"""Test QUICK REFLEXES ability."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity

# Create test setup
ashley = Player("Ashley", "Amethyst")
ashley.hand = []
ashley.deck = [None] * 5
ashley.lore = 0

tace = Player("Tace", "Ruby")
tace.hand = []
tace.deck = [None] * 5

game_state = GameState([ashley, tace])
engine = GameEngine(game_state)

# Create Helga with QUICK REFLEXES
helga = CharacterCard(
    id=1, name="Helga Sinclair", version="Quick Reflexes", full_name="Helga Sinclair - Quick Reflexes",
    cost=2, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=1, story="",
    strength=0, willpower=4, lore=1,
    subtypes=["Storyborn"], controller=ashley
)

# Add QUICK REFLEXES ability
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.quick_reflexes import create_quick_reflexes
ability = create_quick_reflexes(helga, {})
helga.composable_abilities.append(ability)

# Put Helga in play
ashley.characters_in_play.append(helga)

print("=== Testing QUICK REFLEXES Ability ===")
print(f"Initial state:")
print(f"  Current player: {game_state.current_player.name}")
print(f"  Helga has_evasive_ability: {helga.has_evasive_ability()}")
print(f"  Helga metadata: {helga.metadata}")

# Test during Ashley's turn (should have Evasive)
print(f"\n🎮 During Ashley's turn:")
print(f"  Current player: {game_state.current_player.name}")
print(f"  Helga has_evasive_ability: {helga.has_evasive_ability()}")
print(f"  Helga metadata: {helga.metadata}")

# Switch to Tace's turn and test
game_state.current_player_index = 1  # Switch to Tace
print(f"\n🎮 During Tace's turn:")
print(f"  Current player: {game_state.current_player.name}")
print(f"  Helga has_evasive_ability: {helga.has_evasive_ability()}")
print(f"  Helga metadata: {helga.metadata}")

# Test the ability's effect manually
print(f"\n🧪 Testing QuickReflexesEffect manually:")
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.quick_reflexes import QuickReflexesEffect
effect = QuickReflexesEffect()

# Test during Ashley's turn
game_state.current_player_index = 0  # Switch back to Ashley
context = {'game_state': game_state}
print(f"  Ashley's turn - applying effect:")
effect.apply(helga, context)
print(f"    Helga metadata after: {helga.metadata}")
print(f"    has_evasive_ability: {helga.has_evasive_ability()}")

# Test during Tace's turn
game_state.current_player_index = 1  # Switch to Tace
print(f"  Tace's turn - applying effect:")
effect.apply(helga, context)
print(f"    Helga metadata after: {helga.metadata}")
print(f"    has_evasive_ability: {helga.has_evasive_ability()}")

# Test with actual events
print(f"\n🎯 Testing with actual turn events:")
from src.lorcana_sim.engine.event_system import EventContext, GameEvent

# Make sure the ability is registered
engine.event_manager.rebuild_listeners()

# Debug: Check if the ability is registered
print(f"  Helga's composable abilities: {[ability.name for ability in helga.composable_abilities]}")

# Test the trigger condition directly
from src.lorcana_sim.models.abilities.composable.triggers import when_turn_starts
trigger_func = when_turn_starts()
test_context = EventContext(
    event_type=GameEvent.TURN_BEGINS,
    player=ashley,
    game_state=game_state
)
print(f"  Trigger function matches TURN_BEGINS: {trigger_func(test_context)}")

# Test if the ability's trigger matches
ability = helga.composable_abilities[0]
print(f"  Ability: {ability}")
print(f"  Ability __dict__: {ability.__dict__}")

# Check if the ability has the trigger
if hasattr(ability, 'trigger'):
    print(f"  Ability trigger matches: {ability.trigger(test_context)}")
elif hasattr(ability, 'triggers'):
    print(f"  Ability has {len(ability.triggers)} triggers")
    for i, trigger in enumerate(ability.triggers):
        print(f"    Trigger {i} matches: {trigger(test_context)}")
else:
    print(f"  Ability has no trigger/triggers attribute")
    
# Check the listeners
if hasattr(ability, 'listeners'):
    print(f"  Ability has {len(ability.listeners)} listeners")
    for i, listener in enumerate(ability.listeners):
        print(f"    Listener {i} trigger_condition matches: {listener.trigger_condition(test_context)}")

# Test Ashley's turn start
# Test triggering the listener manually
print(f"  Testing listener manually:")
listener = ability.listeners[0]
targets = listener.target_selector.select({'game_state': game_state, 'ability_owner': helga})
print(f"    Targets: {targets}")
if targets:
    context = {'game_state': game_state, 'ability_owner': helga}
    print(f"    Context: {context}")
    listener.effect.apply(targets[0], context)
    print(f"    Helga metadata after manual trigger: {helga.metadata}")
    print(f"    has_evasive_ability: {helga.has_evasive_ability()}")
    
    # Test with Ashley as current player
    print(f"    Testing with Ashley as current player:")
    game_state.current_player_index = 0  # Ashley is index 0
    context2 = {'game_state': game_state, 'ability_owner': helga, 'source': helga}
    listener.effect.apply(targets[0], context2)
    print(f"    Helga metadata after Ashley turn: {helga.metadata}")
    print(f"    has_evasive_ability: {helga.has_evasive_ability()}")
    
    # Test with Tace as current player  
    print(f"    Testing with Tace as current player:")
    game_state.current_player_index = 1  # Tace is index 1
    listener.effect.apply(targets[0], context2)
    print(f"    Helga metadata after Tace turn: {helga.metadata}")
    print(f"    has_evasive_ability: {helga.has_evasive_ability()}")

print(f"  Triggering TURN_BEGINS for Ashley...")
turn_start_context = EventContext(
    event_type=GameEvent.TURN_BEGINS,
    player=ashley,
    game_state=game_state
)
engine.event_manager.trigger_event(turn_start_context)
print(f"    Helga metadata after TURN_BEGINS: {helga.metadata}")
print(f"    has_evasive_ability: {helga.has_evasive_ability()}")

# Test Tace's turn start (should remove Evasive from Helga)
print(f"  Triggering TURN_BEGINS for Tace...")
turn_start_context = EventContext(
    event_type=GameEvent.TURN_BEGINS,
    player=tace,
    game_state=game_state
)
engine.event_manager.trigger_event(turn_start_context)
print(f"    Helga metadata after TURN_BEGINS: {helga.metadata}")
print(f"    has_evasive_ability: {helga.has_evasive_ability()}")

print(f"\n✅ QUICK REFLEXES should work if events trigger the ability correctly!")