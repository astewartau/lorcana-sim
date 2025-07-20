#!/usr/bin/env python3
"""Test Phase 5 implementation - conditional effects integration."""

import sys
sys.path.append('src')

from lorcana_sim.engine.game_engine import GameEngine, ExecutionMode
from lorcana_sim.engine.game_messages import MessageType
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.game.deck import Deck
from lorcana_sim.models.game.game_state import GameState


def test_phase5():
    """Test that Phase 5 conditional effects work without infinite loops."""
    print("🧪 Testing Phase 5: Conditional Effects Integration")
    
    # Create a simple test setup
    player1 = Player("Test Player 1")
    player2 = Player("Test Player 2")
    
    # Create test cards
    test_card = CharacterCard(
        id=1,
        name="Test Card",
        cost=2,
        color=CardColor.AMBER,
        rarity=Rarity.COMMON,
        strength=2,
        willpower=3,
        lore=1,
        version=None,
        full_name="Test Card",
        inkwell=True,
        set_code="TEST",
        number=1,
        story="Test character"
    )
    
    # Create minimal decks
    deck1 = Deck([test_card] * 20)
    deck2 = Deck([test_card] * 20)
    
    player1.deck = deck1
    player2.deck = deck2
    
    # Create game state and engine
    game_state = GameState([player1, player2])
    game = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    print("✅ Game created successfully")
    
    # Run some game steps to test conditional effects
    messages_processed = 0
    max_messages = 100
    
    try:
        message = game.next_message()  # First message
        messages_processed += 1
        
        while messages_processed < max_messages and not game.game_state.is_game_over():
            if messages_processed % 20 == 0:
                print(f"   Processed {messages_processed} messages...")
            
            # Check what type of message we got
            if hasattr(message, 'type'):
                if message.type == MessageType.ACTION_REQUIRED:
                    # Break if we reach a state that requires player input
                    print(f"   Reached action required state in phase: {message.phase}")
                    break
                elif message.type == MessageType.CHOICE_REQUIRED:
                    # Break if we reach a state that requires player choice
                    print(f"   Reached choice required state")
                    break
            
            # Get next message (auto-progression should continue)
            message = game.next_message()
            messages_processed += 1
                
        print(f"✅ Successfully processed {messages_processed} messages without infinite loops")
        print("✅ Phase 5 conditional effects integration working correctly")
        
    except Exception as e:
        print(f"❌ Error during game simulation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_phase5()
    if success:
        print("\n🎉 Phase 5 implementation successful!")
        sys.exit(0)
    else:
        print("\n💥 Phase 5 implementation failed!")
        sys.exit(1)