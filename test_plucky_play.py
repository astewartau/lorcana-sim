#!/usr/bin/env python3
"""Test PLUCKY PLAY choice system."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.lorcana_sim.models.game.game_state import GameState, GameAction
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity

# Create test setup
player1 = Player("Tace", "Ruby")
player1.hand = []
player1.deck = [None] * 5
player1.lore = 0

# Give ink
for _ in range(3):
    player1.inkwell.append(None)

player2 = Player("Ashley", "Amethyst")
player2.hand = []
player2.deck = []

game_state = GameState([player1, player2])
engine = GameEngine(game_state)

# Create Donald Duck with PLUCKY PLAY
donald = CharacterCard(
    id=1, name="Donald Duck", version="Plucky Play", full_name="Donald Duck - Plucky Play",
    cost=3, color=CardColor.RUBY, inkwell=True, rarity=Rarity.UNCOMMON,
    set_code="TEST", number=1, story="",
    strength=2, willpower=4, lore=1,
    subtypes=["Storyborn", "Hero"], controller=player1
)

# Add PLUCKY PLAY ability
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.plucky_play import create_plucky_play
ability = create_plucky_play(donald, {})
donald.composable_abilities.append(ability)

# Create opponent characters (Ashley's characters that should take damage)
helga = CharacterCard(
    id=2, name="Helga Sinclair", version="Test", full_name="Helga Sinclair - Test",
    cost=2, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=2, story="",
    strength=0, willpower=4, lore=1,
    subtypes=["Storyborn"], controller=player2
)

jafar = CharacterCard(
    id=3, name="Jafar", version="Test", full_name="Jafar - Test",
    cost=3, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=3, story="",
    strength=3, willpower=2, lore=2,
    subtypes=["Storyborn"], controller=player2
)

# Put opponent characters in play (both undamaged)
player2.characters_in_play.extend([helga, jafar])

# Put Donald in hand so we can play him
player1.hand.append(donald)

print("=== Testing PLUCKY PLAY Choice System ===")
print(f"Tace hand: {[card.name for card in player1.hand]}")
print(f"Ashley characters: {[(char.name, f'{char.damage} damage') for char in player2.characters_in_play]}")
print(f"Available ink: {player1.available_ink}")

# Set game phase
game_state.current_phase = game_state.current_phase.PLAY

# Play Donald Duck
print(f"\n🎭 Tace plays {donald.name}...")
result = engine.execute_action(GameAction.PLAY_CHARACTER, {'card': donald})

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
        
        # Choose first character (Helga)
        valid_options = [opt for opt in choice.options if opt.id != "none"]
        if valid_options:
            chosen = valid_options[0]
            print(f"   Choosing: {chosen.description}")
            success = engine.provide_player_choice(choice.choice_id, chosen.id)
            print(f"   Choice result: {success}")
    else:
        print(f"\n⚠️  No choice triggered")
        
    print(f"\nFinal state:")
    print(f"   Tace characters: {[(char.name, f'{char.damage} damage') for char in player1.characters_in_play]}")
    print(f"   Ashley characters: {[(char.name, f'{char.damage} damage') for char in player2.characters_in_play]}")
else:
    print(f"Failed: {result.error_message}")