"""Tests for card factory functionality."""

import pytest
from lorcana_sim.models.cards.card_factory import CardFactory
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.action_card import ActionCard
from lorcana_sim.models.cards.item_card import ItemCard
from lorcana_sim.models.cards.location_card import LocationCard
# Old ability system removed - abilities now handled by new framework


def test_create_character_from_json():
    """Test creating a character card from JSON data."""
    card_data = {
        "id": 1,
        "name": "Mickey Mouse",
        "version": "Brave Little Tailor",
        "fullName": "Mickey Mouse - Brave Little Tailor",
        "type": "Character",
        "cost": 3,
        "color": "Amber",
        "inkwell": True,
        "rarity": "Common",
        "setCode": "TFC",
        "number": 1,
        "story": "Mickey Mouse",
        "strength": 3,
        "willpower": 3,
        "lore": 2,
        "subtypes": ["Hero", "Storyborn"],
        "abilities": [
            {
                "type": "keyword",
                "name": "Evasive",
                "keyword": "Evasive",
                "effect": "Only characters with Evasive can challenge this character.",
                "fullText": "Evasive (Only characters with Evasive can challenge this character.)"
            }
        ],
        "flavorText": "Even the smallest mouse can be a giant.",
        "fullText": "Evasive (Only characters with Evasive can challenge this character.)",
        "artists": ["Artist Name"]
    }
    
    card = CardFactory.from_json(card_data)
    
    assert isinstance(card, CharacterCard)
    assert card.id == 1
    assert card.name == "Mickey Mouse"
    assert card.version == "Brave Little Tailor"
    assert card.full_name == "Mickey Mouse - Brave Little Tailor"
    assert card.cost == 3
    assert card.color == CardColor.AMBER
    assert card.inkwell is True
    assert card.rarity == Rarity.COMMON
    assert card.set_code == "TFC"
    assert card.number == 1
    assert card.story == "Mickey Mouse"
    assert card.strength == 3
    assert card.willpower == 3
    assert card.lore == 2
    assert card.subtypes == ["Hero", "Storyborn"]
    assert card.flavor_text == "Even the smallest mouse can be a giant."
    assert card.artists == ["Artist Name"]
    
    # Check abilities - now returns empty list with new framework stub
    assert len(card.abilities) == 0


def test_create_action_from_json():
    """Test creating an action card from JSON data."""
    card_data = {
        "id": 100,
        "name": "Be Prepared",
        "version": None,
        "fullName": "Be Prepared",
        "type": "Action",
        "cost": 2,
        "color": "Emerald",
        "inkwell": True,
        "rarity": "Common",
        "setCode": "TFC",
        "number": 100,
        "story": "The Lion King",
        "abilities": [
            {
                "type": "static",
                "name": "Draw Effect",
                "effect": "Draw 2 cards.",
                "fullText": "Draw 2 cards."
            }
        ],
        "fullText": "Draw 2 cards."
    }
    
    card = CardFactory.from_json(card_data)
    
    assert isinstance(card, ActionCard)
    assert card.id == 100
    assert card.name == "Be Prepared"
    assert card.version is None
    assert card.full_name == "Be Prepared"
    assert card.cost == 2
    assert card.color == CardColor.EMERALD
    assert card.effects == ["Draw 2 cards."]


def test_create_item_from_json():
    """Test creating an item card from JSON data."""
    card_data = {
        "id": 200,
        "name": "Bag of Berries",
        "version": None,
        "fullName": "Bag of Berries",
        "type": "Item",
        "cost": 1,
        "color": "Emerald",
        "inkwell": True,
        "rarity": "Common",
        "setCode": "TFC",
        "number": 200,
        "story": "Snow White",
        "abilities": [],
        "fullText": "Gain 1 lore."
    }
    
    card = CardFactory.from_json(card_data)
    
    assert isinstance(card, ItemCard)
    assert card.id == 200
    assert card.name == "Bag of Berries"
    assert card.cost == 1
    assert card.color == CardColor.EMERALD


