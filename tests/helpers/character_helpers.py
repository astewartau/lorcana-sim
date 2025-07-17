"""Helper functions for creating test characters and abilities."""

from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.action_card import ActionCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.models.abilities.composable.named_abilities import NamedAbilityRegistry
from src.lorcana_sim.models.abilities.composable.keyword_abilities import create_singer_ability


def create_test_character(
    name,
    cost=3,
    color=CardColor.AMBER,
    strength=2,
    willpower=3,
    lore=1,
    abilities=None,
    inkwell=True,
    rarity=Rarity.COMMON,
    card_id=None
):
    """Create a test character with sensible defaults.
    
    Args:
        name: Full character name (e.g., "Ariel - On Human Legs")
        cost: Ink cost to play the character
        color: Card color (from CardColor enum)
        strength: Character's strength value
        willpower: Character's willpower value
        lore: Lore value when questing
        abilities: List of ability names to add (optional)
        inkwell: Whether the card can be put in inkwell
        rarity: Card rarity (from Rarity enum)
        card_id: Unique card ID (auto-generated if not provided)
    
    Returns:
        CharacterCard instance with the specified attributes
    """
    # Extract name and version from full name
    if " - " in name:
        char_name, version = name.split(" - ", 1)
    else:
        char_name = name
        version = "Test"
    
    # Auto-generate ID if not provided
    if card_id is None:
        import random
        card_id = random.randint(1000, 9999)
    
    character = CharacterCard(
        id=card_id,
        name=char_name,
        version=version,
        full_name=name,
        cost=cost,
        color=color,
        inkwell=inkwell,
        rarity=rarity,
        set_code="1",
        number=1,
        story="Test",
        strength=strength,
        willpower=willpower,
        lore=lore
    )
    
    return character


def add_named_ability(character, ability_name, ability_type="static", event_manager=None):
    """Add a named ability to a character.
    
    Args:
        character: The character to add the ability to
        ability_name: Name of the ability (e.g., "VOICELESS", "LOYAL")
        ability_type: Type of ability ("static", "triggered", "activated")
        event_manager: Optional event manager to register the ability with
    
    Returns:
        The created ability instance
    """
    ability_data = {"name": ability_name, "type": ability_type}
    ability = NamedAbilityRegistry.create_ability(ability_name, character, ability_data)
    
    if ability is None:
        # Create a mock ability for testing purposes
        from src.lorcana_sim.models.abilities.composable.composable_ability import ComposableAbility
        ability = ComposableAbility(ability_name, character)
    
    if not character.composable_abilities:
        character.composable_abilities = []
    
    character.composable_abilities.append(ability)
    
    if event_manager and ability:
        character.register_composable_abilities(event_manager)
    
    return ability


def create_test_action_card(
    name,
    cost=3,
    color=CardColor.AMBER,
    card_type="Action",
    inkwell=True,
    rarity=Rarity.COMMON,
    card_id=None
):
    """Create a test action card (including songs) with sensible defaults.
    
    Args:
        name: Card name
        cost: Ink cost to play the card
        color: Card color (from CardColor enum)
        card_type: Type of action card (e.g., "Action", "Song")
        inkwell: Whether the card can be put in inkwell
        rarity: Card rarity (from Rarity enum)
        card_id: Unique card ID (auto-generated if not provided)
    
    Returns:
        ActionCard instance with the specified attributes
    """
    if card_id is None:
        import random
        card_id = random.randint(1000, 9999)
    
    action = ActionCard(
        id=card_id,
        name=name,
        version="",
        full_name=name,
        cost=cost,
        color=color,
        inkwell=inkwell,
        rarity=rarity,
        set_code="1",
        number=1,
        story="Test"
    )
    
    return action


def add_singer_ability(character, singer_cost, event_manager=None):
    """Add a Singer ability to a character.
    
    Args:
        character: The character to add Singer to
        singer_cost: The cost reduction for songs
        event_manager: Optional event manager to register the ability with
    
    Returns:
        The created Singer ability instance
    """
    singer_ability = create_singer_ability(singer_cost, character)
    
    if not character.composable_abilities:
        character.composable_abilities = []
    
    character.composable_abilities.append(singer_ability)
    
    if event_manager:
        character.register_composable_abilities(event_manager)
    
    return singer_ability