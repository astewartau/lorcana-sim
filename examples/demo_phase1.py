#!/usr/bin/env python3
"""
Demo script showing Phase 1 implementation in action.
"""

from pathlib import Path

from lorcana_sim.models.cards.card_factory import CardFactory
from lorcana_sim.models.game.deck import Deck
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.loaders.lorcana_json_parser import LorcanaJsonParser


def main():
    """Demonstrate Phase 1 functionality."""
    print("🃏 Lorcana Sim Phase 1 Demo")
    print("=" * 40)
    
    # Load card database
    print("📚 Loading card database...")
    card_db_path = Path("data/all-cards/allCards.json")
    if not card_db_path.exists():
        print("❌ Card database not found at data/all-cards/allCards.json")
        return
    
    parser = LorcanaJsonParser(str(card_db_path))
    print(f"✅ Loaded {len(parser.cards)} cards from database")
    
    # Create some sample cards
    print("\n🎭 Creating sample cards...")
    sample_cards = []
    
    for i, card_data in enumerate(parser.cards[:10]):
        try:
            card = CardFactory.from_json(card_data)
            sample_cards.append(card)
            print(f"  • {card.full_name} ({card.card_type}, {card.cost} cost)")
        except Exception as e:
            print(f"  ❌ Error creating card {card_data.get('fullName', 'Unknown')}: {e}")
        
        if len(sample_cards) >= 6:
            break
    
    print(f"✅ Created {len(sample_cards)} sample cards")
    
    # Create a simple deck
    print("\n📦 Building demo deck...")
    deck = Deck("Demo Deck")
    
    # Add 3 different cards, 4 copies each, plus fill with first card to get 60
    for i, card in enumerate(sample_cards[:3]):
        deck.add_card(card, 4)
    
    # Fill to 60 cards with the first card
    remaining = 60 - deck.total_cards
    if remaining > 0 and sample_cards:
        deck.add_card(sample_cards[0], min(remaining, 4 - deck.find_card(sample_cards[0].id).quantity))
    
    print(f"  • Deck: {deck}")
    print(f"  • Legal: {deck.is_legal()[0]}")
    print(f"  • Color distribution: {deck.get_color_distribution()}")
    
    # Create players
    print("\n👥 Setting up players...")
    player1 = Player("Alice")
    player2 = Player("Bob")
    
    # Give them shuffled decks
    player1.deck = deck.shuffle()[:30]  # Half deck for demo
    player2.deck = deck.shuffle()[:30]
    
    # Draw opening hands
    player1.draw_cards(7)
    player2.draw_cards(7)
    
    print(f"  • {player1.name}: {player1.hand_size} cards in hand, {player1.deck_size} in deck")
    print(f"  • {player2.name}: {player2.hand_size} cards in hand, {player2.deck_size} in deck")
    
    # Create game
    print("\n🎲 Starting game...")
    game = GameState(players=[player1, player2])
    
    print(f"  • Turn {game.turn_number}, {game.current_phase.value} phase")
    print(f"  • Active player: {game.active_player.name}")
    print(f"  • Game over: {game.game_over}")
    
    # Show legal actions
    legal_actions = game.get_legal_actions()
    print(f"  • Legal actions: {len(legal_actions)}")
    for action, target in legal_actions[:3]:  # Show first 3
        if target:
            print(f"    - {action.value}: {target}")
        else:
            print(f"    - {action.value}")
    
    # Simulate a few turns
    print("\n⚡ Simulating gameplay...")
    
    for turn in range(3):
        print(f"\n--- Turn {game.turn_number} ---")
        
        # Execute phases automatically
        while game.current_phase.value != "main":
            game.execute_phase()
            print(f"  • {game.current_phase.value.title()} phase completed")
        
        print(f"  • {game.active_player.name}'s main phase")
        print(f"  • Hand: {game.active_player.hand_size} cards")
        print(f"  • Ink: {game.active_player.available_ink}")
        print(f"  • Lore: {game.active_player.lore}")
        
        # Play ink if possible
        if game.active_player.can_play_ink():
            inkable_cards = [c for c in game.active_player.hand if c.can_be_inked()]
            if inkable_cards:
                game.active_player.play_ink(inkable_cards[0])
                print(f"  • Played {inkable_cards[0].name} as ink")
        
        # Pass turn
        game.execute_action(game.get_legal_actions()[0][0])  # Pass turn
        
        # Check game over
        is_over, winner = game.is_game_over()
        if is_over:
            print(f"🏆 Game over! Winner: {winner.name}")
            break
    
    print("\n✨ Demo completed!")
    print("\nPhase 1 Implementation Features:")
    print("  ✅ Card models (Character, Action, Item, Location)")
    print("  ✅ Ability system foundation")
    print("  ✅ Deck building and validation")
    print("  ✅ Player state management")
    print("  ✅ Basic game state and turn structure")
    print("  ✅ JSON parsing from lorcana-json format")
    print("  ✅ Comprehensive test suite")
    print("  ✅ Pip package structure")


if __name__ == "__main__":
    main()