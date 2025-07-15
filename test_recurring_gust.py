#!/usr/bin/env python3
"""Test RECURRING GUST ability."""

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

player2 = Player("Ashley", "Amethyst")
player2.hand = []
player2.deck = [None] * 5

game_state = GameState([player1, player2])
engine = GameEngine(game_state)

# Create Archimedes (attacker)
archimedes = CharacterCard(
    id=1, name="Archimedes", version="Evasive", full_name="Archimedes - Evasive",
    cost=2, color=CardColor.RUBY, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=1, story="",
    strength=2, willpower=2, lore=2,
    subtypes=["Storyborn"], controller=player1
)

# Create Gale with RECURRING GUST (defender)
gale = CharacterCard(
    id=2, name="Gale", version="Recurring Gust", full_name="Gale - Recurring Gust",
    cost=1, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=2, story="",
    strength=1, willpower=2, lore=2,
    subtypes=["Storyborn"], controller=player2
)

# Add RECURRING GUST ability to Gale
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.recurring_gust import create_recurring_gust
ability = create_recurring_gust(gale, {})
gale.composable_abilities.append(ability)

# Put characters in play and make them not dry
player1.characters_in_play.append(archimedes)
player2.characters_in_play.append(gale)

# Make characters not dry (set turn_played to a previous turn)
archimedes.turn_played = 1
gale.turn_played = 1

# Make characters dry (ready to act) - True means ready to act
archimedes.is_dry = True  
gale.is_dry = True

# Set current turn to 2 so characters can act
game_state.turn_number = 2

# Set the current player to Tace (who controls Archimedes)
game_state.current_player_index = 0  # Tace is player 0

print("=== Testing RECURRING GUST Ability ===")
print(f"Before challenge:")
print(f"  Tace characters in play: {[char.name for char in player1.characters_in_play]}")
print(f"  Tace hand: {[card.name for card in player1.hand]}")
print(f"  Ashley characters in play: {[char.name for char in player2.characters_in_play]}")
print(f"  Ashley hand: {[card.name for card in player2.hand]}")

# Set game phase
game_state.current_phase = game_state.current_phase.PLAY

# Execute challenge: Archimedes challenges Gale
print(f"\n⚔️  Archimedes challenges Gale...")
result = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
    'attacker': archimedes,
    'defender': gale
})

print(f"Challenge result: {result.success}")
if result.success:
    print(f"Triggered abilities: {result.data.get('triggered_abilities', [])}")
    
    # Check if game is paused for choice
    if engine.is_paused_for_choice():
        print("Game is paused for choice - resolving...")
        while engine.is_paused_for_choice():
            choice = engine.get_current_choice()
            print(f"Choice: {choice.prompt}")
            # Auto-resolve choices
            if choice.options:
                engine.provide_player_choice(choice.choice_id, choice.options[0].id)
    
    print(f"\nAfter challenge:")
    print(f"  Tace characters in play: {[char.name for char in player1.characters_in_play]}")
    print(f"  Tace hand: {[card.name for card in player1.hand]}")
    print(f"  Ashley characters in play: {[char.name for char in player2.characters_in_play]}")
    print(f"  Ashley hand: {[card.name for card in player2.hand]}")
    print(f"  Ashley discard: {[card.name for card in player2.discard_pile]}")
    
    print(f"\n🎯 Expected: Gale should return to Ashley's hand")
    print(f"🎯 Actual: Gale in hand = {'Gale' in [card.name for card in player2.hand]}")
else:
    print(f"Failed: {result.error_message}")