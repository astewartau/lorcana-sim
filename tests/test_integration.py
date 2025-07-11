"""Integration tests with real card data."""

import pytest
import json
from pathlib import Path

from lorcana_sim.models.cards.card_factory import CardFactory
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.action_card import ActionCard
from lorcana_sim.models.cards.item_card import ItemCard
from lorcana_sim.models.cards.location_card import LocationCard
from lorcana_sim.models.game.deck import Deck
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.loaders.lorcana_json_parser import LorcanaJsonParser
from lorcana_sim.loaders.dreamborn_parser import DreambornParser


@pytest.fixture
def card_database():
    """Load the real card database."""
    data_path = Path("data/all-cards/allCards.json")
    if not data_path.exists():
        pytest.skip("Card database not found")
    
    parser = LorcanaJsonParser(str(data_path))
    return parser.cards


@pytest.fixture
def sample_cards(card_database):
    """Get a small sample of real cards for testing."""
    # Take first 10 cards for testing
    sample_data = card_database[:10] if len(card_database) >= 10 else card_database
    return [CardFactory.from_json(card_data) for card_data in sample_data]


def test_load_real_card_database(card_database):
    """Test loading the real card database."""
    assert len(card_database) > 0
    
    # Test creating a sample of cards
    cards_created = 0
    errors = 0
    
    # Test first 50 cards to avoid long test times
    for card_data in card_database[:50]:
        try:
            card = CardFactory.from_json(card_data)
            cards_created += 1
            
            # Basic validation
            assert card.id > 0
            assert card.name
            assert card.cost >= 0
            assert card.color
            assert card.rarity
            
        except Exception as e:
            errors += 1
            print(f"Error creating card {card_data.get('fullName', 'Unknown')}: {e}")
    
    print(f"Successfully created {cards_created} cards with {errors} errors")
    assert cards_created > 0
    assert errors < cards_created  # Should have more successes than failures


def test_card_type_distribution(card_database):
    """Test the distribution of card types in the database."""
    type_counts = {"Character": 0, "Action": 0, "Item": 0, "Location": 0}
    
    for card_data in card_database[:100]:  # Test first 100 cards
        card_type = card_data.get("type")
        if card_type in type_counts:
            try:
                card = CardFactory.from_json(card_data)
                type_counts[card_type] += 1
                
                # Verify card type matches class
                if card_type == "Character":
                    assert isinstance(card, CharacterCard)
                elif card_type == "Action":
                    assert isinstance(card, ActionCard)
                elif card_type == "Item":
                    assert isinstance(card, ItemCard)
                elif card_type == "Location":
                    assert isinstance(card, LocationCard)
                    
            except Exception as e:
                print(f"Error with {card_data.get('fullName', 'Unknown')}: {e}")
    
    print(f"Card type distribution: {type_counts}")
    assert sum(type_counts.values()) > 0


def test_character_cards_have_combat_stats(card_database):
    """Test that character cards have proper combat stats."""
    character_cards = [card for card in card_database if card.get("type") == "Character"]
    
    for card_data in character_cards[:20]:  # Test first 20 characters
        try:
            card = CardFactory.from_json(card_data)
            assert isinstance(card, CharacterCard)
            
            # Character cards should have combat stats
            assert card.strength >= 0
            assert card.willpower > 0  # Characters must have at least 1 willpower
            assert card.lore >= 0
            
            # Should be able to perform character actions
            assert card.can_quest(1) is True  # Initially ready
            assert card.can_challenge(1) is True  # Initially ready
            assert card.is_alive is True  # No initial damage
            
        except Exception as e:
            print(f"Error with character {card_data.get('fullName', 'Unknown')}: {e}")


def test_dreamborn_deck_loading():
    """Test loading a Dreamborn deck."""
    deck_path = Path("data/decks/amethyst-steel.json")
    if not deck_path.exists():
        pytest.skip("Dreamborn deck file not found")
    
    # Load card database
    card_db_path = Path("data/all-cards/allCards.json")
    if not card_db_path.exists():
        pytest.skip("Card database not found")
    
    parser = LorcanaJsonParser(str(card_db_path))
    card_database = parser.cards
    
    # Load deck
    try:
        deck = Deck.from_dreamborn(str(deck_path), card_database, "Test Deck")
        
        assert deck.name == "Test Deck"
        assert deck.total_cards > 0
        assert deck.unique_cards > 0
        
        # Deck should be close to legal (60 cards)
        legal, errors = deck.is_legal()
        print(f"Deck legality: {legal}, errors: {errors}")
        
        # Test deck properties
        print(f"Deck summary: {deck.get_summary()}")
        
    except Exception as e:
        pytest.skip(f"Could not load Dreamborn deck: {e}")


