#!/usr/bin/env python3
"""Test the exact THAT'S BETTER scenario from the game."""

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
for _ in range(3):
    player1.inkwell.append(None)

player2 = Player("Tace", "Ruby-Emerald")
player2.hand = []
player2.deck = []

game_state = GameState([player1, player2])
engine = GameEngine(game_state)

# Create Jafar with THAT'S BETTER
jafar = CharacterCard(
    id=1, name="Jafar", version="That's Better", full_name="Jafar - That's Better",
    cost=3, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.RARE,
    set_code="TEST", number=1, story="",
    strength=3, willpower=2, lore=2,
    subtypes=["Villain", "Sorcerer"], controller=player1
)

# Add THAT'S BETTER ability
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.thats_better import create_thats_better
ability = create_thats_better(jafar, {})
jafar.composable_abilities.append(ability)

# Create another character already in play
helga = CharacterCard(
    id=2, name="Helga Sinclair", version="Test", full_name="Helga Sinclair - Test",
    cost=2, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code="TEST", number=2, story="",
    strength=0, willpower=4, lore=1,
    subtypes=["Storyborn"], controller=player1
)
player1.characters_in_play.append(helga)

# Put Jafar in hand so we can play him
player1.hand.append(jafar)

print("=== Testing THAT'S BETTER in game scenario ===")
print(f"Player: {player1.name}")
print(f"Available ink: {player1.available_ink}")
print(f"Hand: {[card.name for card in player1.hand]}")
print(f"Characters in play: {[char.name for char in player1.characters_in_play]}")

# Check what actions are legal first
legal_actions = engine.validator.get_all_legal_actions()
print(f"Legal actions: {[(action, params.get('card', {}).get('name', str(params))) for action, params in legal_actions[:5]]}")

# Set up the game state properly
game_state.current_phase = game_state.current_phase.PLAY  # Make sure we're in play phase

# Simulate playing Jafar
print(f"\n🎭 Playing {jafar.name}...")

# Execute the play character action
result = engine.execute_action(GameAction.PLAY_CHARACTER, {'card': jafar})

print(f"Action result: {result.success}")
if result.success:
    print(f"Action type: {result.result_type}")
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
        
        # Make the choice
        if choice.options:
            chosen = choice.options[0]  # Choose first option
            print(f"   Choosing: {chosen.description}")
            success = engine.provide_player_choice(choice.choice_id, chosen.id)
            print(f"   Choice result: {success}")
    else:
        print(f"\n⚠️  No choice triggered")
        print(f"   Game paused: {engine.is_paused_for_choice()}")
        print(f"   Current choice: {engine.get_current_choice()}")
        print(f"   Choice manager: {engine.choice_manager}")
        print(f"   Pending choices: {len(engine.choice_manager.pending_choices) if engine.choice_manager else 'No manager'}")
        
    print(f"\nFinal state:")
    print(f"   Characters in play: {[char.name for char in player1.characters_in_play]}")
    print(f"   Hand: {[card.name for card in player1.hand]}")
    print(f"   Available ink: {player1.available_ink}")
    
    # Debug: Let's manually test the choice effect
    print(f"\n🔍 Manual choice test...")
    from src.lorcana_sim.engine.choice_system import choose_character_effect
    from src.lorcana_sim.models.abilities.composable.effects import GAIN_CHALLENGER_BUFF
    
    choice_effect = choose_character_effect(
        prompt="Choose a character to gain Challenger +2 this turn",
        character_filter=lambda char: True,
        effect_on_selected=GAIN_CHALLENGER_BUFF(2, "turn"),
        ability_name="THAT'S BETTER",
        allow_none=False,
        from_play=True,
        from_hand=False,
        controller_characters=True,
        opponent_characters=False
    )
    
    context = {
        'choice_manager': engine.choice_manager,
        'game_state': game_state,
        'ability_owner': jafar,
        'player': player1
    }
    
    print(f"   Testing choice effect directly...")
    print(f"   Context keys: {context.keys()}")
    print(f"   Choice manager: {context.get('choice_manager')}")
    print(f"   Game state: {context.get('game_state')}")
    print(f"   Ability owner: {context.get('ability_owner')}")
    
    choice_effect.apply(player1, context)
    
    if engine.is_paused_for_choice():
        choice = engine.get_current_choice()
        print(f"   ✅ Manual test created choice!")
        print(f"   Options: {[opt.description for opt in choice.options]}")
    else:
        print(f"   ❌ Manual test also failed to create choice")
        
    # Let's also check what the actual ability execution context looks like
    print(f"\n🔍 Checking actual ability execution context...")
    # Re-run the ability to see what context it gets
    from src.lorcana_sim.engine.event_system import GameEvent
    enter_context = engine.event_manager._composable_listeners.get(GameEvent.CHARACTER_ENTERS_PLAY, [])
    print(f"   Registered abilities for enters play: {len(enter_context)}")
    if enter_context:
        for ability in enter_context:
            if ability.name == "THAT'S BETTER":
                print(f"   Found THAT'S BETTER ability: {ability}")
                print(f"   Listeners: {len(ability.listeners)}")
                if ability.listeners:
                    listener = ability.listeners[0]
                    print(f"   Effect: {listener.effect}")
                    print(f"   Target selector: {listener.target_selector}")
else:
    print(f"Failed to play character: {result.error_message}")