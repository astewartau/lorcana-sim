#!/usr/bin/env python3
"""
Demo script showing the DeckBuilder utility in action.
"""

from pathlib import Path

from lorcana_sim.utils.deck_builder import DeckBuilder
from lorcana_sim.models.cards.base_card import CardColor
from lorcana_sim.loaders.lorcana_json_parser import LorcanaJsonParser


def main():
    """Demonstrate deck building capabilities."""
    print("🏗️ Lorcana Deck Builder Demo")
    print("=" * 50)
    
    # Load card database
    print("📚 Loading card database...")
    card_db_path = Path("data/all-cards/allCards.json")
    if not card_db_path.exists():
        print("❌ Card database not found at data/all-cards/allCards.json")
        return
    
    parser = LorcanaJsonParser(str(card_db_path))
    builder = DeckBuilder(parser.cards)
    
    # Show database statistics
    stats = builder.get_statistics()
    print(f"✅ Loaded {stats['total_cards']} cards")
    print(f"   Colors: {', '.join(stats['by_color'].keys())}")
    print(f"   Types: {', '.join(stats['by_type'].keys())}")
    print(f"   Cost range: {stats['cost_range'][0]}-{stats['cost_range'][1]}")
    print()
    
    # Color distribution
    print("🎨 Cards by Color:")
    for color, count in stats['by_color'].items():
        percentage = (count / stats['total_cards']) * 100
        print(f"   {color}: {count} cards ({percentage:.1f}%)")
    print()
    
    # Build different types of decks
    print("🃏 Building Sample Decks...")
    print("-" * 30)
    
    # 1. Random Deck
    print("1️⃣ Random Deck")
    random_deck = builder.build_random_deck("Random Sample")
    if random_deck:
        print(f"   ✅ {random_deck.name}: {random_deck.total_cards} cards")
        print(f"   Colors: {random_deck.get_color_distribution()}")
        print(f"   Cost curve: {random_deck.get_cost_curve()}")
        legal, errors = random_deck.is_legal()
        print(f"   Legal: {'✅' if legal else '❌'}")
    print()
    
    # 2. Mono-color Decks
    print("2️⃣ Mono-Color Decks")
    colors_to_try = [CardColor.AMBER, CardColor.RUBY, CardColor.SAPPHIRE, CardColor.EMERALD]
    
    for color in colors_to_try:
        deck = builder.build_mono_color_deck(color)
        if deck:
            color_dist = deck.get_color_distribution()
            primary_percentage = (color_dist.get(color.value, 0) / deck.total_cards) * 100
            print(f"   ✅ {color.value} Deck: {deck.total_cards} cards ({primary_percentage:.0f}% {color.value})")
        else:
            print(f"   ❌ {color.value} Deck: Not enough cards")
    print()
    
    # 3. Archetype Decks
    print("3️⃣ Archetype Decks")
    
    # Aggro deck
    aggro_deck = builder.build_aggro_deck(CardColor.RUBY)
    if aggro_deck:
        cost_curve = aggro_deck.get_cost_curve()
        low_cost = sum(count for cost, count in cost_curve.items() if cost <= 3)
        print(f"   ✅ Ruby Aggro: {aggro_deck.total_cards} cards ({low_cost} low-cost)")
        print(f"      Cost curve: {cost_curve}")
    
    # Control deck
    control_deck = builder.build_control_deck(CardColor.SAPPHIRE)
    if control_deck:
        cost_curve = control_deck.get_cost_curve()
        high_cost = sum(count for cost, count in cost_curve.items() if cost >= 5)
        print(f"   ✅ Sapphire Control: {control_deck.total_cards} cards ({high_cost} high-cost)")
        print(f"      Cost curve: {cost_curve}")
    print()
    
    # 4. Tribal Decks
    print("4️⃣ Tribal Decks")
    subtypes_to_try = ["Hero", "Villain", "Princess", "Storyborn", "Pirate"]
    
    successful_tribal = 0
    for subtype in subtypes_to_try:
        deck = builder.build_character_tribal_deck(subtype)
        if deck:
            successful_tribal += 1
            type_dist = deck.get_type_distribution()
            characters = type_dist.get("Character", 0)
            print(f"   ✅ {subtype} Tribal: {deck.total_cards} cards ({characters} characters)")
        else:
            print(f"   ❌ {subtype} Tribal: Not enough cards")
    
    print(f"   Built {successful_tribal}/{len(subtypes_to_try)} tribal decks")
    print()
    
    # 5. Balanced Multi-Color Deck
    print("5️⃣ Balanced Multi-Color Deck")
    balanced_deck = builder.build_balanced_deck([CardColor.AMBER, CardColor.STEEL])
    if balanced_deck:
        color_dist = balanced_deck.get_color_distribution()
        cost_curve = balanced_deck.get_cost_curve()
        print(f"   ✅ Amber-Steel Balanced: {balanced_deck.total_cards} cards")
        print(f"      Colors: {color_dist}")
        print(f"      Cost curve: {cost_curve}")
        
        # Analyze curve distribution
        low = sum(count for cost, count in cost_curve.items() if cost <= 2)
        mid = sum(count for cost, count in cost_curve.items() if 3 <= cost <= 5)
        high = sum(count for cost, count in cost_curve.items() if cost >= 6)
        total = balanced_deck.total_cards
        
        print(f"      Distribution: {low} low ({low/total*100:.0f}%), {mid} mid ({mid/total*100:.0f}%), {high} high ({high/total*100:.0f}%)")
    print()
    
    # 6. Deck Comparison
    print("6️⃣ Deck Comparison")
    decks_to_compare = [
        ("Random", random_deck),
        ("Ruby Aggro", aggro_deck),
        ("Sapphire Control", control_deck),
        ("Amber-Steel", balanced_deck)
    ]
    
    print("   Deck Type        | Cards | Avg Cost | Character % | Legal")
    print("   -----------------|-------|----------|-------------|------")
    
    for name, deck in decks_to_compare:
        if deck:
            # Calculate average cost
            cost_curve = deck.get_cost_curve()
            total_cost = sum(cost * count for cost, count in cost_curve.items())
            avg_cost = total_cost / deck.total_cards if deck.total_cards > 0 else 0
            
            # Calculate character percentage
            type_dist = deck.get_type_distribution()
            char_percent = (type_dist.get("Character", 0) / deck.total_cards) * 100
            
            # Check legality
            legal, _ = deck.is_legal()
            legal_symbol = "✅" if legal else "❌"
            
            print(f"   {name:<16} | {deck.total_cards:>5} | {avg_cost:>8.1f} | {char_percent:>10.0f}% | {legal_symbol}")
    print()
    
    # 7. Performance Test
    print("7️⃣ Performance Test")
    print("   Building 10 random decks...")
    
    import time
    start_time = time.time()
    
    performance_decks = []
    for i in range(10):
        deck = builder.build_random_deck(f"Perf Test {i+1}", seed=i)
        if deck:
            performance_decks.append(deck)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"   ✅ Built {len(performance_decks)} decks in {duration:.2f} seconds")
    print(f"   Average: {duration/len(performance_decks):.3f} seconds per deck")
    print()
    
    print("✨ Demo completed!")
    print()
    print("🎯 Key Features Demonstrated:")
    print("   ✅ Database statistics and analysis")
    print("   ✅ Random deck generation")
    print("   ✅ Mono-color deck building")
    print("   ✅ Archetype-specific decks (Aggro, Control)")
    print("   ✅ Tribal/subtype-focused decks")
    print("   ✅ Balanced multi-color decks")
    print("   ✅ Deck analysis and comparison")
    print("   ✅ Performance optimization")
    print()
    print("💡 The DeckBuilder utility can create legal, thematic decks")
    print("   suitable for testing, AI training, or casual play!")


if __name__ == "__main__":
    main()
