#!/usr/bin/env python3

"""Debug script to test full quest flow and see where event triggers break."""

import sys
sys.path.append('/home/ashley/repos/lorcana/lorcana-sim/src')

from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.abilities.composable.composable_ability import ComposableAbility
from lorcana_sim.models.abilities.composable.triggers import when_quests
from lorcana_sim.models.abilities.composable.effects import GainLoreEffect
from lorcana_sim.models.abilities.composable.target_selectors import CONTROLLER
from lorcana_sim.engine.game_moves import QuestMove
from lorcana_sim.engine.game_messages import MessageType

def create_simple_quest_test():
    """Create a simple test for quest triggering."""
    print("=== Testing Full Quest Flow ===")
    
    # Create a mock character with quest ability
    character = CharacterCard(
        name="Test Quester",
        cost=3,
        strength=2,
        willpower=3,
        lore=1
    )
    
    # Add a simple ability that triggers when this character quests
    quest_ability = ComposableAbility("TEST_QUEST_TRIGGER", character)
    quest_ability.when(when_quests(character))
    quest_ability.target(CONTROLLER)
    quest_ability.effect(GainLoreEffect(1))
    
    character.abilities = [quest_ability]
    
    print(f"Character created: {character.name}")
    print(f"Ability: {quest_ability}")
    print(f"Trigger events: {quest_ability.triggers[0].get_relevant_events()}")
    
    # Create game
    game_state = GameState(
        decks=[
            [character] * 10,  # Deck 1
            [] * 10            # Deck 2
        ]
    )
    
    # Put character in play for player 1
    game_state.players[0].characters_in_play.append(character)
    character.controller = game_state.players[0]
    character.exerted = False
    character.is_dry = True
    
    engine = GameEngine(game_state)
    
    print(f"Game setup complete. Player 1 lore: {game_state.players[0].lore}")
    
    # Try to quest
    print("\n--- Attempting Quest ---")
    quest_move = QuestMove(character)
    message = engine.next_message(quest_move)
    
    print(f"Quest message type: {message.type}")
    print(f"Quest message: {message}")
    print(f"Player 1 lore after quest: {game_state.players[0].lore}")
    
    # Check for triggered ability message
    print("\n--- Checking for triggered ability ---")
    trigger_message = engine.next_message()
    print(f"Follow-up message type: {trigger_message.type}")
    print(f"Follow-up message: {trigger_message}")
    print(f"Player 1 lore after trigger: {game_state.players[0].lore}")
    
    return engine, character

if __name__ == "__main__":
    engine, character = create_simple_quest_test()