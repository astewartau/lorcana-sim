#!/usr/bin/env python3
"""Test GRASPING TRUNK ability lore gain attribution."""

from examples.full_game_example import setup_game
from src.lorcana_sim.engine.game_engine import GameEngine, ExecutionMode
from src.lorcana_sim.engine.game_moves import PlayMove, QuestMove, PassMove
from src.lorcana_sim.models.game.phase import Phase

def test_grasping_trunk_attribution():
    """Test that GRASPING TRUNK shows proper lore gain attribution."""
    game_state = setup_game()
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    engine.start_game()
    
    print("🧪 Testing GRASPING TRUNK lore gain attribution...")
    print("=" * 60)
    
    # Get to play phase
    while game_state.current_phase != Phase.PLAY:
        message = engine.next_message()
        if hasattr(message, 'phase') and message.phase != Phase.PLAY:
            engine.next_message(PassMove())
    
    # Play ink and characters for setup
    for i in range(6):  # Get enough ink to play Abu (4 cost)
        # Progress to next turn
        while game_state.current_phase != Phase.PLAY:
            message = engine.next_message()
            if hasattr(message, 'phase') and message.phase != Phase.PLAY:
                engine.next_message(PassMove())
        
        # Find Abu in hand and play ink
        current_player = game_state.current_player
        abu_card = None
        ink_card = None
        
        for card in current_player.hand:
            if 'Abu' in card.name and current_player.can_afford(card):
                abu_card = card
                break
            elif not ink_card:  # Use first card as ink
                ink_card = card
        
        if abu_card:
            print(f"🎭 Found Abu in hand, playing him!")
            engine.next_message(PlayMove(card=abu_card))
            break
        elif ink_card:
            print(f"🔮 Playing {ink_card.name} as ink")
            from src.lorcana_sim.engine.game_moves import InkMove
            engine.next_message(InkMove(card=ink_card))
        
        # End turn
        engine.next_message(PassMove())
    
    # Also need an enemy character for the ability to target
    # Switch to other player and play a character
    while game_state.current_phase != Phase.PLAY:
        message = engine.next_message()
        if hasattr(message, 'phase') and message.phase != Phase.PLAY:
            engine.next_message(PassMove())
    
    current_player = game_state.current_player
    for card in current_player.hand:
        if hasattr(card, 'lore') and card.lore > 0 and current_player.can_afford(card):
            print(f"🎭 Playing {card.name} as target for GRASPING TRUNK")
            engine.next_message(PlayMove(card=card))
            break
    
    # Switch back and quest with Abu to trigger GRASPING TRUNK
    engine.next_message(PassMove())
    
    # Get to next turn and ready Abu
    while game_state.current_phase != Phase.PLAY:
        message = engine.next_message()
        if hasattr(message, 'phase') and message.phase != Phase.PLAY:
            engine.next_message(PassMove())
    
    # Find Abu and quest with him
    current_player = game_state.current_player
    for character in current_player.characters:
        if 'Abu' in character.name and not character.exerted:
            print(f"🏆 Abu questing to trigger GRASPING TRUNK!")
            engine.next_message(QuestMove(character=character))
            
            # Process the next few messages to see the trigger
            for i in range(5):
                message = engine.next_message()
                print(f"Message {i+1}: {message}")
            break
    
    print("\n🎯 Test complete - check above for GRASPING TRUNK lore attribution!")

if __name__ == "__main__":
    test_grasping_trunk_attribution()