"""Tests for deck builder utility."""

import pytest
from pathlib import Path

from lorcana_sim.utils.deck_builder import DeckBuilder
from lorcana_sim.models.cards.base_card import CardColor
from lorcana_sim.loaders.lorcana_json_parser import LorcanaJsonParser


@pytest.fixture
def deck_builder():
    """Create a deck builder with real card data."""
    data_path = Path("data/all-cards/allCards.json")
    if not data_path.exists():
        pytest.skip("Card database not found")
    
    parser = LorcanaJsonParser(str(data_path))
    return DeckBuilder(parser.cards)


def test_deck_builder_initialization(deck_builder):
    """Test deck builder initialization and caching."""
    # Test basic properties
    assert len(deck_builder.cards) > 0
    assert len(deck_builder.cards_by_color) > 0
    assert len(deck_builder.cards_by_cost) > 0
    assert len(deck_builder.cards_by_type) > 0
    
    # Test caching (accessing again should use cache)
    cards1 = deck_builder.cards
    cards2 = deck_builder.cards
    assert cards1 is cards2  # Should be same object (cached)


def test_deck_builder_statistics(deck_builder):
    """Test deck builder statistics."""
    stats = deck_builder.get_statistics()
    
    assert "total_cards" in stats
    assert "by_color" in stats
    assert "by_type" in stats
    assert "by_cost" in stats
    assert "cost_range" in stats
    
    assert stats["total_cards"] > 0
    assert len(stats["by_color"]) > 0
    assert len(stats["by_type"]) > 0
    assert len(stats["by_cost"]) > 0
    
    print(f"Database contains {stats['total_cards']} cards")
    print(f"Colors: {list(stats['by_color'].keys())}")
    print(f"Types: {list(stats['by_type'].keys())}")
    print(f"Cost range: {stats['cost_range']}")


def test_build_random_deck(deck_builder):
    """Test building a random deck."""
    deck = deck_builder.build_random_deck("Test Random", seed=42)
    
    assert deck is not None
    assert deck.name == "Test Random"
    assert deck.total_cards == 60
    assert deck.unique_cards == 15
    
    legal, errors = deck.is_legal()
    assert legal is True
    assert len(errors) == 0
    
    print(f"Random deck: {deck.get_summary()}")


def test_build_mono_color_decks(deck_builder):
    """Test building mono-color decks."""
    colors_to_test = [CardColor.AMBER, CardColor.RUBY, CardColor.SAPPHIRE]
    
    successful_decks = 0
    
    for color in colors_to_test:
        deck = deck_builder.build_mono_color_deck(color, seed=42)
        
        if deck is not None:
            successful_decks += 1
            
            assert deck.total_cards == 60
            legal, errors = deck.is_legal()
            assert legal is True
            
            # Check that primary color dominates
            color_dist = deck.get_color_distribution()
            primary_count = color_dist.get(color.value, 0)
            assert primary_count > deck.total_cards * 0.8  # At least 80% primary color
            
            print(f"{color.value} deck: {primary_count}/{deck.total_cards} cards")
    
    assert successful_decks >= 2, f"Only created {successful_decks} mono-color decks"


def test_build_aggro_deck(deck_builder):
    """Test building an aggro deck."""
    deck = deck_builder.build_aggro_deck(CardColor.RUBY, seed=42)
    
    if deck is None:
        pytest.skip("Could not build aggro deck with available cards")
    
    assert deck.total_cards <= 60
    assert deck.unique_cards > 0
    
    legal, errors = deck.is_legal()
    assert legal is True
    
    # Check that cost curve favors low-cost cards
    cost_curve = deck.get_cost_curve()
    low_cost_cards = sum(count for cost, count in cost_curve.items() if cost <= 3)
    total_cards = deck.total_cards
    
    assert low_cost_cards > total_cards * 0.4  # At least 40% low-cost
    
    print(f"Aggro deck cost curve: {cost_curve}")
    print(f"Low-cost cards: {low_cost_cards}/{total_cards}")


