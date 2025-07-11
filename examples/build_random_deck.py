#!/usr/bin/env python3
"""
Interactive deck builder for Lorcana simulation.
Prompts user for preferences and builds a custom deck with detailed analysis.
"""

import sys
from pathlib import Path
from typing import List, Optional

from lorcana_sim.utils.deck_builder import DeckBuilder
from lorcana_sim.models.cards.base_card import CardColor
from lorcana_sim.loaders.lorcana_json_parser import LorcanaJsonParser


def print_welcome():
    """Print welcome message and introduction."""
    print("=" * 60)
    print("🎴 LORCANA INTERACTIVE DECK BUILDER 🎴")
    print("=" * 60)
    print()
    print("Welcome to the interactive Lorcana deck builder!")
    print("I'll help you create a custom deck based on your preferences.")
    print("Your deck will be analyzed for strategy, curve, and competitiveness.")
    print()


def get_user_choice(prompt: str, options: List[str], allow_multiple: bool = False) -> str | List[str]:
    """Get user choice from a list of options."""
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    if allow_multiple:
        print(f"  Enter numbers separated by commas (e.g., 1,3,5) or 'all' for all options")
    print()
    
    while True:
        try:
            user_input = input("Your choice: ").strip()
            
            if allow_multiple and user_input.lower() == 'all':
                return options
            
            if allow_multiple and ',' in user_input:
                indices = [int(x.strip()) for x in user_input.split(',')]
                selected = [options[i-1] for i in indices if 1 <= i <= len(options)]
                if selected:
                    return selected
                else:
                    print("❌ Invalid selection. Please try again.")
                    continue
            else:
                choice = int(user_input)
                if 1 <= choice <= len(options):
                    return options[choice - 1] if not allow_multiple else [options[choice - 1]]
                else:
                    print(f"❌ Please enter a number between 1 and {len(options)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Thanks for using the deck builder!")
            sys.exit(0)


def get_deck_name() -> str:
    """Get custom deck name from user."""
    print("What would you like to name your deck?")
    try:
        name = input("Deck name (or press Enter for auto-generated): ").strip()
        if name:
            return name
        else:
            return None  # Will auto-generate
    except (EOFError, KeyboardInterrupt):
        return None


def get_random_seed() -> Optional[int]:
    """Get random seed for reproducible results."""
    print("\nWould you like to set a random seed for reproducible results?")
    print("This allows you to regenerate the exact same deck later.")
    
    try:
        choice = input("Enter a number (or press Enter to skip): ").strip()
        if choice:
            try:
                return int(choice)
            except ValueError:
                print("Using random seed...")
                return None
        return None
    except (EOFError, KeyboardInterrupt):
        return None


def analyze_deck_strategy(deck) -> str:
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


def analyze_color_identity(deck) -> str:
    """Analyze deck's color identity and synergies."""
    color_dist = deck.get_color_distribution()
    total_cards = deck.total_cards
    
    # Sort colors by count
    sorted_colors = sorted(color_dist.items(), key=lambda x: x[1], reverse=True)
    
    if len(sorted_colors) == 1:
        return f"🎯 **MONO-{sorted_colors[0][0].upper()}** - Pure color identity with maximum consistency"
    elif len(sorted_colors) == 2 and sorted_colors[1][1] >= total_cards * 0.2:
        return f"🌈 **{sorted_colors[0][0]}-{sorted_colors[1][0]}** - Dual-color build with good mana base"
    elif sorted_colors[0][1] >= total_cards * 0.6:
        return f"🎨 **{sorted_colors[0][0]} SPLASH** - Primarily {sorted_colors[0][0]} with support colors"
    else:
        return "🎪 **RAINBOW** - Multi-color deck with diverse options"


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


