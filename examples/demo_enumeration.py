#!/usr/bin/env python3
"""
Demo script showcasing the enumeration capabilities of the Lorcana JSON parser.

This script demonstrates how to extract and analyze all the different components
of Lorcana cards from the lorcana-json format data.
"""

import sys
from pathlib import Path
from pprint import pprint

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from loaders.lorcana_json_parser import LorcanaJsonParser
from loaders.dreamborn_parser import DreambornParser


def print_section(title: str, content: str = "") -> None:
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    if content:
        print(content)


def display_top_items(items_dict: dict, title: str, top_n: int = 10) -> None:
    """Display top N items from a dictionary"""
    print(f"\n{title}:")
    if isinstance(items_dict, dict):
        # Sort by value (count) descending
        sorted_items = sorted(items_dict.items(), key=lambda x: x[1], reverse=True)
        for item, count in sorted_items[:top_n]:
            print(f"  {item}: {count}")
        if len(sorted_items) > top_n:
            print(f"  ... and {len(sorted_items) - top_n} more")
    else:
        print(f"  {items_dict}")


def main():
    """Main demo function"""
    print("Lorcana Card Database Analysis Demo")
    print("==================================")
    
    # File paths
    lorcana_json_path = "data/all-cards/allCards.json"
    dreamborn_deck_path = "data/decks/amethyst-steel.json"
    
    if not Path(lorcana_json_path).exists():
        print(f"Error: {lorcana_json_path} not found!")
        return
    
    if not Path(dreamborn_deck_path).exists():
        print(f"Error: {dreamborn_deck_path} not found!")
        return
    
    # Initialize parsers
    print("Loading card database...")
    lorcana_parser = LorcanaJsonParser(lorcana_json_path)
    
    print("Loading deck...")
    dreamborn_parser = DreambornParser(dreamborn_deck_path)
    
    # =================================================================
    # BASIC STATISTICS
    # =================================================================
    print_section("BASIC CARD STATISTICS")
    
    card_stats = lorcana_parser.get_card_statistics()
    print(f"Total cards in database: {card_stats.total_cards}")
    print(f"Inkable cards: {card_stats.inkable_cards}")
    print(f"Non-inkable cards: {card_stats.non_inkable_cards}")
    
    display_top_items(card_stats.cards_by_type, "Cards by Type")
    display_top_items(card_stats.cards_by_color, "Cards by Color")
    display_top_items(card_stats.cards_by_rarity, "Cards by Rarity")
    display_top_items(card_stats.cards_by_set, "Cards by Set")
    display_top_items(card_stats.cards_by_story, "Top Disney Stories", 15)
    
    # =================================================================
    # ABILITY ANALYSIS
    # =================================================================
    print_section("ABILITY SYSTEM ANALYSIS")
    
    ability_stats = lorcana_parser.get_ability_statistics()
    print(f"Total abilities across all cards: {ability_stats.total_abilities}")
    print(f"Unique ability names: {len(ability_stats.unique_ability_names)}")
    print(f"Unique keywords: {len(ability_stats.unique_keywords)}")
    
    display_top_items(ability_stats.abilities_by_type, "Abilities by Type")
    display_top_items(ability_stats.keyword_abilities, "Top Keyword Abilities", 20)
    
    print(f"\nAll Ability Types: {lorcana_parser.get_unique_ability_types()}")
    print(f"\nAll Keywords: {lorcana_parser.get_unique_keywords()}")
    
    # =================================================================
    # CHARACTER ANALYSIS
    # =================================================================
    print_section("CHARACTER CARD ANALYSIS")
    
    char_stats = lorcana_parser.get_character_statistics()
    print(f"Total character cards: {char_stats.total_characters}")
    print(f"Unique character subtypes: {len(char_stats.all_subtypes)}")
    
    display_top_items(char_stats.cost_distribution, "Characters by Cost")
    display_top_items(char_stats.strength_distribution, "Characters by Strength")
    display_top_items(char_stats.willpower_distribution, "Characters by Willpower")
    display_top_items(char_stats.lore_distribution, "Characters by Lore Value")
    display_top_items(char_stats.subtypes_frequency, "Top Character Subtypes", 25)
    
    # =================================================================
    # COMPREHENSIVE ENUMERATION
    # =================================================================
    print_section("COMPREHENSIVE FIELD ENUMERATION")
    
    print("Unique Card Types:", lorcana_parser.get_unique_card_types())
    print("Unique Colors:", lorcana_parser.get_unique_colors())
    print("Unique Rarities:", lorcana_parser.get_unique_rarities())
    print("Unique Subtypes:", len(lorcana_parser.get_unique_subtypes()), "total")
    print("Unique Stories:", len(lorcana_parser.get_unique_stories()), "total")
    
    # =================================================================
    # ABILITY EXAMPLES
    # =================================================================
    print_section("ABILITY EXAMPLES")
    
    ability_examples = lorcana_parser.get_ability_examples(limit=3)
    for ability_type, examples in ability_examples.items():
        print(f"\n{ability_type.upper()} Abilities:")
        for example in examples:
            print(f"  - {example['card_name']} (ID: {example['card_id']})")
            ability = example['ability']
            if ability.get('name'):
                print(f"    {ability['name']}: {ability.get('effect', 'No effect text')}")
            else:
                print(f"    {ability.get('fullText', 'No text')}")
    
    # =================================================================
    # CARD TYPE EXAMPLES
    # =================================================================
    print_section("CARD TYPE EXAMPLES")
    
    for card_type in lorcana_parser.get_unique_card_types():
        cards = lorcana_parser.find_cards_by_type(card_type)
        print(f"\n{card_type} Cards ({len(cards)} total):")
        for card in cards[:3]:  # Show first 3 examples
            print(f"  - {card.get('fullName', 'Unknown')} (ID: {card.get('id')})")
            if card_type == 'Character':
                print(f"    Cost: {card.get('cost')}, Strength: {card.get('strength')}, "
                      f"Willpower: {card.get('willpower')}, Lore: {card.get('lore')}")
            elif card_type == 'Location':
                print(f"    Cost: {card.get('cost')}, Move Cost: {card.get('moveCost')}, "
                      f"Willpower: {card.get('willpower')}")
            else:
                print(f"    Cost: {card.get('cost')}, Color: {card.get('color')}")
    
    # =================================================================
    # DECK ANALYSIS
    # =================================================================
    print_section("DECK ANALYSIS")
    
    deck_info = dreamborn_parser.get_deck_info()
    print(f"Deck total cards: {deck_info.total_cards}")
    print(f"Deck unique cards: {deck_info.unique_cards}")
    
    # Get full card information for deck cards
    deck_card_ids = dreamborn_parser.get_unique_card_ids()
    deck_cards = lorcana_parser.get_cards_by_ids(deck_card_ids)
    
    print(f"\nDeck composition:")
    deck_summary = dreamborn_parser.get_deck_summary()
    for card_name, quantity in deck_summary['cards_by_quantity'].items():
        print(f"  {quantity}x {card_name}")
    
    # Analyze deck colors
    deck_colors = {}
    for card in deck_cards:
        color = card.get('color', 'Unknown')
        deck_colors[color] = deck_colors.get(color, 0) + 1
    
    print(f"\nDeck colors:")
    for color, count in sorted(deck_colors.items()):
        print(f"  {color}: {count} cards")
    
    # Validate deck
    issues = dreamborn_parser.validate_deck_format()
    if issues:
        print(f"\nDeck validation issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\nDeck is valid!")
    
    # =================================================================
    # DATA VALIDATION
    # =================================================================
    print_section("DATA VALIDATION")
    
    validation_issues = lorcana_parser.validate_data_completeness()
    
    print(f"Cards with missing required fields: {len(validation_issues['missing_required_fields'])}")
    print(f"Cards with no abilities: {len(validation_issues['cards_with_no_abilities'])}")
    print(f"Cards with unusual stats: {len(validation_issues['cards_with_unusual_stats'])}")
    
    if validation_issues['unknown_ability_types']:
        print(f"Unknown ability types found: {validation_issues['unknown_ability_types']}")
    
    if validation_issues['unknown_card_types']:
        print(f"Unknown card types found: {validation_issues['unknown_card_types']}")
    
    # =================================================================
    # IMPLEMENTATION CHECKLIST
    # =================================================================
    print_section("IMPLEMENTATION CHECKLIST")
    
    print("Required Card Types to Implement:")
    for card_type in lorcana_parser.get_unique_card_types():
        count = len(lorcana_parser.find_cards_by_type(card_type))
        print(f"  ✓ {card_type} ({count} cards)")
    
    print(f"\nRequired Ability Types to Implement:")
    for ability_type in lorcana_parser.get_unique_ability_types():
        count = ability_stats.abilities_by_type.get(ability_type, 0)
        print(f"  ✓ {ability_type} ({count} abilities)")
    
    print(f"\nRequired Keywords to Implement:")
    for keyword in lorcana_parser.get_unique_keywords():
        count = ability_stats.keyword_abilities.get(keyword, 0)
        print(f"  ✓ {keyword} ({count} occurrences)")
    
    print(f"\nRequired Colors to Implement:")
    for color in lorcana_parser.get_unique_colors():
        count = card_stats.cards_by_color.get(color, 0)
        print(f"  ✓ {color} ({count} cards)")
    
    print(f"\nRequired Rarities to Implement:")
    for rarity in lorcana_parser.get_unique_rarities():
        count = card_stats.cards_by_rarity.get(rarity, 0)
        print(f"  ✓ {rarity} ({count} cards)")
    
    print_section("ANALYSIS COMPLETE")
    print("This enumeration provides a comprehensive view of all components")
    print("that need to be implemented in the Card model.")
    print(f"\nNext steps:")
    print("1. Implement base Card class with all identified fields")
    print("2. Create specialized classes for each card type")
    print("3. Implement ability system with all ability types")
    print("4. Add keyword ability handlers")
    print("5. Create comprehensive tests based on this enumeration")


if __name__ == "__main__":
    main()