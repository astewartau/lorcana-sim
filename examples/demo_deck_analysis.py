#!/usr/bin/env python3
"""
Demo script for detailed deck analysis.

This script analyzes a specific deck by cross-referencing with the full card database
to provide insights into franchises, keywords, abilities, and deck composition.
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from loaders.lorcana_json_parser import LorcanaJsonParser
from loaders.dreamborn_parser import DreambornParser


def print_section(title: str, separator: str = "=") -> None:
    """Print a formatted section header"""
    print(f"\n{separator * 60}")
    print(f" {title}")
    print(f"{separator * 60}")


def print_subsection(title: str) -> None:
    """Print a formatted subsection header"""
    print(f"\n{title}")
    print("-" * len(title))


def analyze_deck(deck_path: str, card_db_path: str) -> None:
    """Perform comprehensive deck analysis"""
    
    # Load data
    print("Loading card database and deck...")
    lorcana_parser = LorcanaJsonParser(card_db_path)
    dreamborn_parser = DreambornParser(deck_path)
    
    # Get deck info
    deck_info = dreamborn_parser.get_deck_info()
    deck_summary = dreamborn_parser.get_deck_summary()
    
    # Get full card data for each card in deck
    # Note: Dreamborn CardIDs don't match lorcana-json IDs, so we use card names
    deck_cards = []
    deck_card_list = dreamborn_parser.get_card_list()
    
    for deck_card in deck_card_list:
        # Use the nickname which corresponds to fullName in the card database
        card = lorcana_parser.get_card_by_fullname(deck_card.nickname)
        if card:
            # Add multiple copies of the card based on quantity
            for _ in range(deck_card.quantity):
                deck_cards.append(card)
        else:
            print(f"Warning: Could not find card '{deck_card.nickname}' in database")
    
    print_section("DECK OVERVIEW")
    print(f"Total Cards: {deck_info.total_cards}")
    print(f"Unique Cards: {deck_info.unique_cards}")
    
    # Validate deck legality
    issues = dreamborn_parser.validate_deck_format()
    if issues:
        print(f"\nDeck Issues:")
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print(f"\n✅ Deck is legal!")
    
    # Color Analysis
    print_section("COLOR COMPOSITION")
    color_counts = Counter()
    color_card_names = defaultdict(list)
    for card in deck_cards:
        color = card.get('color', 'Unknown')
        color_counts[color] += 1
        color_card_names[color].append(card.get('fullName', 'Unknown'))
    
    for color, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck_info.total_cards) * 100
        print(f"\n{color}: {count} cards ({percentage:.1f}%)")
        # Show unique cards in this color
        unique_cards = set(color_card_names[color])
        for card_name in sorted(unique_cards):
            count_in_deck = color_card_names[color].count(card_name)
            print(f"  • {count_in_deck}x {card_name}")
    
    # Franchise/Story Analysis
    print_section("FRANCHISE REPRESENTATION")
    franchise_counts = Counter()
    franchise_cards = defaultdict(list)
    for card in deck_cards:
        franchise = card.get('story', 'Unknown')
        if franchise:
            franchise_counts[franchise] += 1
            franchise_cards[franchise].append(card.get('fullName', 'Unknown'))
    
    for franchise, count in sorted(franchise_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck_info.total_cards) * 100
        print(f"\n{franchise}: {count} cards ({percentage:.1f}%)")
        unique_cards = set(franchise_cards[franchise])
        for card_name in sorted(unique_cards):
            count_in_deck = franchise_cards[franchise].count(card_name)
            print(f"  • {count_in_deck}x {card_name}")
    
    # Card Type Distribution
    print_section("CARD TYPE DISTRIBUTION")
    type_counts = Counter()
    type_details = defaultdict(list)
    for card in deck_cards:
        card_type = card.get('type', 'Unknown')
        type_counts[card_type] += 1
        type_details[card_type].append(card)
    
    for card_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck_info.total_cards) * 100
        print(f"\n{card_type}: {count} cards ({percentage:.1f}%)")
        
        if card_type == 'Character':
            # Show character stats distribution
            strength_dist = Counter(c.get('strength', 0) for c in type_details[card_type])
            willpower_dist = Counter(c.get('willpower', 0) for c in type_details[card_type])
            lore_dist = Counter(c.get('lore', 0) for c in type_details[card_type])
            
            print(f"  Strength distribution: {dict(sorted(strength_dist.items()))}")
            print(f"  Willpower distribution: {dict(sorted(willpower_dist.items()))}")
            print(f"  Lore value distribution: {dict(sorted(lore_dist.items()))}")
    
    # Mana Curve Analysis
    print_section("MANA CURVE")
    cost_distribution = Counter()
    cost_by_type = defaultdict(lambda: defaultdict(int))
    for card in deck_cards:
        cost = card.get('cost', 0)
        card_type = card.get('type', 'Unknown')
        cost_distribution[cost] += 1
        cost_by_type[cost][card_type] += 1
    
    print("\nOverall Mana Curve:")
    for cost in sorted(cost_distribution.keys()):
        count = cost_distribution[cost]
        bar = "█" * count
        print(f"  {cost}: {bar} ({count})")
    
    print("\nMana Curve by Type:")
    for cost in sorted(cost_by_type.keys()):
        types = cost_by_type[cost]
        type_str = ", ".join(f"{count} {t}" for t, count in sorted(types.items()))
        print(f"  {cost} cost: {type_str}")
    
    # Keyword Analysis
    print_section("KEYWORD ABILITIES")
    keyword_counts = Counter()
    keyword_cards = defaultdict(list)
    
    for card in deck_cards:
        # Check for keywordAbilities array (primary way keywords are stored)
        keyword_abilities = card.get('keywordAbilities', [])
        for keyword in keyword_abilities:
            keyword_counts[keyword] += 1
            keyword_cards[keyword].append(card.get('fullName', 'Unknown'))
        
        # Also check abilities array for backward compatibility
        abilities = card.get('abilities', [])
        for ability in abilities:
            if ability.get('type') == 'keyword':
                keyword = ability.get('keyword', ability.get('name', 'Unknown'))
                if keyword not in keyword_abilities:  # Avoid double counting
                    keyword_counts[keyword] += 1
                    keyword_cards[keyword].append(card.get('fullName', 'Unknown'))
    
    if keyword_counts:
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"\n{keyword}: {count} instances")
            unique_cards = set(keyword_cards[keyword])
            for card_name in sorted(unique_cards):
                print(f"  • {card_name}")
    else:
        print("\nNo keyword abilities found in deck.")
    
    # Other Abilities Analysis
    print_section("OTHER ABILITIES")
    ability_types = Counter()
    unique_abilities = {}  # Use dict to track unique abilities
    
    for card in deck_cards:
        abilities = card.get('abilities', [])
        for ability in abilities:
            ability_type = ability.get('type', 'unknown')
            ability_types[ability_type] += 1
            
            if ability_type != 'keyword':
                # Create a unique key for each ability
                ability_name = ability.get('name', '')
                ability_effect = ability.get('effect', ability.get('fullText', ''))
                card_name = card.get('fullName', 'Unknown')
                
                # Use ability name and card name as unique key
                unique_key = f"{card_name}|{ability_name}"
                
                if unique_key not in unique_abilities:
                    unique_abilities[unique_key] = {
                        'card': card_name,
                        'type': ability_type,
                        'name': ability_name,
                        'effect': ability_effect,
                        'count': 1
                    }
                else:
                    unique_abilities[unique_key]['count'] += 1
    
    print("\nAbility Type Distribution:")
    for ability_type, count in sorted(ability_types.items()):
        print(f"  {ability_type}: {count}")
    
    print("\nUnique Abilities by Type:")
    # Group by ability type and show all unique abilities
    for ability_type in ['triggered', 'activated', 'static']:
        type_abilities = [a for a in unique_abilities.values() if a['type'] == ability_type]
        if type_abilities:
            print(f"\n{ability_type.capitalize()} Abilities ({len(type_abilities)} unique):")
            # Sort by count (most common first) then by card name
            sorted_abilities = sorted(type_abilities, key=lambda x: (-x['count'], x['card']))
            for ability in sorted_abilities:
                count_str = f" (x{ability['count']})" if ability['count'] > 1 else ""
                if ability['name']:
                    print(f"  • {ability['card']} - {ability['name']}{count_str}")
                    if ability['effect']:
                        # Truncate long effects
                        effect = ability['effect'][:100] + "..." if len(ability['effect']) > 100 else ability['effect']
                        print(f"    → {effect}")
    
    # Rarity Distribution
    print_section("RARITY DISTRIBUTION")
    rarity_counts = Counter()
    rarity_cards = defaultdict(list)
    for card in deck_cards:
        rarity = card.get('rarity', 'Unknown')
        rarity_counts[rarity] += 1
        rarity_cards[rarity].append(card.get('fullName', 'Unknown'))
    
    for rarity, count in sorted(rarity_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck_info.total_cards) * 100
        print(f"\n{rarity}: {count} cards ({percentage:.1f}%)")
        unique_cards = set(rarity_cards[rarity])
        for card_name in sorted(unique_cards):
            count_in_deck = rarity_cards[rarity].count(card_name)
            print(f"  • {count_in_deck}x {card_name}")
    
    # Inkwell Analysis
    print_section("INKWELL ANALYSIS")
    inkable_count = sum(1 for card in deck_cards if card.get('inkwell', False))
    non_inkable_count = deck_info.total_cards - inkable_count
    inkable_percentage = (inkable_count / deck_info.total_cards) * 100
    
    print(f"Inkable cards: {inkable_count} ({inkable_percentage:.1f}%)")
    print(f"Non-inkable cards: {non_inkable_count} ({100 - inkable_percentage:.1f}%)")
    
    # Character Subtypes
    print_section("CHARACTER SUBTYPES")
    subtype_counts = Counter()
    for card in deck_cards:
        if card.get('type') == 'Character':
            subtypes = card.get('subtypes', [])
            for subtype in subtypes:
                subtype_counts[subtype] += 1
    
    if subtype_counts:
        print("\nCharacter Subtype Distribution:")
        for subtype, count in sorted(subtype_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {subtype}: {count}")
    
    # Deck Strategy Summary
    print_section("DECK STRATEGY SUMMARY", "=")
    
    # Determine primary colors
    primary_colors = [color for color, count in color_counts.most_common(2)]
    print(f"\nPrimary Colors: {' / '.join(primary_colors)}")
    
    # Determine main franchises
    main_franchises = [franchise for franchise, count in franchise_counts.most_common(3)]
    print(f"Main Franchises: {', '.join(main_franchises)}")
    
    # Average stats for characters
    character_cards = [c for c in deck_cards if c.get('type') == 'Character']
    if character_cards:
        avg_cost = sum(c.get('cost', 0) for c in character_cards) / len(character_cards)
        avg_strength = sum(c.get('strength', 0) for c in character_cards) / len(character_cards)
        avg_willpower = sum(c.get('willpower', 0) for c in character_cards) / len(character_cards)
        avg_lore = sum(c.get('lore', 0) for c in character_cards) / len(character_cards)
        
        print(f"\nAverage Character Stats:")
        print(f"  Cost: {avg_cost:.1f}")
        print(f"  Strength: {avg_strength:.1f}")
        print(f"  Willpower: {avg_willpower:.1f}")
        print(f"  Lore Value: {avg_lore:.1f}")
    
    # Key mechanics
    if keyword_counts:
        key_mechanics = [keyword for keyword, count in keyword_counts.most_common(3)]
        print(f"\nKey Mechanics: {', '.join(key_mechanics)}")
    
    print("\n" + "=" * 60)
    print(" Analysis Complete!")
    print("=" * 60)


def main():
    """Main function"""
    # File paths
    deck_path = "data/decks/tace.json"
    card_db_path = "data/all-cards/allCards.json"
    
    # Check files exist
    if not Path(deck_path).exists():
        print(f"Error: Deck file not found at {deck_path}")
        return
    
    if not Path(card_db_path).exists():
        print(f"Error: Card database not found at {card_db_path}")
        return
    
    # Run analysis
    analyze_deck(deck_path, card_db_path)


if __name__ == "__main__":
    main()
