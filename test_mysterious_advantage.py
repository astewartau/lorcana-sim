#!/usr/bin/env python3
"""Test MYSTERIOUS ADVANTAGE choice directly."""

import sys
sys.path.append('.')

from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.event_system import EventContext, GameEvent

# Create test setup
player1 = Player('Test', 'Ruby')
player1.hand = []
player1.deck = [None] * 5
player2 = Player('Opponent', 'Steel')
player2.hand = []
player2.deck = []

game_state = GameState([player1, player2])
engine = GameEngine(game_state)

# Create character with MYSTERIOUS ADVANTAGE
cobra = CharacterCard(
    id=1, name='Giant Cobra', version='Test', full_name='Giant Cobra - Test',
    cost=3, color=CardColor.AMETHYST, inkwell=True, rarity=Rarity.COMMON,
    set_code='TEST', number=1, story='',
    strength=4, willpower=3, lore=2,
    subtypes=['Villain'], controller=player1
)

# Add ability
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.mysterious_advantage import create_mysterious_advantage
ability = create_mysterious_advantage(cobra, {})
cobra.composable_abilities.append(ability)

# Add cards to hand
card1 = CharacterCard(
    id=2, name='Card 1', version='', full_name='Card 1',
    cost=1, color=CardColor.RUBY, inkwell=True, rarity=Rarity.COMMON,
    set_code='TEST', number=2, story='',
    strength=1, willpower=1, lore=1,
    subtypes=[], controller=player1
)
player1.hand.append(card1)

# Put cobra in play and register abilities
player1.characters_in_play.append(cobra)
cobra.register_composable_abilities(engine.event_manager)

print('Testing MYSTERIOUS ADVANTAGE trigger...')
print(f'Hand before: {len(player1.hand)} cards')
print(f'Lore before: {player1.lore}')

# Trigger enters play event
enter_context = EventContext(
    event_type=GameEvent.CHARACTER_ENTERS_PLAY,
    source=cobra,
    player=player1,
    game_state=game_state
)

# Trigger the event with choices
results = engine.trigger_event_with_choices(enter_context)
print(f'Event results: {results}')

# Check if game is paused
if engine.is_paused_for_choice():
    choice = engine.get_current_choice()
    print(f'Game paused for choice!')
    print(f'Ability: {choice.ability_name}')
    print(f'Prompt: {choice.prompt}')
    print(f'Options: {[opt.description for opt in choice.options]}')
    
    # Make choice
    valid = [opt for opt in choice.options if opt.id != "none"]
    if valid:
        print(f'Choosing: {valid[0].description}')
        engine.provide_player_choice(choice.choice_id, valid[0].id)
        print(f'Hand after: {len(player1.hand)} cards')
        print(f'Lore after: {player1.lore}')
else:
    print('No choice triggered - checking why...')
    print(f'Hand size: {len(player1.hand)}')