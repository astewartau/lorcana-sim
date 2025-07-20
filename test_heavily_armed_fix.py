#!/usr/bin/env python3
"""Quick test script to verify HEAVILY ARMED ability triggers correctly."""

import sys
import os
sys.path.append('src')

from lorcana_sim.loaders.deck_loader import DeckLoader
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.engine.game_moves import PlayMove

def test_heavily_armed():
    print("🔧 Testing HEAVILY ARMED ability fix...")
    
    # Load decks
    deck_loader = DeckLoader('data/all-cards/allCards.json')
    player1, player2 = deck_loader.load_two_decks(
        'data/decks/amethyst-steel.json', 
        'data/decks/tace.json',
        'Ashley', 'Tace'
    )
    
    # Start game
    from lorcana_sim.models.game.game_state import GameState
    from lorcana_sim.engine.game_engine import ExecutionMode
    
    game_state = GameState([player1, player2])
    engine = GameEngine(game_state, ExecutionMode.MANUAL)
    engine.start_game()
    
    print(f"\n🎮 Game started. Current player: {engine.game_state.current_player.name}")
    
    # Check if Ashley has Royal Guard anywhere (hand, deck)
    royal_guard = None
    all_cards = player1.hand + player1.deck
    for card in all_cards:
        if hasattr(card, 'name') and 'Royal Guard' in card.name:
            royal_guard = card
            break
    
    if royal_guard:
        print(f"✅ Found Royal Guard: {royal_guard.name}")
        
        # Manually place Royal Guard in play
        print(f"🎭 Manually placing Royal Guard in play...")
        if royal_guard in player1.hand:
            player1.hand.remove(royal_guard)
        elif royal_guard in player1.deck:
            player1.deck.remove(royal_guard)
        
        player1.characters_in_play.append(royal_guard)
        royal_guard.controller = player1  # This is the key fix - controller gets set
        print(f"✅ Royal Guard controller is now: {getattr(royal_guard.controller, 'name', 'None')}")
    else:
        print("❌ No Royal Guard found in Ashley's deck")
    
    # Now test drawing a card to trigger HEAVILY ARMED
    print(f"\n🃏 Testing HEAVILY ARMED trigger by drawing a card...")
    
    # Check if Royal Guard is in play first
    royal_guard_in_play = None
    for char in player1.characters_in_play:
        if hasattr(char, 'name') and 'Royal Guard' in char.name:
            royal_guard_in_play = char
            break
    
    if royal_guard_in_play:
        print(f"✅ Royal Guard is in play with controller: {getattr(royal_guard_in_play.controller, 'name', 'None')}")
        
        # Manually draw a card to trigger HEAVILY ARMED
        print(f"📝 Player1 deck has {len(player1.deck)} cards")
        if player1.deck:
            drawn_card = player1.deck.pop(0)
            player1.hand.append(drawn_card)
            print(f"📖 Drew a card successfully")
            
            # Trigger the CARD_DRAWN event manually
            from lorcana_sim.engine.event_system import EventContext, GameEvent
            
            print(f"🎯 Creating CARD_DRAWN event for player: {player1.name}")
            event_context = EventContext(
                event_type=GameEvent.CARD_DRAWN,
                source=drawn_card,
                player=player1,
                additional_data={'card': drawn_card}
            )
            
            print(f"🔥 Triggering CARD_DRAWN event...")
            engine.event_manager.trigger_event(event_context)
            print(f"📚 Drew card: {getattr(drawn_card, 'name', 'Unknown')}")
            
            print(f"🎪 Checking for ability trigger message...")
            # Check for ability trigger message
            trigger_msg = engine.next_message()
            if trigger_msg:
                print(f"✨ Ability trigger: {trigger_msg}")
            else:
                print("❌ No ability trigger message found")
    else:
        print("❌ No Royal Guard in play - can't test HEAVILY ARMED trigger")

if __name__ == "__main__":
    test_heavily_armed()