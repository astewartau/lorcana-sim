"""Test the new message-based interface for the stepped game engine."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.stepped_game_engine import SteppedGameEngine
from src.lorcana_sim.engine.game_messages import MessageType, ActionRequiredMessage, StepExecutedMessage, ChoiceRequiredMessage
from src.lorcana_sim.engine.game_moves import PlayMove, InkMove, QuestMove, ChoiceMove
from src.lorcana_sim.loaders.deck_loader import DeckLoader


def test_message_interface():
    """Test the new message-based interface."""
    print("🎲 Testing Message-Based Lorcana Game Interface!")
    print("=" * 50)
    
    # Set up game
    cards_db_path = os.path.join(os.path.dirname(__file__), 'data', 'all-cards', 'allCards.json')
    deck1_path = os.path.join(os.path.dirname(__file__), 'data', 'decks', 'amethyst-steel.json')
    deck2_path = os.path.join(os.path.dirname(__file__), 'data', 'decks', 'tace.json')
    
    loader = DeckLoader(cards_db_path)
    ashley, tace = loader.load_two_decks(deck1_path, deck2_path, "Ashley", "Tace")
    
    game_state = GameState([ashley, tace])
    engine = SteppedGameEngine(game_state)
    
    # Start the game
    engine.start_game()
    
    print("🎮 Game started! Using message interface...")
    print()
    
    # Get first message
    message = engine.next_message()
    print(f"📨 Message Type: {message.type.value}")
    
    if isinstance(message, ActionRequiredMessage):
        print(f"👤 {message.player.name}'s turn ({message.phase.value} phase)")
        print(f"⚖️  Legal actions: {len(message.legal_actions)}")
        
        # Show some legal actions
        for i, action in enumerate(message.legal_actions[:3]):
            target_name = action.target.name if action.target else "N/A"
            print(f"   {i+1}. {action.action.value} - {target_name}")
        
        if len(message.legal_actions) > 3:
            print(f"   ... and {len(message.legal_actions) - 3} more")
        
        # Try to progress first to get to play phase
        progress_actions = [a for a in message.legal_actions if a.action.value == "PROGRESS"]
        if progress_actions:
            print(f"\n⏭️ Progressing to next phase...")
            from src.lorcana_sim.engine.game_moves import PassMove
            move = PassMove()
            message = engine.next_message(move)
            
            if isinstance(message, StepExecutedMessage):
                print(f"✅ Step: {message.description}")
                print(f"   Result: {message.result}")
                
                # Continue to get next action required
                message = engine.next_message()
                print(f"\n📨 Next Message: {message.type.value}")
                
                if isinstance(message, ActionRequiredMessage):
                    print(f"👤 {message.player.name}'s turn ({message.phase.value} phase)")
                    print(f"⚖️  Legal actions: {len(message.legal_actions)}")
                    
                    # Show ink actions if we're in play phase
                    ink_actions = [a for a in message.legal_actions if a.action.value == "PLAY_INK"]
                    if ink_actions:
                        card_to_ink = ink_actions[0].target
                        print(f"\n🔮 Inking {card_to_ink.name}...")
                        
                        move = InkMove(card=card_to_ink)
                        message = engine.next_message(move)
                        
                        if isinstance(message, StepExecutedMessage):
                            print(f"✅ Step: {message.description}")
                            print(f"   Result: {message.result}")
                            
                            # Get next message
                            message = engine.next_message()
                            print(f"\n📨 Next Message: {message.type.value}")
                            
                            if isinstance(message, ChoiceRequiredMessage):
                                print(f"🎯 Choice required: {message.choice.prompt}")
                                for option in message.choice.options:
                                    print(f"   • {option.id}: {option.description}")
                                
                                # Auto-choose "yes" if available
                                if any(opt.id == "yes" for opt in message.choice.options):
                                    choice_move = ChoiceMove(choice_id=message.choice.choice_id, option="yes")
                                    message = engine.next_message(choice_move)
                                    print(f"✅ Choice resolved: {message.result}")
                            
                            elif isinstance(message, ActionRequiredMessage):
                                print(f"👤 {message.player.name} can take another action")
        
        print(f"\n📊 Current game state:")
        print(f"   Ashley: {ashley.lore} lore, {ashley.available_ink}/{ashley.total_ink} ink")
        print(f"   Tace: {tace.lore} lore, {tace.available_ink}/{tace.total_ink} ink")


if __name__ == "__main__":
    try:
        test_message_interface()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()