def print_detailed_analysis(deck):
    """Print comprehensive deck analysis."""
    print("=" * 60)
    print("📊 DETAILED DECK ANALYSIS")
    print("=" * 60)
    
    # Basic stats
    legal, errors = deck.is_legal()
    print(f"📋 **Deck Name:** {deck.name}")
    print(f"🎴 **Total Cards:** {deck.total_cards}")
    print(f"🔢 **Unique Cards:** {deck.unique_cards}")
    print(f"⚖️ **Legal for Play:** {'✅ Yes' if legal else '❌ No'}")
    if errors:
        for error in errors:
            print(f"   ⚠️ {error}")
    print()
    
    # Strategy analysis
    strategy, description = analyze_deck_strategy(deck)
    print(f"🎯 **Strategy:** {strategy}")
    print(f"   {description}")
    print()
    
    # Color identity
    color_identity = analyze_color_identity(deck)
    print(f"🎨 **Color Identity:** {color_identity}")
    
    # Color distribution
    color_dist = deck.get_color_distribution()
    print("   Color Breakdown:")
    for color, count in sorted(color_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck.total_cards) * 100
        bar = "█" * int(percentage // 4)  # Visual bar
        print(f"     {color}: {count} cards ({percentage:.1f}%) {bar}")
    print()
    
    # Curve analysis
    grade, quality, avg_cost, (early, mid, late) = analyze_curve_quality(deck)
    print(f"📈 **Mana Curve Grade:** {grade} ({quality})")
    print(f"💰 **Average Cost:** {avg_cost:.1f} ink")
    print(f"   Early Game (1-2): {early:.1f}%")
    print(f"   Mid Game (3-5): {mid:.1f}%")
    print(f"   Late Game (6+): {late:.1f}%")
    
    # Detailed curve
    cost_curve = deck.get_cost_curve()
    print("   Cost Distribution:")
    max_count = max(cost_curve.values()) if cost_curve else 1
    for cost in sorted(cost_curve.keys()):
        count = cost_curve[cost]
        bar = "█" * int((count / max_count) * 20)  # 20-char max bar
        print(f"     {cost} ink: {count:2d} cards {bar}")
    print()
    
    # Type distribution
    type_dist = deck.get_type_distribution()
    print("🃏 **Card Types:**")
    for card_type, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck.total_cards) * 100
        print(f"   {card_type}: {count} cards ({percentage:.1f}%)")
    print()
    
    # Competitive rating
    print("🏆 **Competitive Assessment:**")
    
    # Calculate overall score
    scores = []
    
    # Curve score (30 points)
    curve_score = {"A": 30, "B": 20, "C": 10}[grade]
    scores.append(("Mana Curve", curve_score, 30))
    
    # Legality score (20 points)
    legal_score = 20 if legal else 0
    scores.append(("Deck Legality", legal_score, 20))
    
    # Color consistency (25 points)
    color_count = len(color_dist)
    if color_count == 1:
        color_score = 25
    elif color_count == 2:
        color_score = 20
    elif color_count == 3:
        color_score = 15
    else:
        color_score = 10
    scores.append(("Color Consistency", color_score, 25))
    
    # Type balance (25 points)
    character_percent = (type_dist.get("Character", 0) / deck.total_cards) * 100
    if 60 <= character_percent <= 80:
        type_score = 25
    elif 45 <= character_percent <= 85:
        type_score = 20
    else:
        type_score = 15
    scores.append(("Type Balance", type_score, 25))
    
    total_score = sum(score for _, score, _ in scores)
    max_score = sum(max_pts for _, _, max_pts in scores)
    
    for category, score, max_pts in scores:
        percentage = (score / max_pts) * 100
        print(f"   {category}: {score}/{max_pts} ({percentage:.0f}%)")
    
    overall_percentage = (total_score / max_score) * 100
    print(f"\n🎯 **Overall Rating:** {total_score}/{max_score} ({overall_percentage:.0f}%)")
    
    if overall_percentage >= 85:
        rating = "🏆 Competitive"
    elif overall_percentage >= 70:
        rating = "⚔️ Tournament Viable"
    elif overall_percentage >= 55:
        rating = "🎮 Casual Play"
    else:
        rating = "🔧 Needs Work"
    
    print(f"   Grade: {rating}")
    print()


