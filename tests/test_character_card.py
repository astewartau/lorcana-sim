"""Tests for character card functionality."""

import pytest
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity


def test_character_card_creation():
    """Test character card creation."""
    card = CharacterCard(
        id=1,
        name="Mickey Mouse",
        version="Brave Little Tailor",
        full_name="Mickey Mouse - Brave Little Tailor",
        cost=3,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TFC",
        number=1,
        story="Mickey Mouse",
        strength=3,
        willpower=3,
        lore=2,
        subtypes=["Hero", "Storyborn"]
    )
    
    assert card.strength == 3
    assert card.willpower == 3
    assert card.lore == 2
    assert card.subtypes == ["Hero", "Storyborn"]
    assert card.damage == 0
    assert card.exerted is False
    assert card.location is None


def test_character_validation():
    """Test character card validation."""
    # Negative strength
    with pytest.raises(ValueError, match="Character strength cannot be negative"):
        CharacterCard(
            id=1, name="Test", version=None, full_name="Test",
            cost=3, color=CardColor.AMBER, inkwell=True,
            rarity=Rarity.COMMON, set_code="TEST", number=1, story="Test",
            strength=-1, willpower=3, lore=2
        )
    
    # Negative willpower
    with pytest.raises(ValueError, match="Character willpower cannot be negative"):
        CharacterCard(
            id=1, name="Test", version=None, full_name="Test",
            cost=3, color=CardColor.AMBER, inkwell=True,
            rarity=Rarity.COMMON, set_code="TEST", number=1, story="Test",
            strength=3, willpower=-1, lore=2
        )
    
    # Negative lore
    with pytest.raises(ValueError, match="Character lore cannot be negative"):
        CharacterCard(
            id=1, name="Test", version=None, full_name="Test",
            cost=3, color=CardColor.AMBER, inkwell=True,
            rarity=Rarity.COMMON, set_code="TEST", number=1, story="Test",
            strength=3, willpower=3, lore=-1
        )


def test_character_combat_properties():
    """Test character combat-related properties."""
    card = CharacterCard(
        id=1, name="Test Fighter", version=None, full_name="Test Fighter",
        cost=4, color=CardColor.STEEL, inkwell=True,
        rarity=Rarity.COMMON, set_code="TEST", number=1, story="Test",
        strength=4, willpower=5, lore=1
    )
    
    # Initially alive and undamaged
    assert card.is_alive is True
    assert card.current_strength == 4
    assert card.current_willpower == 5
    assert card.current_lore == 1
    
    # Deal damage
    card.deal_damage(3)
    assert card.damage == 3
    assert card.is_alive is True  # 3 damage < 5 willpower
    
    # Deal more damage
    card.deal_damage(2)
    assert card.damage == 5
    assert card.is_alive is False  # 5 damage >= 5 willpower
    
    # Heal damage
    card.heal_damage(2)
    assert card.damage == 3
    assert card.is_alive is True


def test_character_damage_validation():
    """Test damage validation."""
    card = CharacterCard(
        id=1, name="Test", version=None, full_name="Test",
        cost=3, color=CardColor.AMBER, inkwell=True,
        rarity=Rarity.COMMON, set_code="TEST", number=1, story="Test",
        strength=3, willpower=3, lore=2
    )
    
    # Negative damage should raise error
    with pytest.raises(ValueError, match="Damage amount cannot be negative"):
        card.deal_damage(-1)
    
    # Negative heal should raise error
    with pytest.raises(ValueError, match="Heal amount cannot be negative"):
        card.heal_damage(-1)


def test_character_exert_ready():
    """Test character exert/ready mechanics."""
    card = CharacterCard(
        id=1, name="Test", version=None, full_name="Test",
        cost=3, color=CardColor.AMBER, inkwell=True,
        rarity=Rarity.COMMON, set_code="TEST", number=1, story="Test",
        strength=3, willpower=3, lore=2
    )
    
    # Set to dry ink so we can test exert/ready mechanics properly
    card.is_dry = True
    
    # Initially ready
    assert card.exerted is False
    assert card.can_quest(1) is True
    assert card.can_challenge(1) is True
    
    # Exert the character
    card.exert()
    assert card.exerted is True
    assert card.can_quest(1) is False
    assert card.can_challenge(1) is False
    
    # Ready the character
    card.ready()
    assert card.exerted is False
    assert card.can_quest(1) is True
    assert card.can_challenge(1) is True


def test_character_subtypes():
    """Test character subtype functionality."""
    card = CharacterCard(
        id=1, name="Elsa", version="Snow Queen", full_name="Elsa - Snow Queen",
        cost=8, color=CardColor.AMETHYST, inkwell=True,
        rarity=Rarity.LEGENDARY, set_code="TFC", number=1, story="Frozen",
        strength=4, willpower=6, lore=3,
        subtypes=["Hero", "Queen", "Storyborn", "Sorcerer"]
    )
    
    assert card.has_subtype("Hero") is True
    assert card.has_subtype("Queen") is True
    assert card.has_subtype("Storyborn") is True
    assert card.has_subtype("Sorcerer") is True
    assert card.has_subtype("Villain") is False
    
    # Test origin type
    assert card.get_origin_type() == "Storyborn"


def test_character_string_representation():
    """Test character string representation."""
    card = CharacterCard(
        id=1, name="Mickey Mouse", version="Brave Little Tailor",
        full_name="Mickey Mouse - Brave Little Tailor",
        cost=3, color=CardColor.AMBER, inkwell=True,
        rarity=Rarity.COMMON, set_code="TFC", number=1, story="Mickey Mouse",
        strength=3, willpower=3, lore=2
    )
    
    # Normal state
    assert str(card) == "Mickey Mouse - Brave Little Tailor (3/3)"
    
    # Exerted
    card.exert()
    assert str(card) == "Mickey Mouse - Brave Little Tailor (3/3) [EXERTED]"
    
    # Damaged
    card.ready()
    card.deal_damage(1)
    assert str(card) == "Mickey Mouse - Brave Little Tailor (3/3) [1 damage]"
    
    # Both exerted and damaged
    card.exert()
    assert str(card) == "Mickey Mouse - Brave Little Tailor (3/3) [EXERTED] [1 damage]"


def test_character_card_type():
    """Test character card type property."""
    card = CharacterCard(
        id=1, name="Test", version=None, full_name="Test",
        cost=3, color=CardColor.AMBER, inkwell=True,
        rarity=Rarity.COMMON, set_code="TEST", number=1, story="Test",
        strength=3, willpower=3, lore=2
    )
    
    assert card.card_type == "Character"