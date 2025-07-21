"""Base class for GameEngine integration tests with proper setup and utilities."""

from typing import List, Optional
from lorcana_sim.engine.game_engine import GameEngine, ExecutionMode
from lorcana_sim.models.game.game_state import GameState, Phase
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.action_card import ActionCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, PassMove, InkMove
from lorcana_sim.engine.message_engine import MessageType


class GameEngineTestBase:
    """Base class for integration tests using GameEngine with proper setup.
    
    This class provides:
    - Properly initialized GameEngine with two players
    - Ink setup for both players
    - Phase management utilities
    - Character/card creation helpers
    - Common assertion patterns
    """
    
    def setup_method(self):
        """Set up test game with players, decks, and proper initialization."""
        # Create players
        self.player1 = Player("Alice")
        self.player2 = Player("Bob")
        
        # Create basic decks (empty for most tests, individual tests can add cards)
        self.create_basic_decks()
        
        # Create game state and engine
        self.game_state = GameState([self.player1, self.player2])
        self.game_engine = GameEngine(self.game_state, ExecutionMode.MANUAL)
        
        # Start the game
        self.game_engine.start_game()
        
        # Ensure we're in the PLAY phase for the first player
        self.advance_to_play_phase()
        
        # Give both players sufficient ink for testing
        self.setup_player_ink(self.player1, ink_count=7)
        self.setup_player_ink(self.player2, ink_count=7)
    
    def create_basic_decks(self):
        """Create basic decks with minimal cards for game initialization."""
        # Create some basic cards for each player's deck
        for i in range(10):
            card1 = self.create_test_character(f"Deck Card {i}", cost=1, card_id=100+i)
            card2 = self.create_test_character(f"Deck Card {i+10}", cost=1, card_id=200+i)
            self.player1.deck.append(card1)
            self.player2.deck.append(card2)
    
    def setup_player_ink(self, player: Player, ink_count: int = 7):
        """Give a player the specified amount of ink."""
        # Clear existing inkwell
        player.inkwell.clear()
        
        # Add ink cards
        for i in range(ink_count):
            ink_card = self.create_test_character(f"Ink Card {i}", cost=1, card_id=1000+i)
            player.inkwell.append(ink_card)
    
    def advance_to_play_phase(self):
        """Advance the game to the PLAY phase for the current player."""
        max_attempts = 10
        attempts = 0
        
        while self.game_state.current_phase != Phase.PLAY and attempts < max_attempts:
            try:
                message = self.game_engine.next_message(PassMove())
                # Debug: print(f"Phase transition: {self.game_state.current_phase}")
            except:
                break
            attempts += 1
        
        if attempts >= max_attempts:
            raise RuntimeError(f"Failed to reach PLAY phase after {max_attempts} attempts")
    
    def create_test_character(self, name: str = "Test Character", cost: int = 3, 
                             strength: int = 2, willpower: int = 3, lore: int = 1,
                             color: CardColor = CardColor.AMBER, 
                             subtypes: Optional[List[str]] = None,
                             damage: int = 0, exerted: bool = False,
                             card_id: Optional[int] = None) -> CharacterCard:
        """Create a test character card with specified properties."""
        if card_id is None:
            # Generate a unique ID
            card_id = len(self.player1.deck) + len(self.player2.deck) + len(self.player1.hand) + len(self.player2.hand) + 500
        
        character = CharacterCard(
            id=card_id,
            name=name,
            version=None,
            full_name=name,
            cost=cost,
            color=color,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=1,
            story="",
            strength=strength,
            willpower=willpower,
            lore=lore,
            subtypes=subtypes or []
        )
        
        # Apply damage and exertion if specified
        if damage > 0:
            character.damage = damage
        if exerted:
            character.exerted = exerted
        
        return character
    
    def create_test_action(self, name: str = "Test Action", cost: int = 2,
                          color: CardColor = CardColor.AMBER,
                          card_id: Optional[int] = None) -> ActionCard:
        """Create a test action card."""
        if card_id is None:
            card_id = len(self.player1.deck) + len(self.player2.deck) + len(self.player1.hand) + len(self.player2.hand) + 600
        
        return ActionCard(
            id=card_id,
            name=name,
            version=None,
            full_name=name,
            cost=cost,
            color=color,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=1,
            story=""
        )
    
    def play_character(self, character: CharacterCard, player: Player):
        """Play a character using the game engine, ensuring proper setup."""
        # Add character to player's hand
        if character not in player.hand:
            player.hand.append(character)
        
        # Ensure we're in the right phase and it's the right player's turn
        if self.game_state.current_player != player:
            # Advance turns until it's this player's turn
            max_attempts = 5
            attempts = 0
            while self.game_state.current_player != player and attempts < max_attempts:
                self.advance_to_play_phase()
                # Pass turn to other player
                try:
                    self.game_engine.next_message(PassMove())
                except:
                    pass
                attempts += 1
        
        # Ensure we're in PLAY phase
        self.advance_to_play_phase()
        
        # Play the character
        play_move = PlayMove(character)
        message = self.game_engine.next_message(play_move)
        return message
    
    def process_ability_messages(self, max_messages: int = 5):
        """Process any pending ability trigger and effect messages."""
        messages = []
        for _ in range(max_messages):
            try:
                message = self.game_engine.next_message()
                messages.append(message)
                # Stop if we get an action required message (player input needed)
                if message.type == MessageType.ACTION_REQUIRED:
                    break
            except:
                # No more messages
                break
        return messages
    
    def assert_character_in_play(self, character: CharacterCard, player: Player):
        """Assert that a character is in the specified player's play area."""
        assert character in player.characters_in_play, f"{character.name} should be in {player.name}'s play area"
    
    def assert_character_not_in_play(self, character: CharacterCard, player: Player):
        """Assert that a character is NOT in the specified player's play area."""
        assert character not in player.characters_in_play, f"{character.name} should NOT be in {player.name}'s play area"
    
    def assert_character_exerted(self, character: CharacterCard, exerted: bool = True):
        """Assert character's exerted state."""
        if exerted:
            assert character.exerted, f"{character.name} should be exerted"
        else:
            assert not character.exerted, f"{character.name} should NOT be exerted"
    
    def assert_character_damage(self, character: CharacterCard, expected_damage: int):
        """Assert character's damage amount."""
        assert character.damage == expected_damage, f"{character.name} should have {expected_damage} damage, but has {character.damage}"
    
    def assert_message_type(self, message, expected_type: MessageType):
        """Assert message is of expected type."""
        assert message.type == expected_type, f"Expected message type {expected_type}, got {message.type}"
    
    def assert_message_has_event_data(self, message):
        """Assert message has event data (for ability trigger verification)."""
        assert message.event_data is not None or message.step is not None, "Message should have event data or step information"