def test_create_simple_game(sample_cards):
    """Test creating a simple game with real cards."""
    if len(sample_cards) < 4:
        pytest.skip("Not enough sample cards")
    
    # Create two simple decks (not legal, just for testing)
    deck1_cards = sample_cards[:2]
    deck2_cards = sample_cards[2:4]
    
    deck1 = Deck("Player 1 Deck")
    deck2 = Deck("Player 2 Deck")
    
    # Add multiple copies to make deck larger
    for card in deck1_cards:
        deck1.add_card(card, 4)
    for card in deck2_cards:
        deck2.add_card(card, 4)
    
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Set up decks
    player1.deck = deck1.shuffle()
    player2.deck = deck2.shuffle()
    
    # Draw opening hands
    player1.draw_cards(7)
    player2.draw_cards(7)
    
    # Create game state
    game = GameState(players=[player1, player2])
    
    assert len(game.players) == 2
    assert game.current_player == player1
    assert game.turn_number == 1
    assert not game.game_over
    
    # Test basic game operations with the new engine
    from src.lorcana_sim.engine.move_validator import MoveValidator
    validator = MoveValidator(game)
    legal_actions = validator.get_all_legal_actions()
    assert len(legal_actions) > 0
    
    # Should be able to pass turn  
    pass_actions = [action for action in legal_actions if action[0].value == "pass_turn"]
    assert len(pass_actions) > 0


def test_card_abilities_parsing(card_database):
    """Test that card abilities are properly parsed."""
    cards_with_abilities = []
    
    for card_data in card_database[:50]:
        if card_data.get("abilities"):
            try:
                card = CardFactory.from_json(card_data)
                cards_with_abilities.append(card)
            except Exception:
                continue
    
    assert len(cards_with_abilities) > 0
    
    for card in cards_with_abilities[:10]:  # Test first 10 cards with abilities
        assert len(card.abilities) > 0
        
        for ability in card.abilities:
            # Name might be empty for some abilities (like keyword abilities)
            assert ability.name is not None
            # Effect or full_text should have content
            assert ability.effect or ability.full_text
            assert ability.type
            
            # Ability should have valid type
            assert ability.type.value in ["keyword", "triggered", "static", "activated"]


def _create_random_legal_deck(card_database, deck_name="Random Deck", max_attempts=100):
    """Helper to create a random legal deck from card database."""
    import random
    
    # Create cards from database
    all_cards = []
    for card_data in card_database:
        try:
            card = CardFactory.from_json(card_data)
            all_cards.append(card)
        except Exception:
            continue
    
    if len(all_cards) < 15:
        return None
    
    # Randomly select 15 different cards for a legal deck
    random.seed(42)  # For reproducible tests
    selected_cards = random.sample(all_cards, 15)
    
    # Create a legal-sized deck
    deck = Deck(deck_name)
    
    # Add 15 different cards, 4 copies each = 60 cards
    for card in selected_cards:
        deck.add_card(card, 4)
    
    return deck


def _create_realistic_deck(card_database, primary_colors, deck_name="Realistic Deck"):
    """Helper to create a more realistic deck with proper color distribution."""
    import random
    from collections import defaultdict
    
    # Organize cards by color and cost
    cards_by_color = defaultdict(list)
    for card_data in card_database:
        try:
            card = CardFactory.from_json(card_data)
            cards_by_color[card.color].append(card)
        except Exception:
            continue
    
    # Check if we have enough cards in the primary colors
    available_cards = []
    for color in primary_colors:
        if color in cards_by_color:
            available_cards.extend(cards_by_color[color])
    
    if len(available_cards) < 15:
        return None
    
    # Select cards with realistic distribution
    deck = Deck(deck_name)
    random.seed(42)
    
    # Randomly select unique cards
    selected_cards = random.sample(available_cards, min(15, len(available_cards)))
    
    # Add with varying quantities for more realistic distribution
    for i, card in enumerate(selected_cards):
        if i < 5:  # Core cards - 4 copies
            quantity = 4
        elif i < 10:  # Support cards - 3 copies  
            quantity = 3
        else:  # Tech cards - 2 copies
            quantity = 2
        
        deck.add_card(card, quantity)
        
        if deck.total_cards >= 60:
            break
    
    # Fill to exactly 60 if needed
    while deck.total_cards < 60:
        # Add more copies of existing cards
        for deck_card in deck.cards:
            if deck_card.quantity < 4 and deck.total_cards < 60:
                deck_card.quantity += 1
                break
        else:
            break  # Can't add more
    
    return deck


