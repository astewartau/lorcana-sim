"""Tests for base card functionality."""

import pytest
from lorcana_sim.models.cards.base_card import Card, CardColor, Rarity
# Old ability system removed


def test_card_creation():
    """Test basic card creation."""
    card = Card(
        id=1,
        name="Test Card",
        version="Test Version",
        full_name="Test Card - Test Version",
        cost=3,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test Story"
    )
    
    assert card.id == 1
    assert card.name == "Test Card"
    assert card.cost == 3
    assert card.color == CardColor.AMBER
    assert card.inkwell is True
    assert card.can_be_inked() is True


def test_card_validation():
    """Test card validation."""
    # Negative cost should raise error
    with pytest.raises(ValueError, match="Card cost cannot be negative"):
        Card(
            id=1,
            name="Test Card",
            version=None,
            full_name="Test Card",
            cost=-1,
            color=CardColor.AMBER,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=1,
            story="Test Story"
        )
    
    # Empty name should raise error
    with pytest.raises(ValueError, match="Card name cannot be empty"):
        Card(
            id=1,
            name="",
            version=None,
            full_name="Test Card",
            cost=3,
            color=CardColor.AMBER,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=1,
            story="Test Story"
        )


def test_card_full_name_generation():
    """Test automatic full name generation."""
    # With version
    card1 = Card(
        id=1,
        name="Mickey Mouse",
        version="Brave Little Tailor",
        full_name="",  # Empty - should be auto-generated
        cost=3,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Mickey Mouse"
    )
    assert card1.full_name == "Mickey Mouse - Brave Little Tailor"
    
    # Without version
    card2 = Card(
        id=2,
        name="Test Action",
        version=None,
        full_name="",  # Empty - should be auto-generated
        cost=2,
        color=CardColor.RUBY,
        inkwell=False,
        rarity=Rarity.RARE,
        set_code="TEST",
        number=2,
        story="Test Story"
    )
    assert card2.full_name == "Test Action"


def test_card_type_property():
    """Test card type property."""
    card = Card(
        id=1,
        name="Test Card",
        version=None,
        full_name="Test Card",
        cost=3,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test Story"
    )
    
    # Base Card class should return "Card"
    assert card.card_type == "Card"


def test_card_string_representations():
    """Test string representations of cards."""
    card = Card(
        id=1,
        name="Test Card",
        version="Test Version",
        full_name="Test Card - Test Version",
        cost=3,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test Story"
    )
    
    assert str(card) == "Test Card - Test Version"
    assert repr(card) == "Card(id=1, name='Test Card - Test Version', cost=3)"


def test_card_enums():
    """Test card enums."""
    # Test all card colors
    assert CardColor.AMBER.value == "Amber"
    assert CardColor.AMETHYST.value == "Amethyst"
    assert CardColor.EMERALD.value == "Emerald"
    assert CardColor.RUBY.value == "Ruby"
    assert CardColor.SAPPHIRE.value == "Sapphire"
    assert CardColor.STEEL.value == "Steel"
    
    # Test all rarities
    assert Rarity.COMMON.value == "Common"
    assert Rarity.UNCOMMON.value == "Uncommon"
    assert Rarity.RARE.value == "Rare"
    assert Rarity.SUPER_RARE.value == "Super Rare"
    assert Rarity.LEGENDARY.value == "Legendary"
    assert Rarity.SPECIAL.value == "Special"
    assert Rarity.ENCHANTED.value == "Enchanted"