#!/usr/bin/env python3
"""
Simple deck builder demo for Lorcana simulation.
Builds a deck and displays complete contents with analysis.
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict

from lorcana_sim.utils.deck_builder import DeckBuilder
from lorcana_sim.models.cards.base_card import CardColor
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.loaders.lorcana_json_parser import LorcanaJsonParser


def print_section(title: str, separator: str = "=") -> None:
    """Print a formatted section header"""
    print(f"\n{separator * 60}")
    print(f" {title}")
    print(f"{separator * 60}")


def print_subsection(title: str) -> None:
    """Print a formatted subsection header"""
    print(f"\n{title}")
    print("-" * len(title))


def build_random_color_deck(builder):
    """Build a deck with two randomly selected colors."""
    import random
    
    # Get all available colors
    all_colors = list(CardColor)
    
    # Randomly select two colors
    selected_colors = random.sample(all_colors, 2)
    
    # Create deck name
    color_names = "-".join([color.value for color in selected_colors])
    deck_name = f"{color_names} Deck"
    
    print(f"Building {deck_name}...")
    
    # Build balanced deck with the selected colors
    return builder.build_balanced_deck(selected_colors, deck_name)


def analyze_deck(deck):
    """Perform comprehensive deck analysis using our models."""
    
    print_section("DECK OVERVIEW")
    print(f"Deck Name: {deck.name}")
    print(f"Total Cards: {deck.total_cards}")
    print(f"Unique Cards: {deck.unique_cards}")
    
    # Validate deck legality
    legal, issues = deck.is_legal()
    if issues:
        print(f"\nDeck Issues:")
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print(f"\n✅ Deck is legal!")
    
    # Complete deck listing
    print_section("COMPLETE DECK LISTING")
    
    # Get all cards with quantities
    for deck_card in sorted(deck.cards, key=lambda x: (x.card.cost, x.card.full_name)):
        card = deck_card.card
        quantity = deck_card.quantity
        
        # Format based on card type
        if isinstance(card, CharacterCard):
            print(f"{quantity}x {card.full_name} ({card.cost}) - {card.strength}⚔️/{card.willpower}❤️, {card.lore}◊")
        else:
            print(f"{quantity}x {card.full_name} ({card.cost}) - {card.card_type}")
        
        # Show abilities if any
        if card.abilities:
            for ability in card.abilities:
                ability_text = ability.full_text if ability.full_text else ability.effect
                if ability_text:
                    # Truncate long ability text
                    if len(ability_text) > 80:
                        ability_text = ability_text[:77] + "..."
                    print(f"    → {ability_text}")
    
    # Expand to full card list for analysis
    all_cards = []
    for deck_card in deck.cards:
        for _ in range(deck_card.quantity):
            all_cards.append(deck_card.card)
    
    # Color Analysis
    print_section("COLOR COMPOSITION")
    color_counts = Counter()
    color_card_names = defaultdict(list)
    
    for card in all_cards:
        color = card.color.value
        color_counts[color] += 1
        color_card_names[color].append(card.full_name)
    
    for color, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck.total_cards) * 100
        print(f"\n{color}: {count} cards ({percentage:.1f}%)")
        # Show unique cards in this color
        unique_cards = set(color_card_names[color])
        for card_name in sorted(unique_cards):
            count_in_deck = color_card_names[color].count(card_name)
            print(f"  • {count_in_deck}x {card_name}")
    
    # Story/Franchise Analysis
    print_section("FRANCHISE REPRESENTATION")
    story_counts = Counter()
    story_cards = defaultdict(list)
    
    for card in all_cards:
        story = card.story
        if story:
            story_counts[story] += 1
            story_cards[story].append(card.full_name)
    
    for story, count in sorted(story_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck.total_cards) * 100
        print(f"\n{story}: {count} cards ({percentage:.1f}%)")
        unique_cards = set(story_cards[story])
        for card_name in sorted(unique_cards):
            count_in_deck = story_cards[story].count(card_name)
            print(f"  • {count_in_deck}x {card_name}")
    
    # Card Type Distribution
    print_section("CARD TYPE DISTRIBUTION")
    type_counts = Counter()
    type_details = defaultdict(list)
    
    for card in all_cards:
        card_type = card.card_type
        type_counts[card_type] += 1
        type_details[card_type].append(card)
    
    for card_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck.total_cards) * 100
        print(f"\n{card_type}: {count} cards ({percentage:.1f}%)")
        
        if card_type == 'Character':
            # Show character stats distribution
            characters = [c for c in type_details[card_type] if isinstance(c, CharacterCard)]
            if characters:
                strength_dist = Counter(c.strength for c in characters)
                willpower_dist = Counter(c.willpower for c in characters)
                lore_dist = Counter(c.lore for c in characters)
                
                print(f"  Strength distribution: {dict(sorted(strength_dist.items()))}")
                print(f"  Willpower distribution: {dict(sorted(willpower_dist.items()))}")
                print(f"  Lore value distribution: {dict(sorted(lore_dist.items()))}")
    
    # Mana Curve Analysis
    print_section("MANA CURVE")
    cost_distribution = Counter()
    cost_by_type = defaultdict(lambda: defaultdict(int))
    
    for card in all_cards:
        cost = card.cost
        card_type = card.card_type
        cost_distribution[cost] += 1
        cost_by_type[cost][card_type] += 1
    
    print("\nOverall Mana Curve:")
    max_count = max(cost_distribution.values()) if cost_distribution else 1
    for cost in sorted(cost_distribution.keys()):
        count = cost_distribution[cost]
        # Create visual bar proportional to count
        bar_length = int((count / max_count) * 20)
        bar = "█" * bar_length
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
    
    for card in all_cards:
        for ability in card.abilities:
            if ability.type.value == 'keyword':
                keyword_name = getattr(ability, 'keyword', ability.name)
                if keyword_name:
                    keyword_counts[keyword_name] += 1
                    keyword_cards[keyword_name].append(card.full_name)
    
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
    unique_abilities = {}
    
    for card in all_cards:
        for ability in card.abilities:
            ability_type = ability.type.value
            ability_types[ability_type] += 1
            
            if ability_type != 'keyword':
                # Create a unique key for each ability
                ability_name = ability.name
                ability_effect = ability.full_text if ability.full_text else ability.effect
                card_name = card.full_name
                
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
    for ability_type in ['triggered', 'activated', 'static']:
        type_abilities = [a for a in unique_abilities.values() if a['type'] == ability_type]
        if type_abilities:
            print(f"\n{ability_type.capitalize()} Abilities ({len(type_abilities)} unique):")
            sorted_abilities = sorted(type_abilities, key=lambda x: (-x['count'], x['card']))
            for ability in sorted_abilities:
                count_str = f" (x{ability['count']})" if ability['count'] > 1 else ""
                if ability['name']:
                    print(f"  • {ability['card']} - {ability['name']}{count_str}")
                    if ability['effect']:
                        effect = ability['effect'][:100] + "..." if len(ability['effect']) > 100 else ability['effect']
                        print(f"    → {effect}")
    
    # Rarity Distribution
    print_section("RARITY DISTRIBUTION")
    rarity_counts = Counter()
    rarity_cards = defaultdict(list)
    
    for card in all_cards:
        rarity = card.rarity.value
        rarity_counts[rarity] += 1
        rarity_cards[rarity].append(card.full_name)
    
    for rarity, count in sorted(rarity_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / deck.total_cards) * 100
        print(f"\n{rarity}: {count} cards ({percentage:.1f}%)")
        unique_cards = set(rarity_cards[rarity])
        for card_name in sorted(unique_cards):
            count_in_deck = rarity_cards[rarity].count(card_name)
            print(f"  • {count_in_deck}x {card_name}")
    
    # Inkwell Analysis
    print_section("INKWELL ANALYSIS")
    inkable_count = sum(1 for card in all_cards if card.can_be_inked())
    non_inkable_count = deck.total_cards - inkable_count
    inkable_percentage = (inkable_count / deck.total_cards) * 100
    
    print(f"Inkable cards: {inkable_count} ({inkable_percentage:.1f}%)")
    print(f"Non-inkable cards: {non_inkable_count} ({100 - inkable_percentage:.1f}%)")
    
    # Character Subtypes
    print_section("CHARACTER SUBTYPES")
    subtype_counts = Counter()
    
    for card in all_cards:
        if isinstance(card, CharacterCard):
            for subtype in card.subtypes:
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
    main_franchises = [story for story, count in story_counts.most_common(3)]
    print(f"Main Franchises: {', '.join(main_franchises)}")
    
    # Average stats for characters
    character_cards = [c for c in all_cards if isinstance(c, CharacterCard)]
    if character_cards:
        avg_cost = sum(c.cost for c in character_cards) / len(character_cards)
        avg_strength = sum(c.strength for c in character_cards) / len(character_cards)
        avg_willpower = sum(c.willpower for c in character_cards) / len(character_cards)
        avg_lore = sum(c.lore for c in character_cards) / len(character_cards)
        
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
    print("Lorcana Deck Builder & Analyzer")
    print("=" * 40)
    
    # Load card database
    card_db_path = Path("data/all-cards/allCards.json")
    if not card_db_path.exists():
        print(f"Error: Card database not found at {card_db_path}")
        return
    
    print("Loading card database...")
    parser = LorcanaJsonParser(str(card_db_path))
    builder = DeckBuilder(parser.cards)
    stats = builder.get_statistics()
    print(f"✅ Loaded {stats['total_cards']} cards")
    
    # Build deck with random colors
    deck = build_random_color_deck(builder)
    
    if not deck:
        print("Error: Could not build deck")
        return
    
    print(f"✅ Built deck: {deck.name}")
    
    # Analyze the deck
    analyze_deck(deck)


if __name__ == "__main__":
    main()
