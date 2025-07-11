"""Tests for deck functionality."""

import pytest
from lorcana_sim.models.cards.base_card import Card, CardColor, Rarity
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.game.deck import Deck, DeckCard


def create_test_card(card_id: int, name: str, cost: int = 3) -> Card:
    """Helper to create a test card."""
    return Card(
        id=card_id,
        name=name,
        version=None,
        full_name=name,
        cost=cost,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=card_id,
        story="Test Story"
    )


def test_deck_creation():
    """Test basic deck creation."""
    deck = Deck("Test Deck")
    
    assert deck.name == "Test Deck"
    assert deck.total_cards == 0
    assert deck.unique_cards == 0
    assert len(deck.cards) == 0


def test_deck_card_validation():
    """Test deck card validation."""
    card = create_test_card(1, "Test Card")
    
    # Valid deck card
    deck_card = DeckCard(card=card, quantity=4)
    assert deck_card.card == card
    assert deck_card.quantity == 4
    
    # Invalid quantity (zero)
    with pytest.raises(ValueError, match="Card quantity must be positive"):
        DeckCard(card=card, quantity=0)
    
    # Invalid quantity (negative)
    with pytest.raises(ValueError, match="Card quantity must be positive"):
        DeckCard(card=card, quantity=-1)
    
    # Invalid quantity (too many)
    with pytest.raises(ValueError, match="Cannot have more than 4 copies"):
        DeckCard(card=card, quantity=5)


def test_deck_add_cards():
    """Test adding cards to deck."""
    deck = Deck("Test Deck")
    card1 = create_test_card(1, "Card 1")
    card2 = create_test_card(2, "Card 2")
    
    # Add first card
    deck.add_card(card1, 2)
    assert deck.total_cards == 2
    assert deck.unique_cards == 1
    
    # Add second card
    deck.add_card(card2, 3)
    assert deck.total_cards == 5
    assert deck.unique_cards == 2
    
    # Add more of first card
    deck.add_card(card1, 1)
    assert deck.total_cards == 6
    assert deck.unique_cards == 2
    
    # Check that first card has 3 copies now
    found_card = deck.find_card(1)
    assert found_card is not None
    assert found_card.quantity == 3
    
    # Try to add too many copies
    with pytest.raises(ValueError, match="would exceed 4 copy limit"):
        deck.add_card(card1, 2)


def test_deck_remove_cards():
    """Test removing cards from deck."""
    deck = Deck("Test Deck")
    card = create_test_card(1, "Test Card")
    
    # Add card
    deck.add_card(card, 3)
    assert deck.total_cards == 3
    
    # Remove some copies
    removed = deck.remove_card(1, 1)
    assert removed is True
    assert deck.total_cards == 2
    
    # Remove remaining copies
    removed = deck.remove_card(1, 2)
    assert removed is True
    assert deck.total_cards == 0
    assert deck.unique_cards == 0
    
    # Try to remove non-existent card
    removed = deck.remove_card(999, 1)
    assert removed is False


def test_deck_legality():
    """Test deck legality checking."""
    deck = Deck("Test Deck")
    
    # Empty deck is not legal
    legal, errors = deck.is_legal()
    assert legal is False
    assert "Deck must have 60 cards" in errors[0]
    
    # Add exactly 60 cards (15 unique cards × 4 copies)
    for i in range(15):
        card = create_test_card(i + 1, f"Card {i + 1}")
        deck.add_card(card, 4)
    
    legal, errors = deck.is_legal()
    assert legal is True
    assert len(errors) == 0
    
    # Add one more card to make it 61
    extra_card = create_test_card(16, "Extra Card")
    deck.add_card(extra_card, 1)
    
    legal, errors = deck.is_legal()
    assert legal is False
    assert "Deck must have 60 cards, has 61" in errors[0]


def test_deck_shuffle():
    """Test deck shuffling."""
    deck = Deck("Test Deck")
    
    # Add some cards
    for i in range(5):
        card = create_test_card(i + 1, f"Card {i + 1}")
        deck.add_card(card, 3)
    
    # Shuffle multiple times and check we get different orders
    shuffle1 = deck.shuffle()
    shuffle2 = deck.shuffle()
    
    assert len(shuffle1) == 15  # 5 cards × 3 copies
    assert len(shuffle2) == 15
    
    # Should contain the same cards
    assert sorted([c.id for c in shuffle1]) == sorted([c.id for c in shuffle2])
    
    # Orders might be different (though could be same by chance)
    card_ids1 = [c.id for c in shuffle1]
    card_ids2 = [c.id for c in shuffle2]
    
    # At least verify we get the right total of each card
    from collections import Counter
    count1 = Counter(card_ids1)
    count2 = Counter(card_ids2)
    assert count1 == count2
    
    for card_id in range(1, 6):
        assert count1[card_id] == 3


def test_deck_distributions():
    """Test deck distribution calculations."""
    deck = Deck("Test Deck")
    
    # Add cards with different colors and costs
    card1 = Card(
        id=1, name="Amber Card", version=None, full_name="Amber Card",
        cost=1, color=CardColor.AMBER, inkwell=True,
        rarity=Rarity.COMMON, set_code="TEST", number=1, story="Test"
    )
    card2 = Card(
        id=2, name="Ruby Card", version=None, full_name="Ruby Card",
        cost=3, color=CardColor.RUBY, inkwell=True,
        rarity=Rarity.COMMON, set_code="TEST", number=2, story="Test"
    )
    card3 = CharacterCard(
        id=3, name="Character", version=None, full_name="Character",
        cost=5, color=CardColor.STEEL, inkwell=True,
        rarity=Rarity.COMMON, set_code="TEST", number=3, story="Test",
        strength=4, willpower=4, lore=2
    )
    
    deck.add_card(card1, 4)  # 4 Amber, cost 1
    deck.add_card(card2, 3)  # 3 Ruby, cost 3
    deck.add_card(card3, 2)  # 2 Steel, cost 5, Character
    
    # Test color distribution
    color_dist = deck.get_color_distribution()
    assert color_dist["Amber"] == 4
    assert color_dist["Ruby"] == 3
    assert color_dist["Steel"] == 2
    
    # Test cost curve
    cost_curve = deck.get_cost_curve()
    assert cost_curve[1] == 4
    assert cost_curve[3] == 3
    assert cost_curve[5] == 2
    
    # Test type distribution
    type_dist = deck.get_type_distribution()
    assert type_dist["Card"] == 7  # card1 and card2
    assert type_dist["Character"] == 2  # card3


def test_deck_summary():
    """Test deck summary generation."""
    deck = Deck("Test Deck")
    
    # Add a few cards
    for i in range(3):
        card = create_test_card(i + 1, f"Card {i + 1}", cost=i + 1)
        deck.add_card(card, i + 2)  # 2, 3, 4 copies respectively
    
    summary = deck.get_summary()
    
    assert summary["name"] == "Test Deck"
    assert summary["total_cards"] == 9  # 2 + 3 + 4
    assert summary["unique_cards"] == 3
    assert summary["color_distribution"]["Amber"] == 9  # All amber
    assert 1 in summary["cost_curve"]
    assert 2 in summary["cost_curve"]
    assert 3 in summary["cost_curve"]


def test_deck_string_representation():
    """Test deck string representation."""
    deck = Deck("My Awesome Deck")
    
    # Empty deck
    assert str(deck) == "Deck 'My Awesome Deck' (0 cards, 0 unique)"
    
    # Add some cards
    card = create_test_card(1, "Test Card")
    deck.add_card(card, 4)
    
    assert str(deck) == "Deck 'My Awesome Deck' (4 cards, 1 unique)"