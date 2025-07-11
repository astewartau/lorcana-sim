"""Shared test helpers and utilities for all test files."""

from typing import List, Optional
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.action_card import ActionCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.models.abilities.base_ability import Ability, AbilityType
from lorcana_sim.models.game.game_state import GameState, Phase
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.game.deck import Deck
from lorcana_sim.engine.move_validator import MoveValidator
from lorcana_sim.engine.game_engine import GameEngine


def create_test_character(name: str, abilities: List[Ability] = None, 
                         cost: int = 3, strength: int = 2, willpower: int = 3, 
                         lore: int = 1, color: CardColor = CardColor.AMBER) -> CharacterCard:
    """Helper to create test character cards."""
    return CharacterCard(
        id=1,
        name=name,
        version="Test Version",
        full_name=f"{name} - Test Version",
        cost=cost,
        color=color,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test",
        strength=strength,
        willpower=willpower,
        lore=lore,
        abilities=abilities or []
    )


def create_test_song(cost: int, singer_cost: int, name: str = "Test Song") -> ActionCard:
    """Helper to create test song cards."""
    # Create an ability with the proper song text format
    song_ability = Ability(
        name="Song Effect",
        type=AbilityType.STATIC,
        effect=f"A character with cost {singer_cost} or more can sing this song for free.",
        full_text=f"A character with cost {singer_cost} or more can sing this song for free."
    )
    
    song = ActionCard(
        id=1,
        name=name,
        version="Test Version",
        full_name=f"{name} - Test Version",
        cost=cost,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test",
        abilities=[song_ability]
    )
    return song


def create_test_deck(cards: List[tuple] = None) -> Deck:
    """Helper to create test decks. 
    
    Args:
        cards: List of (card, quantity) tuples. If None, creates a basic deck.
    """
    if cards is None:
        # Create a basic deck with test characters
        test_char = create_test_character("Test Character")
        cards = [(test_char, 60)]  # Simple deck for testing
    
    deck = Deck()
    for card, quantity in cards:
        deck.add_cards(card, quantity)
    
    return deck


def setup_basic_game() -> tuple[GameState, MoveValidator, GameEngine]:
    """Create a basic game state for testing."""
    # Create players without decks (simpler for testing)
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Give players some ink
    for i in range(5):
        ink_card = create_test_character(f"Ink {i}")
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    # Create game state
    game_state = GameState(players=[player1, player2])
    game_state.current_phase = Phase.MAIN  # Start in main phase
    
    # Create validator and engine
    validator = MoveValidator(game_state)
    engine = GameEngine(game_state)
    
    return game_state, validator, engine


def setup_game_with_characters(player1_characters: List[CharacterCard], 
                              player2_characters: List[CharacterCard]) -> tuple[GameState, MoveValidator, GameEngine]:
    """Create a game state with specific characters in play.
    
    This is particularly useful for integration testing where you need
    characters with specific abilities already on the board.
    """
    # Create players
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Put characters in play
    player1.characters_in_play = player1_characters
    player2.characters_in_play = player2_characters
    
    # Give players some ink
    for i in range(5):
        ink_card = create_test_character(f"Ink {i}")
        player1.inkwell.append(ink_card)
        player2.inkwell.append(ink_card)
    
    game_state = GameState(players=[player1, player2])
    game_state.current_phase = Phase.MAIN  # Start in main phase where actions happen
    
    validator = MoveValidator(game_state)
    engine = GameEngine(game_state)
    
    return game_state, validator, engine


def create_character_with_ability(name: str, ability: Ability, **kwargs) -> CharacterCard:
    """Helper to create a character with a specific ability."""
    return create_test_character(name, abilities=[ability], **kwargs)


def advance_to_main_phase(game_state: GameState) -> None:
    """Advance game state to MAIN phase for testing actions."""
    game_state.current_phase = Phase.MAIN
    game_state.players[0].available_ink = 10
    game_state.players[1].available_ink = 10