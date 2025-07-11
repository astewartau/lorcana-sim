#!/usr/bin/env python3
"""
Demo script showing the interactive deck builder without requiring user input.
This demonstrates the analysis capabilities on pre-built decks.
"""

from pathlib import Path

from lorcana_sim.utils.deck_builder import DeckBuilder
from lorcana_sim.models.cards.base_card import CardColor
from lorcana_sim.loaders.lorcana_json_parser import LorcanaJsonParser


def analyze_deck_strategy(deck) -> tuple:
    """Analyze deck and determine its likely strategy."""
    cost_curve = deck.get_cost_curve()
    total_cards = deck.total_cards
    
    low_cost = sum(count for cost, count in cost_curve.items() if cost <= 3)
    mid_cost = sum(count for cost, count in cost_curve.items() if 4 <= cost <= 6)
    high_cost = sum(count for cost, count in cost_curve.items() if cost >= 7)
    
    low_percent = (low_cost / total_cards) * 100
    high_percent = (high_cost / total_cards) * 100
    
    type_dist = deck.get_type_distribution()
    character_percent = (type_dist.get("Character", 0) / total_cards) * 100
    
    # Determine strategy
    if low_percent >= 50:
        strategy = "🏃 **AGGRO** - Fast, aggressive strategy"
        description = "This deck wants to win quickly by playing cheap, efficient threats and dealing damage early."
    elif high_percent >= 30:
        strategy = "🛡️ **CONTROL** - Late-game powerhouse"
        description = "This deck aims to survive the early game and win with powerful late-game cards."
    elif character_percent >= 80:
        strategy = "👥 **CREATURE-BASED** - Board control focused"
        description = "This deck relies heavily on characters to control the board and pressure opponents."
    else:
        strategy = "⚖️ **MIDRANGE** - Balanced approach"
        description = "This deck has a balanced curve, adapting to different game states."
    
    return strategy, description


def analyze_curve_quality(deck) -> tuple:
    """Analyze the quality of the deck's mana curve."""
    cost_curve = deck.get_cost_curve()
    total_cards = deck.total_cards
    
    # Calculate average cost
    total_cost = sum(cost * count for cost, count in cost_curve.items())
    avg_cost = total_cost / total_cards
    
    # Analyze curve shape
    early_game = sum(count for cost, count in cost_curve.items() if cost <= 2)
    mid_game = sum(count for cost, count in cost_curve.items() if 3 <= cost <= 5)
    late_game = sum(count for cost, count in cost_curve.items() if cost >= 6)
    
    early_percent = (early_game / total_cards) * 100
    mid_percent = (mid_game / total_cards) * 100
    late_percent = (late_game / total_cards) * 100
    
    # Grade the curve
    if 15 <= early_percent <= 35 and 30 <= mid_percent <= 50 and 15 <= late_percent <= 35:
        grade = "A"
        quality = "Excellent"
    elif 10 <= early_percent <= 45 and 25 <= mid_percent <= 60 and 10 <= late_percent <= 45:
        grade = "B"
        quality = "Good"
    else:
        grade = "C"
        quality = "Needs improvement"
    
    return grade, quality, avg_cost, (early_percent, mid_percent, late_percent)


