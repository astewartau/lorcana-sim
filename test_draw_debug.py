#!/usr/bin/env python3
"""Debug test for draw phase functionality."""

from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.base_card import Card, CardColor, Rarity

# Create a simple test
players = [Player("Ashley"), Player("Tace")]

# Give each player a minimal deck
for player in players:
    for i in range(10):
        # Create a basic card
        card = Card()
        card.name = f"Test Card {i}"
        card.cost = 1
        card.color = CardColor.AMBER
        card.rarity = Rarity.COMMON
        card.inkwell = True
        card.set_code = "test"
        card.number = i
        player.deck.append(card)
    
    # Draw starting hands
    for _ in range(7):
        player.draw_card()

# Create game engine
engine = GameEngine(players)

print("=== INITIAL STATE ===")
print(f"Turn {engine.game_state.turn_number}, Player {engine.game_state.current_player_index} ({engine.game_state.current_player.name})")
print(f"Phase: {engine.game_state.current_phase.value}")
print(f"Ashley hand: {len(players[0].hand)}, deck: {len(players[0].deck)}")
print(f"Tace hand: {len(players[1].hand)}, deck: {len(players[1].deck)}")
print(f"card_drawn_this_turn: {engine.game_state.card_drawn_this_turn}")

print("\n=== STEPPING THROUGH DRAW PHASES ===")

# Step through messages to see what happens
for i in range(20):
    message = engine.next_message()
    print(f"Step {i+1}: {message}")
    print(f"  Turn {engine.game_state.turn_number}, Player {engine.game_state.current_player_index} ({engine.game_state.current_player.name})")
    print(f"  Phase: {engine.game_state.current_phase.value}")
    print(f"  Ashley hand: {len(players[0].hand)}, deck: {len(players[0].deck)}")
    print(f"  Tace hand: {len(players[1].hand)}, deck: {len(players[1].deck)}")
    print(f"  card_drawn_this_turn: {engine.game_state.card_drawn_this_turn}")
    
    # Stop if we see a card draw
    if hasattr(message, 'event_data') and message.event_data and message.event_data.get('type') == 'draw_cards':
        print("*** CARD DRAW DETECTED! ***")
        break
        
    # Stop if we're looping
    if i > 10 and engine.game_state.current_phase.value == 'draw':
        print("*** STUCK IN DRAW PHASE ***")
        break