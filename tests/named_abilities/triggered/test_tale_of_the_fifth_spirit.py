"""Integration tests for TALE OF THE FIFTH SPIRIT - When you play this character, if an opponent has an exerted character in play, gain 1 lore."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.tale_of_the_fifth_spirit import create_tale_of_the_fifth_spirit


class TestTaleOfTheFifthSpiritIntegration(GameEngineTestBase):
    """Integration tests for TALE OF THE FIFTH SPIRIT named ability."""
    
    def create_tale_character(self, name="Honeymaren", cost=2, strength=2, willpower=3):
        """Create a test character with TALE OF THE FIFTH SPIRIT ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            color=CardColor.EMERALD,
            subtypes=["Hero", "Northuldra"]
        )
        
        # Add the TALE OF THE FIFTH SPIRIT ability
        ability_data = {"name": "TALE OF THE FIFTH SPIRIT", "type": "triggered"}
        tale_ability = create_tale_of_the_fifth_spirit(character, ability_data)
        character.composable_abilities = [tale_ability]
        
        return character
    
    def test_tale_of_the_fifth_spirit_creation(self):
        """Unit test: Verify TALE OF THE FIFTH SPIRIT ability creates correctly."""
        character = self.create_tale_character()
        
        assert len(character.composable_abilities) == 1
        ability = character.composable_abilities[0]
        assert "TALE OF THE FIFTH SPIRIT" in ability.name
    
    def test_tale_gains_lore_when_opponent_has_exerted_character(self):
        """Test that TALE OF THE FIFTH SPIRIT grants 1 lore when opponent has exerted characters."""
        # Create Honeymaren with TALE OF THE FIFTH SPIRIT
        honeymaren = self.create_tale_character(name="Honeymaren", cost=2)
        
        # Create opponent characters - some exerted, some not
        opponent_char1 = self.create_test_character(name="Opponent Char 1", strength=3, willpower=2)
        opponent_char2 = self.create_test_character(name="Opponent Char 2", strength=2, willpower=4)
        
        # Set up controllers
        honeymaren.controller = self.player1
        opponent_char1.controller = self.player2
        opponent_char2.controller = self.player2
        
        # Put opponent characters in play and exert one of them
        self.player2.characters_in_play = [opponent_char1, opponent_char2]
        opponent_char1.exerted = True  # This should trigger the condition
        opponent_char2.exerted = False
        
        # Set up game state
        self.setup_player_ink(self.player1, ink_count=3)
        self.player1.hand = [honeymaren]
        
        # Record initial state
        initial_lore = self.player1.lore
        print(f"Initial state:")
        print(f"  Player1 lore: {initial_lore}")
        print(f"  Opponent exerted characters: {[char.name for char in self.player2.characters_in_play if char.exerted]}")
        
        # Play Honeymaren to trigger TALE OF THE FIFTH SPIRIT
        play_message = self.play_character(honeymaren, self.player1)
        assert play_message.type == MessageType.STEP_EXECUTED
        assert honeymaren in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        assert "TALE OF THE FIFTH SPIRIT" in str(trigger_message.step)
        print(f"Trigger message: {trigger_message.step}")
        
        # Get the effect application message
        effect_message = self.game_engine.next_message()
        print(f"Effect message: {effect_message.type}")
        if hasattr(effect_message, 'step'):
            print(f"  Step: {effect_message.step}")
        
        # Verify lore was gained
        final_lore = self.player1.lore
        print(f"Final lore: {final_lore}")
        
        assert final_lore == initial_lore + 1, f"Expected {initial_lore + 1} lore, got {final_lore}"
        
        print(f"✅ SUCCESS: Gained 1 lore when opponent has exerted character (lore: {initial_lore} → {final_lore})")
    
    def test_tale_no_lore_when_no_opponent_exerted_characters(self):
        """Test that TALE OF THE FIFTH SPIRIT grants no lore when opponents have no exerted characters."""
        # Create Honeymaren with TALE OF THE FIFTH SPIRIT
        honeymaren = self.create_tale_character(name="Honeymaren", cost=2)
        
        # Create opponent characters - none exerted
        opponent_char1 = self.create_test_character(name="Opponent Char 1", strength=3, willpower=2)
        opponent_char2 = self.create_test_character(name="Opponent Char 2", strength=2, willpower=4)
        
        # Set up controllers
        honeymaren.controller = self.player1
        opponent_char1.controller = self.player2
        opponent_char2.controller = self.player2
        
        # Put opponent characters in play - NONE exerted
        self.player2.characters_in_play = [opponent_char1, opponent_char2]
        opponent_char1.exerted = False  # Not exerted
        opponent_char2.exerted = False  # Not exerted
        
        # Set up game state
        self.setup_player_ink(self.player1, ink_count=3)
        self.player1.hand = [honeymaren]
        
        # Record initial state
        initial_lore = self.player1.lore
        print(f"Initial state:")
        print(f"  Player1 lore: {initial_lore}")
        print(f"  Opponent exerted characters: {[char.name for char in self.player2.characters_in_play if char.exerted]}")
        
        # Play Honeymaren to trigger TALE OF THE FIFTH SPIRIT
        play_message = self.play_character(honeymaren, self.player1)
        assert play_message.type == MessageType.STEP_EXECUTED
        assert honeymaren in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        assert "TALE OF THE FIFTH SPIRIT" in str(trigger_message.step)
        print(f"Trigger message: {trigger_message.step}")
        
        # Try to get effect message (might not exist if condition fails)
        try:
            effect_message = self.game_engine.next_message()
            print(f"Effect message: {effect_message.type}")
            if hasattr(effect_message, 'step'):
                print(f"  Step: {effect_message.step}")
        except ValueError as e:
            if "Expected move or choice" in str(e):
                print("No effect message - condition likely failed")
            else:
                raise
        
        # Verify no lore was gained
        final_lore = self.player1.lore
        print(f"Final lore: {final_lore}")
        
        assert final_lore == initial_lore, f"Expected no lore gain ({initial_lore}), got {final_lore}"
        
        print(f"✅ SUCCESS: No lore gained when no opponent has exerted characters (lore unchanged: {initial_lore})")
    
    def test_tale_no_lore_when_no_opponents(self):
        """Test that TALE OF THE FIFTH SPIRIT grants no lore when there are no opponents."""
        # Create Honeymaren with TALE OF THE FIFTH SPIRIT
        honeymaren = self.create_tale_character(name="Honeymaren", cost=2)
        
        # Set up controllers
        honeymaren.controller = self.player1
        
        # NO opponent characters in play
        self.player2.characters_in_play = []
        
        # Set up game state
        self.setup_player_ink(self.player1, ink_count=3)
        self.player1.hand = [honeymaren]
        
        # Record initial state
        initial_lore = self.player1.lore
        
        # Play Honeymaren to trigger TALE OF THE FIFTH SPIRIT
        play_message = self.play_character(honeymaren, self.player1)
        assert play_message.type == MessageType.STEP_EXECUTED
        assert honeymaren in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        assert "TALE OF THE FIFTH SPIRIT" in str(trigger_message.step)
        
        # Verify no lore was gained
        final_lore = self.player1.lore
        assert final_lore == initial_lore, f"Expected no lore gain ({initial_lore}), got {final_lore}"
        
        print(f"✅ SUCCESS: No lore gained when no opponents (lore unchanged: {initial_lore})")
    
    def test_tale_ignores_own_exerted_characters(self):
        """Test that TALE OF THE FIFTH SPIRIT ignores player's own exerted characters."""
        # Create Honeymaren with TALE OF THE FIFTH SPIRIT
        honeymaren = self.create_tale_character(name="Honeymaren", cost=2)
        
        # Create player's own characters - some exerted
        own_char1 = self.create_test_character(name="Own Char 1", strength=3, willpower=2)
        own_char2 = self.create_test_character(name="Own Char 2", strength=2, willpower=4)
        
        # Set up controllers (all belong to player1)
        honeymaren.controller = self.player1
        own_char1.controller = self.player1
        own_char2.controller = self.player1
        
        # Put own characters in play and exert them
        self.player1.characters_in_play = [own_char1, own_char2]
        own_char1.exerted = True  # Player's own exerted character - should NOT trigger
        own_char2.exerted = True  # Player's own exerted character - should NOT trigger
        
        # No opponent characters
        self.player2.characters_in_play = []
        
        # Set up game state
        self.setup_player_ink(self.player1, ink_count=3)
        self.player1.hand = [honeymaren]
        
        # Record initial state
        initial_lore = self.player1.lore
        
        # Play Honeymaren to trigger TALE OF THE FIFTH SPIRIT
        play_message = self.play_character(honeymaren, self.player1)
        assert play_message.type == MessageType.STEP_EXECUTED
        assert honeymaren in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        assert "TALE OF THE FIFTH SPIRIT" in str(trigger_message.step)
        
        # Verify no lore was gained (own exerted characters don't count)
        final_lore = self.player1.lore
        assert final_lore == initial_lore, f"Expected no lore gain ({initial_lore}), got {final_lore}"
        
        print(f"✅ SUCCESS: Own exerted characters ignored (lore unchanged: {initial_lore})")
    
    def test_tale_multiple_opponent_exerted_characters_still_gives_one_lore(self):
        """Test that TALE OF THE FIFTH SPIRIT gives only 1 lore even with multiple opponent exerted characters."""
        # Create Honeymaren with TALE OF THE FIFTH SPIRIT
        honeymaren = self.create_tale_character(name="Honeymaren", cost=2)
        
        # Create multiple opponent characters - all exerted
        opponent_chars = []
        for i in range(3):
            char = self.create_test_character(name=f"Opponent Char {i+1}", strength=2, willpower=2)
            char.controller = self.player2
            char.exerted = True  # All exerted
            opponent_chars.append(char)
        
        # Set up controllers
        honeymaren.controller = self.player1
        
        # Put opponent characters in play
        self.player2.characters_in_play = opponent_chars
        
        # Set up game state
        self.setup_player_ink(self.player1, ink_count=3)
        self.player1.hand = [honeymaren]
        
        # Record initial state
        initial_lore = self.player1.lore
        exerted_count = len([char for char in self.player2.characters_in_play if char.exerted])
        print(f"Opponent has {exerted_count} exerted characters")
        
        # Play Honeymaren to trigger TALE OF THE FIFTH SPIRIT
        play_message = self.play_character(honeymaren, self.player1)
        assert play_message.type == MessageType.STEP_EXECUTED
        assert honeymaren in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        assert "TALE OF THE FIFTH SPIRIT" in str(trigger_message.step)
        
        # Process effect message
        effect_message = self.game_engine.next_message()
        
        # Verify only 1 lore was gained (not per exerted character)
        final_lore = self.player1.lore
        assert final_lore == initial_lore + 1, f"Expected {initial_lore + 1} lore (only 1, not {exerted_count}), got {final_lore}"
        
        print(f"✅ SUCCESS: Only 1 lore gained despite {exerted_count} exerted opponents (lore: {initial_lore} → {final_lore})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])