def print_deck_analysis(deck):
    """Print analysis similar to the interactive builder."""
    print("=" * 60)
    print(f"📊 ANALYSIS: {deck.name}")
    print("=" * 60)
    
    # Basic stats
    legal, errors = deck.is_legal()
    print(f"🎴 **Total Cards:** {deck.total_cards}")
    print(f"🔢 **Unique Cards:** {deck.unique_cards}")
    print(f"⚖️ **Legal for Play:** {'✅ Yes' if legal else '❌ No'}")
    print()
    
    # Strategy analysis
    strategy, description = analyze_deck_strategy(deck)
    print(f"🎯 **Strategy:** {strategy}")
    print(f"   {description}")
    print()
    
    # Color distribution with visual bars
    color_dist = deck.get_color_distribution()
    print("🎨 **Color Distribution:**")
    for color, count in sorted(color_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck.total_cards) * 100
        bar = "█" * int(percentage // 5)  # Visual bar
        print(f"   {color}: {count} cards ({percentage:.1f}%) {bar}")
    print()
    
    # Curve analysis
    grade, quality, avg_cost, (early, mid, late) = analyze_curve_quality(deck)
    print(f"📈 **Mana Curve:** Grade {grade} ({quality})")
    print(f"💰 **Average Cost:** {avg_cost:.1f} ink")
    print(f"   Early (1-2): {early:.1f}% | Mid (3-5): {mid:.1f}% | Late (6+): {late:.1f}%")
    
    # Visual curve
    cost_curve = deck.get_cost_curve()
    print("   Cost Distribution:")
    max_count = max(cost_curve.values()) if cost_curve else 1
    for cost in sorted(cost_curve.keys()):
        count = cost_curve[cost]
        bar = "█" * int((count / max_count) * 15)  # 15-char max bar
        print(f"     {cost}: {count:2d} {bar}")
    print()
    
    # Type distribution
    type_dist = deck.get_type_distribution()
    print("🃏 **Card Types:**")
    for card_type, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck.total_cards) * 100
        print(f"   {card_type}: {count} cards ({percentage:.1f}%)")
    print()


def main():
    """Demonstrate interactive deck analysis without user input."""
    print("🎴 LORCANA DECK ANALYZER DEMO")
    print("=" * 50)
    print()
    print("This demo shows the analysis capabilities of our interactive deck builder")
    print("by creating and analyzing several different deck archetypes.")
    print()
    
    # Load card database
    print("📚 Loading card database...")
    card_db_path = Path("data/all-cards/allCards.json")
    if not card_db_path.exists():
        print("❌ Card database not found at data/all-cards/allCards.json")
        return
    
    parser = LorcanaJsonParser(str(card_db_path))
    builder = DeckBuilder(parser.cards)
    stats = builder.get_statistics()
    print(f"✅ Loaded {stats['total_cards']} cards")
    print()
    
    # Build and analyze different deck types
    deck_configs = [
        ("Ruby Aggro", lambda: builder.build_aggro_deck(CardColor.RUBY, "Ruby Rush", seed=42)),
        ("Sapphire Control", lambda: builder.build_control_deck(CardColor.SAPPHIRE, "Sapphire Control", seed=42)),
        ("Princess Tribal", lambda: builder.build_character_tribal_deck("Princess", "Princess Power", seed=42)),
        ("Amber-Steel Balanced", lambda: builder.build_balanced_deck([CardColor.AMBER, CardColor.STEEL], "Amber-Steel Balance", seed=42)),
        ("Random Chaos", lambda: builder.build_random_deck("Random Chaos", seed=42))
    ]
    
    for name, build_func in deck_configs:
        print(f"🔨 Building {name}...")
        deck = build_func()
        
        if deck:
            print_deck_analysis(deck)
            
            # Show a few sample cards
            print("🃏 **Sample Cards:**")
            for deck_card in deck.cards[:3]:  # Show first 3 unique cards
                card = deck_card.card
                if hasattr(card, 'strength'):  # Character
                    print(f"   • {card.full_name} ({card.cost} ink) - {card.strength}⚔️/{card.willpower}❤️")
                else:
                    print(f"   • {card.full_name} ({card.cost} ink) - {card.card_type}")
            
            print("\n" + "="*60 + "\n")
        else:
            print(f"❌ Could not build {name}")
            print()
    
    print("🎯 **Analysis Summary:**")
    print("• The analyzer identifies deck archetypes based on cost curves and card types")
    print("• Mana curves are graded from A (excellent) to C (needs work)")
    print("• Color consistency affects deck reliability")
    print("• Character percentages indicate deck strategy focus")
    print("• Visual bars help understand distributions at a glance")
    print()
    print("✨ Try running `python examples/build_random_deck.py` for the full interactive experience!")


if __name__ == "__main__":
    main()