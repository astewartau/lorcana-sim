#!/usr/bin/env python3
"""Test UNTOLD TREASURE when NO Illusion character is in play."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.lorcana_sim.models.game.game_state import GameState, GameAction
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity

# Create test setup
player1 = Player("Ashley", "Amethyst-Steel")
player1.hand = []
player1.deck = [None] * 5
player1.lore = 0

# Give ink
for _ in range(4):
    player1.inkwell.append(None)

player2 = Player("Tace", "Ruby-Emerald")
player2.hand = []
player2.deck = []

game_state = GameState([player1, player2])
engine = GameEngine(game_state)

# Create HeiHei (NOT an Illusion) - already in play
heihei = CharacterCard(
    id=1, name="HeiHei", version="Test", full_name="HeiHei - Test",
    cost=2, color=CardColor.RUBY, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=1, story="",
    strength=2, willpower=2, lore=1,
    subtypes=["Storyborn", "Ally"], controller=player1  # No "Illusion"
)

# Put HeiHei in play (NOT an Illusion)
player1.characters_in_play.append(heihei)

# Create Treasure Guardian with UNTOLD TREASURE
treasure_guardian = CharacterCard(
    id=2, name="Treasure Guardian", version="Test", full_name="Treasure Guardian - Test",
    cost=4, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=2, story="",
    strength=3, willpower=3, lore=2,
    subtypes=["Storyborn"], controller=player1
)

# Add UNTOLD TREASURE ability
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.untold_treasure import create_untold_treasure
ability = create_untold_treasure(treasure_guardian, {})
treasure_guardian.composable_abilities.append(ability)

# Put Treasure Guardian in hand
player1.hand.append(treasure_guardian)

print("=== Testing UNTOLD TREASURE WITHOUT Illusion ===")
print(f"Characters in play: {[(char.name, char.subtypes) for char in player1.characters_in_play]}")
print(f"Hand: {[card.name for card in player1.hand]}")
print(f"Hand size before: {len(player1.hand)}")

# Set game phase
game_state.current_phase = game_state.current_phase.PLAY

# Test the condition function directly first
print(f"\n🔍 Testing condition function directly...")
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.untold_treasure import _has_illusion_condition

context = {
    'game_state': game_state,
    'player': player1
}

condition_result = _has_illusion_condition(treasure_guardian, context)
print(f"   Condition result: {condition_result}")
print(f"   HeiHei subtypes: {heihei.subtypes}")
print(f"   'Illusion' in subtypes: {'Illusion' in heihei.subtypes}")

# Play Treasure Guardian
print(f"\n🎭 Playing {treasure_guardian.name}...")
result = engine.execute_action(GameAction.PLAY_CHARACTER, {'card': treasure_guardian})

print(f"Action result: {result.success}")
if result.success:
    print(f"Triggered abilities: {result.data.get('triggered_abilities', [])}")
    
    # Check if game is paused for choice
    if engine.is_paused_for_choice():
        choice = engine.get_current_choice()
        print(f"\n✅ Game paused for choice!")
        print(f"   Ability: {choice.ability_name}")
        print(f"   Prompt: {choice.prompt}")
    else:
        print(f"\n⚠️  No choice triggered (expected when no Illusion in play)")
        
    print(f"\nFinal state:")
    print(f"   Hand size after: {len(player1.hand)}")
    print(f"   Deck size after: {len(player1.deck)}")
else:
    print(f"Failed: {result.error_message}")