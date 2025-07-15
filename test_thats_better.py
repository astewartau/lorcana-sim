#!/usr/bin/env python3
"""Test THAT'S BETTER choice system."""

import sys
sys.path.append('.')

from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.event_system import EventContext, GameEvent

# Create test setup
player1 = Player('Ashley', 'Amethyst')
player1.hand = []
player1.deck = [None] * 5
player2 = Player('Tace', 'Ruby')
player2.hand = []
player2.deck = []

game_state = GameState([player1, player2])
engine = GameEngine(game_state)

# Create Jafar with THAT'S BETTER
jafar = CharacterCard(
    id=1, name='Jafar', version="That's Better", full_name="Jafar - That's Better",
    cost=3, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.RARE,
    set_code='TEST', number=1, story='',
    strength=3, willpower=2, lore=2,
    subtypes=['Villain', 'Sorcerer'], controller=player1
)

# Add THAT'S BETTER ability
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.thats_better import create_thats_better
ability = create_thats_better(jafar, {})
jafar.composable_abilities.append(ability)

# Create another character in play to target
helga = CharacterCard(
    id=2, name='Helga Sinclair', version='Test', full_name='Helga Sinclair - Test',
    cost=2, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code='TEST', number=2, story='',
    strength=0, willpower=4, lore=1,
    subtypes=['Storyborn'], controller=player1
)

# Put characters in play
player1.characters_in_play.extend([jafar, helga])

# Register abilities
jafar.register_composable_abilities(engine.event_manager)

print('Testing THAT\'S BETTER choice system...')
print(f'Characters in play: {[char.name for char in player1.characters_in_play]}')
print(f'Jafar abilities: {[ability.name for ability in jafar.composable_abilities]}')

# Trigger enters play event for Jafar
enter_context = EventContext(
    event_type=GameEvent.CHARACTER_ENTERS_PLAY,
    source=jafar,
    player=player1,
    game_state=game_state
)

# Trigger the event with choices
results = engine.trigger_event_with_choices(enter_context)
print(f'Event results: {results}')

# Check if game is paused
if engine.is_paused_for_choice():
    choice = engine.get_current_choice()
    print(f'✅ Game paused for choice!')
    print(f'   Player: {choice.player.name}')
    print(f'   Ability: {choice.ability_name}')
    print(f'   Prompt: {choice.prompt}')
    print(f'   Options:')
    for opt in choice.options:
        print(f'     • {opt.id}: {opt.description}')
    
    # Choose a character
    valid = [opt for opt in choice.options if opt.id != "none"]
    if valid:
        chosen = valid[0]  # Choose first character
        print(f'   Choosing: {chosen.description}')
        success = engine.provide_player_choice(choice.choice_id, chosen.id)
        if success:
            print(f'✅ Choice resolved successfully!')
            print(f'   Chosen character should now have Challenger +2 buff')
        else:
            print(f'❌ Failed to provide choice')
else:
    print('⚠️  No choice triggered - checking why...')
    print(f'   Characters: {len(player1.characters_in_play)}')
    print(f'   Ability registered: {jafar.composable_abilities[0] if jafar.composable_abilities else "None"}')