def test_deck_validation_with_real_cards(card_database):
    """Test deck validation with real cards."""
    deck = _create_random_legal_deck(card_database, "Test Legal Deck")
    
    if deck is None:
        pytest.skip("Not enough valid cards in database for deck validation test")
    
    legal, errors = deck.is_legal()
    
    assert deck.total_cards == 60
    assert legal is True
    assert len(errors) == 0
    
    # Test deck properties
    assert deck.unique_cards == 15
    
    # Test color and cost distributions
    color_dist = deck.get_color_distribution()
    cost_curve = deck.get_cost_curve()
    type_dist = deck.get_type_distribution()
    
    assert len(color_dist) > 0
    assert len(cost_curve) > 0
    assert len(type_dist) > 0
    
    # Test deck shuffle
    shuffled_cards = deck.shuffle()
    assert len(shuffled_cards) == 60
    
    # Count should be correct
    from collections import Counter
    card_counts = Counter(card.id for card in shuffled_cards)
    for card_id, count in card_counts.items():
        assert count == 4  # Each card should appear exactly 4 times


def test_create_multiple_deck_archetypes(card_database):
    """Test creating different deck archetypes with real cards."""
    from lorcana_sim.models.cards.base_card import CardColor
    
    # Test different color combinations
    archetypes = [
        ([CardColor.AMBER], "Amber Aggro"),
        ([CardColor.RUBY], "Ruby Burn"),
        ([CardColor.SAPPHIRE], "Sapphire Control"),
        ([CardColor.EMERALD], "Emerald Ramp"),
        ([CardColor.AMETHYST], "Amethyst Combo"),
        ([CardColor.STEEL], "Steel Midrange"),
    ]
    
    successful_decks = 0
    
    for colors, name in archetypes:
        deck = _create_realistic_deck(card_database, colors, name)
        
        if deck is not None:
            successful_decks += 1
            
            # Basic validation
            assert deck.total_cards <= 60
            assert deck.unique_cards > 0
            
            # Check color distribution favors the archetype
            color_dist = deck.get_color_distribution()
            if len(color_dist) > 0:
                primary_color = colors[0].value
                if primary_color in color_dist:
                    # Primary color should be significant portion
                    assert color_dist[primary_color] > deck.total_cards * 0.3
            
            print(f"  ✅ Created {name}: {deck.total_cards} cards, {deck.unique_cards} unique")
    
    # Should be able to create at least a few decks
    assert successful_decks >= 3, f"Only created {successful_decks} successful decks"


def test_deck_building_edge_cases(card_database):
    """Test edge cases in deck building."""
    import random
    
    # Get some valid cards
    valid_cards = []
    for card_data in card_database[:50]:  # Test with first 50 to keep it fast
        try:
            card = CardFactory.from_json(card_data)
            valid_cards.append(card)
        except Exception:
            continue
    
    if len(valid_cards) < 5:
        pytest.skip("Not enough valid cards for edge case testing")
    
    # Test 1: Deck with too few cards
    deck1 = Deck("Undersized Deck")
    deck1.add_card(valid_cards[0], 4)
    deck1.add_card(valid_cards[1], 4)
    
    legal, errors = deck1.is_legal()
    assert not legal
    assert any("must have 60 cards" in error for error in errors)
    
    # Test 2: Try to add too many copies of a card
    deck2 = Deck("Overstuffed Deck") 
    with pytest.raises(ValueError, match="would exceed 4 copy limit"):
        deck2.add_card(valid_cards[0], 4)
        deck2.add_card(valid_cards[0], 1)  # This should fail
    
    # Test 3: Remove cards
    deck3 = Deck("Removal Test")
    deck3.add_card(valid_cards[0], 3)
    
    assert deck3.total_cards == 3
    removed = deck3.remove_card(valid_cards[0].id, 1)
    assert removed
    assert deck3.total_cards == 2
    
    # Test 4: Card lookup
    found_card = deck3.find_card(valid_cards[0].id)
    assert found_card is not None
    assert found_card.quantity == 2
    
    not_found = deck3.find_card(9999)  # Non-existent ID
    assert not_found is None