def main():
    """Main interactive deck builder."""
    print_welcome()
    
    # Load card database
    print("📚 Loading Lorcana card database...")
    card_db_path = Path("data/all-cards/allCards.json")
    if not card_db_path.exists():
        print("❌ Card database not found at data/all-cards/allCards.json")
        print("Please ensure the card database is available to use this tool.")
        return
    
    try:
        parser = LorcanaJsonParser(str(card_db_path))
        builder = DeckBuilder(parser.cards)
        stats = builder.get_statistics()
        print(f"✅ Loaded {stats['total_cards']} cards from database")
        print()
    except Exception as e:
        print(f"❌ Error loading card database: {e}")
        return
    
    # Get user preferences
    print("Let's build your custom deck! I'll ask you a few questions...")
    print()
    
    # 1. Choose build strategy
    strategies = [
        "Random deck (completely random selection)",
        "Aggro deck (fast, low-cost strategy)",
        "Control deck (late-game focused)",
        "Balanced deck (good mix of costs)",
        "Mono-color deck (single color focus)",
        "Tribal deck (character subtype synergy)"
    ]
    
    strategy = get_user_choice("🎯 What type of deck would you like to build?", strategies)
    print()
    
    # 2. Get additional parameters based on strategy
    deck_name = None
    primary_colors = []
    tribal_type = None
    
    if "Random" in strategy:
        deck_name = get_deck_name() or "Random Adventure"
        
    elif "Aggro" in strategy:
        colors = ["Amber", "Ruby", "Emerald", "Steel", "Sapphire", "Amethyst"]
        color_choice = get_user_choice("🔥 Choose primary color for your aggro deck:", colors)
        primary_colors = [getattr(CardColor, color_choice.upper())]
        deck_name = get_deck_name() or f"{color_choice} Aggro"
        
    elif "Control" in strategy:
        colors = ["Sapphire", "Amethyst", "Steel", "Amber", "Ruby", "Emerald"]
        color_choice = get_user_choice("🛡️ Choose primary color for your control deck:", colors)
        primary_colors = [getattr(CardColor, color_choice.upper())]
        deck_name = get_deck_name() or f"{color_choice} Control"
        
    elif "Balanced" in strategy:
        colors = ["Amber", "Ruby", "Emerald", "Steel", "Sapphire", "Amethyst"]
        color_choices = get_user_choice("⚖️ Choose 1-2 colors for your balanced deck:", colors, allow_multiple=True)
        primary_colors = [getattr(CardColor, color.upper()) for color in color_choices[:2]]
        color_name = "-".join(color_choices[:2])
        deck_name = get_deck_name() or f"{color_name} Balanced"
        
    elif "Mono-color" in strategy:
        colors = ["Amber", "Ruby", "Emerald", "Steel", "Sapphire", "Amethyst"]
        color_choice = get_user_choice("🎨 Choose your mono-color:", colors)
        primary_colors = [getattr(CardColor, color_choice.upper())]
        deck_name = get_deck_name() or f"Pure {color_choice}"
        
    elif "Tribal" in strategy:
        subtypes = ["Hero", "Villain", "Princess", "Storyborn", "Pirate", "Fairy", "Prince", "Queen", "Captain"]
        tribal_choice = get_user_choice("👥 Choose character type for tribal synergy:", subtypes)
        tribal_type = tribal_choice
        deck_name = get_deck_name() or f"{tribal_choice} Tribal"
    
    # 3. Get random seed
    seed = get_random_seed()
    
    # Build the deck
    print("\n🔨 Building your deck...")
    print("⏳ This may take a moment while I select the best cards...")
    
    try:
        if "Random" in strategy:
            deck = builder.build_random_deck(deck_name, seed=seed)
        elif "Aggro" in strategy:
            deck = builder.build_aggro_deck(primary_colors[0], deck_name, seed=seed)
        elif "Control" in strategy:
            deck = builder.build_control_deck(primary_colors[0], deck_name, seed=seed)
        elif "Balanced" in strategy:
            deck = builder.build_balanced_deck(primary_colors, deck_name, seed=seed)
        elif "Mono-color" in strategy:
            deck = builder.build_mono_color_deck(primary_colors[0], deck_name, seed=seed)
        elif "Tribal" in strategy:
            deck = builder.build_character_tribal_deck(tribal_type, deck_name, seed=seed)
        
        if deck is None:
            print("❌ Sorry, I couldn't build a deck with your specifications.")
            print("This might happen if there aren't enough cards of the requested type.")
            return
        
        print(f"✅ Successfully built '{deck.name}'!")
        print()
        
        # Provide detailed analysis
        print_detailed_analysis(deck)
        
        # Offer additional options
        print("🎮 **What would you like to do next?**")
        print("1. View some sample cards from your deck")
        print("2. Get deck building tips")
        print("3. Build another deck")
        print("4. Exit")
        
        choice = input("\nYour choice (1-4): ").strip()
        
        if choice == "1":
            print("\n🃏 **Sample Cards from Your Deck:**")
            shown_cards = set()
            card_count = 0
            
            for deck_card in deck.cards[:8]:  # Show up to 8 different cards
                card = deck_card.card
                if card.id not in shown_cards:
                    shown_cards.add(card.id)
                    card_count += 1
                    
                    if hasattr(card, 'strength'):  # Character card
                        print(f"   • {card.full_name} ({card.cost} ink)")
                        print(f"     {card.strength}⚔️/{card.willpower}❤️, {card.lore}◊ lore")
                    else:
                        print(f"   • {card.full_name} ({card.cost} ink)")
                        print(f"     {card.card_type}")
                    
                    if card.abilities:
                        for ability in card.abilities[:1]:  # Show first ability
                            print(f"     💫 {ability.full_text}")
                    print()
        
        elif choice == "2":
            print("\n💡 **Deck Building Tips:**")
            
            grade, quality, avg_cost, _ = analyze_curve_quality(deck)
            
            if grade == "C":
                print("• Your mana curve could use improvement. Try to balance low, mid, and high cost cards.")
            
            color_dist = deck.get_color_distribution()
            if len(color_dist) > 2:
                print("• Consider reducing colors for more consistent ink availability.")
            
            type_dist = deck.get_type_distribution()
            char_percent = (type_dist.get("Character", 0) / deck.total_cards) * 100
            if char_percent < 50:
                print("• Consider adding more characters - they're essential for board presence and lore generation.")
            elif char_percent > 85:
                print("• You might want some non-character cards for utility and removal.")
            
            if avg_cost > 5:
                print("• Your deck might be too expensive. Consider adding cheaper cards for early game.")
            elif avg_cost < 3:
                print("• Your deck is very aggressive! Make sure you have enough late-game threats.")
            
            print("• Remember: Characters generate lore, but Actions and Items provide utility!")
            print("• Ink cards wisely - you can only ink one card per turn!")
        
        elif choice == "3":
            print("\n🔄 Starting over...\n")
            main()  # Restart
            return
        
        print("\n🌟 Thanks for using the Lorcana Deck Builder!")
        print("May your games be filled with magic and adventure! ✨")
        
    except Exception as e:
        print(f"❌ An error occurred while building your deck: {e}")
        print("Please try again with different options.")


if __name__ == "__main__":
    main()