def test_build_control_deck(deck_builder):
    """Test building a control deck."""
    deck = deck_builder.build_control_deck(CardColor.SAPPHIRE, seed=42)
    
    if deck is None:
        pytest.skip("Could not build control deck with available cards")
    
    assert deck.total_cards <= 60
    legal, errors = deck.is_legal()
    assert legal is True
    
    # Check that cost curve includes higher-cost cards
    cost_curve = deck.get_cost_curve()
    high_cost_cards = sum(count for cost, count in cost_curve.items() if cost >= 5)
    total_cards = deck.total_cards
    
    assert high_cost_cards > total_cards * 0.2  # At least 20% high-cost
    
    print(f"Control deck cost curve: {cost_curve}")
    print(f"High-cost cards: {high_cost_cards}/{total_cards}")


def test_build_tribal_deck(deck_builder):
    """Test building a tribal deck."""
    # Try some common subtypes
    subtypes_to_test = ["Hero", "Villain", "Princess", "Storyborn"]
    
    successful_decks = 0
    
    for subtype in subtypes_to_test:
        deck = deck_builder.build_character_tribal_deck(subtype, seed=42)
        
        if deck is not None:
            successful_decks += 1
            
            assert deck.total_cards <= 60
            assert deck.unique_cards > 0
            
            legal, errors = deck.is_legal()
            if deck.total_cards == 60:
                assert legal is True
            
            print(f"{subtype} tribal deck: {deck.total_cards} cards, {deck.unique_cards} unique")
            
            # Check that we have characters with the subtype
            type_dist = deck.get_type_distribution()
            character_count = type_dist.get("Character", 0)
            assert character_count > 0
    
    assert successful_decks >= 1, f"Could not create any tribal decks"


def test_build_balanced_deck(deck_builder):
    """Test building a balanced deck."""
    colors = [CardColor.AMBER, CardColor.STEEL]
    deck = deck_builder.build_balanced_deck(colors, seed=42)
    
    if deck is None:
        pytest.skip("Could not build balanced deck with available cards")
    
    assert deck.total_cards <= 60
    legal, errors = deck.is_legal()
    assert legal is True
    
    # Check color distribution
    color_dist = deck.get_color_distribution()
    primary_colors_count = sum(color_dist.get(color.value, 0) for color in colors)
    total_cards = deck.total_cards
    
    assert primary_colors_count > total_cards * 0.7  # Most cards should be primary colors
    
    # Check cost curve is reasonably distributed
    cost_curve = deck.get_cost_curve()
    assert len(cost_curve) >= 3  # Should have cards at multiple cost levels
    
    print(f"Balanced deck colors: {color_dist}")
    print(f"Balanced deck curve: {cost_curve}")


def test_deck_builder_edge_cases(deck_builder):
    """Test edge cases in deck building."""
    # Test with insufficient cards (this might happen with very specific filters)
    # We can't easily test this with the full database, so we'll test the methods exist
    
    # Test that methods handle None gracefully
    empty_builder = DeckBuilder([])  # Empty database
    
    random_deck = empty_builder.build_random_deck()
    assert random_deck is None
    
    mono_deck = empty_builder.build_mono_color_deck(CardColor.AMBER)
    assert mono_deck is None
    
    # Test statistics with empty database
    stats = empty_builder.get_statistics()
    assert stats["total_cards"] == 0


def test_multiple_deck_generation(deck_builder):
    """Test generating multiple different decks."""
    decks = []
    
    # Generate several random decks with different seeds
    for i in range(3):
        deck = deck_builder.build_random_deck(f"Random Deck {i+1}", seed=i)
        if deck:
            decks.append(deck)
    
    # Generate mono-color decks
    for color in [CardColor.AMBER, CardColor.RUBY]:
        deck = deck_builder.build_mono_color_deck(color, seed=42)
        if deck:
            decks.append(deck)
    
    assert len(decks) >= 3, "Should be able to generate multiple different decks"
    
    # Check that decks are actually different
    # Convert nested dict to a hashable format
    def make_hashable(obj):
        if isinstance(obj, dict):
            return frozenset((k, make_hashable(v)) for k, v in obj.items())
        elif isinstance(obj, list):
            return tuple(make_hashable(i) for i in obj)
        else:
            return obj
    
    deck_summaries = [make_hashable(deck.get_summary()) for deck in decks]
    unique_summaries = set(deck_summaries)
    
    assert len(unique_summaries) > 1, "Generated decks should be different from each other"
    
    print(f"Generated {len(decks)} decks, {len(unique_summaries)} unique configurations")