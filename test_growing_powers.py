#!/usr/bin/env python3
"""Test GROWING POWERS choice system."""

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

# Create Anna with GROWING POWERS
anna = CharacterCard(
    id=1, name="Anna", version="Heir to Arendelle", full_name="Anna - Heir to Arendelle",
    cost=3, color=CardColor.RUBY, inkwell=True, rarity=Rarity.UNCOMMON,
    set_code="TEST", number=1, story="",
    strength=1, willpower=3, lore=1,
    subtypes=["Storyborn", "Hero", "Princess"], controller=player1
)

# Add GROWING POWERS ability
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.growing_powers import create_growing_powers
ability = create_growing_powers(anna, {})
anna.composable_abilities.append(ability)

# Create opponent characters (Ashley's characters that should be forced to exert)
pain = CharacterCard(
    id=2, name="Pain", version="Test", full_name="Pain - Test",
    cost=1, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=2, story="",
    strength=1, willpower=3, lore=1,
    subtypes=["Storyborn"], controller=player2
)

giant_cobra = CharacterCard(
    id=3, name="Giant Cobra", version="Test", full_name="Giant Cobra - Test",
    cost=3, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=3, story="",
    strength=4, willpower=4, lore=1,
    subtypes=["Storyborn"], controller=player2
)

# Put opponent characters in play (both ready)
player2.characters_in_play.extend([pain, giant_cobra])

# Put Anna in hand so we can play her
player1.hand.append(anna)

print("=== Testing GROWING POWERS Choice System ===")
print(f"Tace hand: {[card.name for card in player1.hand]}")
print(f"Ashley characters: {[(char.name, 'Ready' if not char.exerted else 'Exerted') for char in player2.characters_in_play]}")
print(f"Available ink: {player1.available_ink}")

# Set game phase
game_state.current_phase = game_state.current_phase.PLAY

# Play Anna
print(f"\n🎭 Tace plays {anna.name}...")
result = engine.execute_action(GameAction.PLAY_CHARACTER, {'card': anna})

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
        
        # Choose first character (Pain)
        valid_options = [opt for opt in choice.options if opt.id != "none"]
        if valid_options:
            chosen = valid_options[0]
            print(f"   Choosing: {chosen.description}")
            success = engine.provide_player_choice(choice.choice_id, chosen.id)
            print(f"   Choice result: {success}")
    else:
        print(f"\n⚠️  No choice triggered")
        
    print(f"\nFinal state:")
    print(f"   Tace characters: {[(char.name, 'Ready' if not char.exerted else 'Exerted') for char in player1.characters_in_play]}")
    print(f"   Ashley characters: {[(char.name, 'Ready' if not char.exerted else 'Exerted') for char in player2.characters_in_play]}")
else:
    print(f"Failed: {result.error_message}")