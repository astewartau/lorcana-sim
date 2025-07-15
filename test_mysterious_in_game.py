#!/usr/bin/env python3
"""Test MYSTERIOUS ADVANTAGE in game scenario."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.lorcana_sim.models.game.game_state import GameState, GameAction
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity

# Recreate the exact scenario
player1 = Player("Ashley", "Amethyst-Steel")
player1.hand = []
player1.deck = [None] * 5
player1.lore = 0

# Give some ink
for _ in range(4):
    player1.inkwell.append(None)

player2 = Player("Tace", "Ruby-Emerald")
player2.hand = []
player2.deck = []

game_state = GameState([player1, player2])
engine = GameEngine(game_state)

# Create Giant Cobra with MYSTERIOUS ADVANTAGE
cobra = CharacterCard(
    id=1, name="Giant Cobra", version="Scheming Henchman", full_name="Giant Cobra - Scheming Henchman",
    cost=3, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.UNCOMMON,
    set_code="TEST", number=1, story="",
    strength=4, willpower=3, lore=2,
    subtypes=["Villain"], controller=player1
)

# Add MYSTERIOUS ADVANTAGE ability
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.mysterious_advantage import create_mysterious_advantage
ability = create_mysterious_advantage(cobra, {})
cobra.composable_abilities.append(ability)

# Add some cards to hand
card1 = CharacterCard(
    id=2, name="Test Card 1", version="", full_name="Test Card 1",
    cost=1, color=CardColor.RUBY, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=2, story="",
    strength=1, willpower=1, lore=1,
    subtypes=[], controller=player1
)

card2 = CharacterCard(
    id=3, name="Test Card 2", version="", full_name="Test Card 2",
    cost=2, color=CardColor.STEEL, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=3, story="",
    strength=2, willpower=2, lore=1,
    subtypes=[], controller=player1
)

player1.hand.extend([cobra, card1, card2])

print("=== Testing MYSTERIOUS ADVANTAGE in game scenario ===")
print(f"Hand: {[card.name for card in player1.hand]}")
print(f"Available ink: {player1.available_ink}")

# Set up the game state properly  
game_state.current_phase = game_state.current_phase.PLAY

# Simulate playing Giant Cobra
print(f"\n🎭 Playing {cobra.name}...")

# Execute the play character action
result = engine.execute_action(GameAction.PLAY_CHARACTER, {'card': cobra})

print(f"Action result: {result.success}")
if result.success:
    print(f"Triggered abilities: {result.data.get('triggered_abilities', [])}")
    
    # Check if game is paused for choice
    if engine.is_paused_for_choice():
        choice = engine.get_current_choice()
        print(f"\n✅ Game paused for choice!")
        print(f"   Player: {choice.player.name}")
        print(f"   Ability: {choice.ability_name}")
        print(f"   Prompt: {choice.prompt}")
        print(f"   Options:")
        for opt in choice.options:
            print(f"     • {opt.id}: {opt.description}")
    else:
        print(f"\n⚠️  No choice triggered")
        print(f"   Game paused: {engine.is_paused_for_choice()}")
        
    print(f"\nFinal state:")
    print(f"   Hand: {[card.name for card in player1.hand]}")
    print(f"   Lore: {player1.lore}")
else:
    print(f"Failed: {result.error_message}")