def test_create_location_from_json():
    """Test creating a location card from JSON data."""
    card_data = {
        "id": 300,
        "name": "Beast's Castle",
        "version": "Ballroom",
        "fullName": "Beast's Castle - Ballroom",
        "type": "Location",
        "cost": 3,
        "color": "Amber",
        "inkwell": True,
        "rarity": "Uncommon",
        "setCode": "TFC",
        "number": 300,
        "story": "Beauty and the Beast",
        "moveCost": 2,
        "willpower": 5,
        "lore": 1,
        "abilities": [],
        "fullText": "Characters at this location get +1 lore."
    }
    
    card = CardFactory.from_json(card_data)
    
    assert isinstance(card, LocationCard)
    assert card.id == 300
    assert card.name == "Beast's Castle"
    assert card.version == "Ballroom"
    assert card.move_cost == 2
    assert card.willpower == 5
    assert card.lore == 1


def test_unknown_card_type():
    """Test handling of unknown card types."""
    card_data = {
        "id": 999,
        "name": "Unknown Card",
        "fullName": "Unknown Card",
        "type": "Unknown",
        "cost": 1,
        "color": "Amber",
        "inkwell": True,
        "rarity": "Common",
        "setCode": "TEST",
        "number": 999,
        "story": "Test"
    }
    
    with pytest.raises(ValueError, match="Unknown card type: Unknown"):
        CardFactory.from_json(card_data)


def test_multi_color_card():
    """Test handling of multi-color cards."""
    card_data = {
        "id": 400,
        "name": "Multi Color",
        "fullName": "Multi Color",
        "type": "Character",
        "cost": 5,
        "color": "Amber-Steel",  # Multi-color
        "inkwell": True,
        "rarity": "Rare",
        "setCode": "TEST",
        "number": 400,
        "story": "Test",
        "strength": 4,
        "willpower": 4,
        "lore": 2,
        "abilities": []
    }
    
    card = CardFactory.from_json(card_data)
    
    # Should parse as the first color (Amber)
    assert card.color == CardColor.AMBER


def test_unknown_color():
    """Test handling of unknown colors."""
    card_data = {
        "id": 500,
        "name": "Unknown Color",
        "fullName": "Unknown Color",
        "type": "Character",
        "cost": 3,
        "color": "Purple",  # Unknown color
        "inkwell": True,
        "rarity": "Common",
        "setCode": "TEST",
        "number": 500,
        "story": "Test",
        "strength": 3,
        "willpower": 3,
        "lore": 2,
        "abilities": []
    }
    
    with pytest.raises(ValueError, match="Unknown card color: Purple"):
        CardFactory.from_json(card_data)


def test_missing_required_fields():
    """Test handling of missing required fields."""
    card_data = {
        "id": 600,
        "name": "Incomplete Card",
        # Missing required fields like cost, color, etc.
        "type": "Character"
    }
    
    with pytest.raises((KeyError, ValueError)):
        CardFactory.from_json(card_data)


def test_create_cards_from_database():
    """Test creating multiple cards from a database."""
    database = [
        {
            "id": 1,
            "name": "Card 1",
            "fullName": "Card 1",
            "type": "Character",
            "cost": 3,
            "color": "Amber",
            "inkwell": True,
            "rarity": "Common",
            "setCode": "TEST",
            "number": 1,
            "story": "Test",
            "strength": 3,
            "willpower": 3,
            "lore": 2,
            "abilities": []
        },
        {
            "id": 2,
            "name": "Card 2",
            "fullName": "Card 2",
            "type": "Action",
            "cost": 2,
            "color": "Ruby",
            "inkwell": True,
            "rarity": "Common",
            "setCode": "TEST",
            "number": 2,
            "story": "Test",
            "abilities": []
        },
        {
            # Invalid card - missing required fields
            "id": 3,
            "name": "Invalid Card",
            "type": "Character"
        }
    ]
    
    cards = CardFactory.create_cards_from_database(database)
    
    # Should create 2 valid cards and skip the invalid one
    assert len(cards) == 2
    assert cards[0].name == "Card 1"
    assert cards[1].name == "Card 2"

# Removed keyword ability tests - old ability system removed

