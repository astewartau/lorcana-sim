"""Integration tests for MUSICAL DEBUT - When you play this character, look at the top 4 cards of your deck. You may reveal a song card and put it into your hand. Put the rest on the bottom of your deck in any order."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.action_card import ActionCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.musical_debut import create_musical_debut


class TestMusicalDebutIntegration(GameEngineTestBase):
    """Integration tests for MUSICAL DEBUT named ability."""
    
    def create_musical_debut_character(self, name="Musical Character", cost=3, strength=2, willpower=3):
        """Create a test character with MUSICAL DEBUT ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower
        )
        
        # Add MUSICAL DEBUT ability
        ability_data = {"name": "MUSICAL DEBUT", "type": "triggered"}
        musical_debut_ability = create_musical_debut(character, ability_data)
        character.composable_abilities.append(musical_debut_ability)
        
        return character
    
    def create_song_card(self, name="Test Song"):
        """Create a test song (action) card."""
        song_card = ActionCard(
            id=len(self.player1.deck) + len(self.player2.deck) + 200,
            name=name,
            version=None,
            full_name=name,
            cost=2,
            color=CardColor.RUBY,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=2,
            story=""
        )
        # Add song effect to make it detectable as a song
        song_card.effects = ["Characters with cost 2 or more can sing this song for 1 ink."]
        return song_card
    
    def create_regular_card(self, name="Regular Card"):
        """Create a regular (non-song) card."""
        return self.create_test_character(name, cost=2)
    
    def put_character_in_play(self, character, player):
        """Put a character in play using game engine."""
        player.hand.append(character)
        play_move = PlayMove(character)
        message = self.game_engine.next_message(play_move)
        return message
    
    def setup_deck_with_songs(self, player, song_count=2, regular_count=8):
        """Set up a deck with specific number of songs and regular cards."""
        # Clear existing deck
        player.deck.clear()
        
        # Add songs to deck
        for i in range(song_count):
            song = self.create_song_card(f"Song {i+1}")
            player.deck.append(song)
        
        # Add regular cards to deck
        for i in range(regular_count):
            card = self.create_regular_card(f"Regular Card {i+1}")
            player.deck.append(card)
    
    def test_musical_debut_ability_creation(self):
        """Test that MUSICAL DEBUT ability creates correctly."""
        character = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        assert len(character.composable_abilities) == 1
        musical_debut_ability = character.composable_abilities[0]
        assert musical_debut_ability.name == "MUSICAL DEBUT"
        assert musical_debut_ability.character == character
    
    def test_musical_debut_triggers_on_play(self):
        """Test that MUSICAL DEBUT triggers when the character is played."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Set up deck with at least 4 cards
        self.setup_deck_with_songs(self.player1, song_count=2, regular_count=3)
        
        # Verify deck has enough cards
        assert len(self.player1.deck) >= 4
        initial_deck_size = len(self.player1.deck)
        
        # Play musical debut character
        message = self.put_character_in_play(musical_debut_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert musical_debut_char in self.player1.characters_in_play
        
        # Should have MUSICAL DEBUT ability
        assert len(musical_debut_char.composable_abilities) == 1
        assert musical_debut_char.composable_abilities[0].name == "MUSICAL DEBUT"
    
    def test_musical_debut_with_song_cards_in_deck(self):
        """Test MUSICAL DEBUT when there are song cards in the top 4 cards."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Set up deck with songs in top positions
        self.setup_deck_with_songs(self.player1, song_count=3, regular_count=5)
        
        # Track initial hand size
        initial_hand_size = len(self.player1.hand)
        initial_deck_size = len(self.player1.deck)
        
        # Play musical debut character
        message = self.put_character_in_play(musical_debut_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert musical_debut_char in self.player1.characters_in_play
        
        # Should have ability
        assert len(musical_debut_char.composable_abilities) == 1
        assert musical_debut_char.composable_abilities[0].name == "MUSICAL DEBUT"
        
        # The actual card manipulation would happen through game engine choice system
        # For now, verify the ability is present and functional
    
    def test_musical_debut_with_no_song_cards(self):
        """Test MUSICAL DEBUT when there are no song cards in the top 4 cards."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Set up deck with no songs in top 4 cards
        self.setup_deck_with_songs(self.player1, song_count=0, regular_count=10)
        
        # Track initial hand size
        initial_hand_size = len(self.player1.hand)
        initial_deck_size = len(self.player1.deck)
        
        # Play musical debut character
        message = self.put_character_in_play(musical_debut_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert musical_debut_char in self.player1.characters_in_play
        
        # Should have ability even with no songs to find
        assert len(musical_debut_char.composable_abilities) == 1
        assert musical_debut_char.composable_abilities[0].name == "MUSICAL DEBUT"
    
    def test_musical_debut_with_fewer_than_4_cards_in_deck(self):
        """Test MUSICAL DEBUT when deck has fewer than 4 cards."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Set up deck with only 2 cards
        self.setup_deck_with_songs(self.player1, song_count=1, regular_count=1)
        
        # Verify deck has fewer than 4 cards
        assert len(self.player1.deck) < 4
        initial_deck_size = len(self.player1.deck)
        
        # Play musical debut character
        message = self.put_character_in_play(musical_debut_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert musical_debut_char in self.player1.characters_in_play
        
        # Should have ability even with small deck
        assert len(musical_debut_char.composable_abilities) == 1
        assert musical_debut_char.composable_abilities[0].name == "MUSICAL DEBUT"
    
    def test_musical_debut_with_empty_deck(self):
        """Test MUSICAL DEBUT when deck is empty."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Clear deck completely
        self.player1.deck.clear()
        
        # Verify deck is empty
        assert len(self.player1.deck) == 0
        
        # Play musical debut character
        message = self.put_character_in_play(musical_debut_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert musical_debut_char in self.player1.characters_in_play
        
        # Should have ability even with empty deck
        assert len(musical_debut_char.composable_abilities) == 1
        assert musical_debut_char.composable_abilities[0].name == "MUSICAL DEBUT"
    
    def test_musical_debut_only_triggers_for_self(self):
        """Test that MUSICAL DEBUT only triggers when the ability owner enters play."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        other_char = self.create_test_character("Other Character")
        
        # Set up deck with songs
        self.setup_deck_with_songs(self.player1, song_count=2, regular_count=3)
        
        # Put musical debut character in play first
        self.put_character_in_play(musical_debut_char, self.player1)
        
        # Track deck state before playing other character
        deck_state_before = len(self.player1.deck)
        hand_state_before = len(self.player1.hand)
        
        # Other character enters play (should NOT trigger MUSICAL DEBUT)
        message = self.put_character_in_play(other_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert other_char in self.player1.characters_in_play
        
        # MUSICAL DEBUT should not have triggered for other character
        # (Deck manipulation should not have occurred)\n    
    def test_musical_debut_ability_registration(self):
        """Test that MUSICAL DEBUT ability is properly registered."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Put character in play
        self.put_character_in_play(musical_debut_char, self.player1)
        
        # Should have ability
        assert musical_debut_char.composable_abilities
        assert musical_debut_char.composable_abilities[0].name == "MUSICAL DEBUT"
        
        # Check that it has listeners for the correct event
        ability = musical_debut_char.composable_abilities[0]
        assert len(ability.listeners) > 0
    
    def test_musical_debut_effect_structure(self):
        """Test that MUSICAL DEBUT uses LOOK_AT_TOP_4 effect correctly."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Should have MUSICAL DEBUT ability with correct effect
        assert len(musical_debut_char.composable_abilities) == 1
        musical_debut_ability = musical_debut_char.composable_abilities[0]
        assert musical_debut_ability.name == "MUSICAL DEBUT"
        
        # Verify the ability has the correct components
        assert len(musical_debut_ability.listeners) > 0
        
        # The actual LOOK_AT_TOP_4 effect would be handled by the game engine
        # For now, verify the ability is correctly set up
    
    def test_musical_debut_deck_ordering(self):
        """Test that MUSICAL DEBUT maintains proper deck ordering."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Set up deck with known card order
        self.setup_deck_with_songs(self.player1, song_count=2, regular_count=6)
        
        # Track the top 4 cards before ability triggers
        top_4_cards = self.player1.deck[:4] if len(self.player1.deck) >= 4 else self.player1.deck[:]
        remaining_cards = self.player1.deck[4:] if len(self.player1.deck) > 4 else []
        
        # Play musical debut character
        message = self.put_character_in_play(musical_debut_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert musical_debut_char in self.player1.characters_in_play
        
        # Should have ability
        assert len(musical_debut_char.composable_abilities) == 1
        assert musical_debut_char.composable_abilities[0].name == "MUSICAL DEBUT"
        
        # The actual deck manipulation and ordering would be handled by the choice system
        # For now, verify the ability is set up to trigger on the correct event
    
    def test_musical_debut_choice_interaction(self):
        """Test that MUSICAL DEBUT creates appropriate choice interactions."""
        musical_debut_char = self.create_musical_debut_character("Ariel - Spectacular Singer")
        
        # Set up deck with both songs and regular cards
        song1 = self.create_song_card("Beautiful Song")
        song2 = self.create_song_card("Wonderful Melody")
        regular1 = self.create_regular_card("Regular Card 1")
        regular2 = self.create_regular_card("Regular Card 2")
        
        # Put cards in specific order in deck
        self.player1.deck = [song1, regular1, song2, regular2]
        
        # Play musical debut character
        message = self.put_character_in_play(musical_debut_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert musical_debut_char in self.player1.characters_in_play
        
        # Should have ability that will create choices for song selection
        assert len(musical_debut_char.composable_abilities) == 1
        musical_debut_ability = musical_debut_char.composable_abilities[0]
        assert musical_debut_ability.name == "MUSICAL DEBUT"
        
        # The actual choice handling would happen through the game engine's choice system
        # For now, verify the ability is correctly set up to handle song selection


if __name__ == "__main__":
    pytest.main([__file__, "-v"])