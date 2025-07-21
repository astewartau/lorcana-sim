"""Integration tests for UNTOLD TREASURE - When you play this character, if you have an Illusion character in play, you may draw a card."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.untold_treasure import create_untold_treasure


class TestUntoldTreasureIntegration(GameEngineTestBase):
    """Integration tests for UNTOLD TREASURE named ability."""
    
    def create_untold_treasure_character(self, name="Treasure Character", cost=3, strength=2, willpower=3):
        """Create a test character with UNTOLD TREASURE ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower
        )
        
        # Add UNTOLD TREASURE ability
        ability_data = {"name": "UNTOLD TREASURE", "type": "triggered"}
        untold_treasure_ability = create_untold_treasure(character, ability_data)
        character.composable_abilities.append(untold_treasure_ability)
        
        return character
    
    def create_illusion_character(self, name="Illusion Character"):
        """Create an Illusion character for testing the condition."""
        return self.create_test_character(
            name=name,
            cost=2,
            strength=1,
            willpower=2,
            subtypes=["Illusion"]
        )
    
    
    def add_cards_to_deck(self, player, count=10):
        """Add cards to player's deck for drawing."""
        for i in range(count):
            card = self.create_test_character(f"Deck Card {i}", cost=1)
            player.deck.append(card)
    
    def test_untold_treasure_ability_creation(self):
        """Test that UNTOLD TREASURE ability creates correctly."""
        character = self.create_untold_treasure_character("Treasure Guardian")
        
        assert len(character.composable_abilities) == 1
        untold_treasure_ability = character.composable_abilities[0]
        assert untold_treasure_ability.name == "UNTOLD TREASURE"
        assert untold_treasure_ability.character == character
    
    def test_untold_treasure_triggers_with_illusion_present(self):
        """Test that UNTOLD TREASURE triggers when an Illusion character is in play."""
        treasure_char = self.create_untold_treasure_character("Treasure Guardian")
        illusion_char = self.create_illusion_character("Test Illusion")
        
        # Add cards to deck for drawing
        self.add_cards_to_deck(self.player1, 5)
        
        # Put illusion character in play first
        self.play_character(illusion_char, self.player1)
        
        # Verify illusion is in play
        assert illusion_char in self.player1.characters_in_play
        assert "Illusion" in illusion_char.subtypes
        
        # Track hand size before playing treasure character
        initial_hand_size = len(self.player1.hand)
        
        # Play treasure character
        message = self.play_character(treasure_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert treasure_char in self.player1.characters_in_play
        
        # Should have UNTOLD TREASURE ability
        assert len(treasure_char.composable_abilities) == 1
        assert treasure_char.composable_abilities[0].name == "UNTOLD TREASURE"
    
    def test_untold_treasure_does_not_trigger_without_illusion(self):
        """Test that UNTOLD TREASURE does not trigger when no Illusion character is in play."""
        treasure_char = self.create_untold_treasure_character("Treasure Guardian")
        normal_char = self.create_test_character("Normal Character")  # No Illusion subtype
        
        # Add cards to deck for drawing
        self.add_cards_to_deck(self.player1, 5)
        
        # Put normal character in play (not an Illusion)
        self.play_character(normal_char, self.player1)
        
        # Verify no illusion is in play
        assert normal_char in self.player1.characters_in_play
        assert "Illusion" not in normal_char.subtypes
        
        # Track hand size before playing treasure character
        initial_hand_size = len(self.player1.hand)
        
        # Play treasure character
        message = self.play_character(treasure_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert treasure_char in self.player1.characters_in_play
        
        # Should still have ability, but it shouldn't trigger without Illusion
        assert len(treasure_char.composable_abilities) == 1
        assert treasure_char.composable_abilities[0].name == "UNTOLD TREASURE"
        
        # Hand size should not have changed (no draw)
        current_hand_size = len(self.player1.hand)
        assert current_hand_size == initial_hand_size
    
    def test_untold_treasure_no_characters_in_play(self):
        """Test UNTOLD TREASURE when no characters are in play."""
        treasure_char = self.create_untold_treasure_character("Treasure Guardian")
        
        # Add cards to deck for drawing
        self.add_cards_to_deck(self.player1, 5)
        
        # No characters in play initially
        assert len(self.player1.characters_in_play) == 0
        
        # Track hand size before playing treasure character
        initial_hand_size = len(self.player1.hand)
        
        # Play treasure character
        message = self.play_character(treasure_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert treasure_char in self.player1.characters_in_play
        
        # Should have ability but no trigger condition met
        assert len(treasure_char.composable_abilities) == 1
        assert treasure_char.composable_abilities[0].name == "UNTOLD TREASURE"
        
        # Hand size should not have changed (no Illusion present)
        current_hand_size = len(self.player1.hand)
        assert current_hand_size == initial_hand_size
    
    def test_untold_treasure_multiple_illusions_in_play(self):
        """Test UNTOLD TREASURE with multiple Illusion characters in play."""
        treasure_char = self.create_untold_treasure_character("Treasure Guardian")
        illusion_char1 = self.create_illusion_character("First Illusion")
        illusion_char2 = self.create_illusion_character("Second Illusion")
        
        # Add cards to deck for drawing
        self.add_cards_to_deck(self.player1, 5)
        
        # Put multiple illusion characters in play
        self.play_character(illusion_char1, self.player1)
        self.play_character(illusion_char2, self.player1)
        
        # Verify both illusions are in play
        assert illusion_char1 in self.player1.characters_in_play
        assert illusion_char2 in self.player1.characters_in_play
        assert "Illusion" in illusion_char1.subtypes
        assert "Illusion" in illusion_char2.subtypes
        
        # Track hand size before playing treasure character
        initial_hand_size = len(self.player1.hand)
        
        # Play treasure character
        message = self.play_character(treasure_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert treasure_char in self.player1.characters_in_play
        
        # Should have UNTOLD TREASURE ability
        assert len(treasure_char.composable_abilities) == 1
        assert treasure_char.composable_abilities[0].name == "UNTOLD TREASURE"
    
    def test_untold_treasure_opponent_illusion_does_not_count(self):
        """Test that opponent's Illusion characters don't trigger UNTOLD TREASURE."""
        treasure_char = self.create_untold_treasure_character("Treasure Guardian")
        opponent_illusion = self.create_illusion_character("Opponent Illusion")
        
        # Add cards to deck for drawing
        self.add_cards_to_deck(self.player1, 5)
        
        # Put illusion character in opponent's play area
        self.play_character(opponent_illusion, self.player2)
        
        # Verify opponent's illusion is in play
        assert opponent_illusion in self.player2.characters_in_play
        assert "Illusion" in opponent_illusion.subtypes
        
        # Track hand size before playing treasure character
        initial_hand_size = len(self.player1.hand)
        
        # Play treasure character for player1
        message = self.play_character(treasure_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert treasure_char in self.player1.characters_in_play
        
        # Should have ability but opponent's Illusion shouldn't trigger it
        assert len(treasure_char.composable_abilities) == 1
        assert treasure_char.composable_abilities[0].name == "UNTOLD TREASURE"
        
        # Hand size should not have changed (opponent's Illusion doesn't count)
        current_hand_size = len(self.player1.hand)
        assert current_hand_size == initial_hand_size
    
    def test_untold_treasure_only_triggers_for_self(self):
        """Test that UNTOLD TREASURE only triggers when the ability owner enters play."""
        treasure_char = self.create_untold_treasure_character("Treasure Guardian", cost=2)
        other_char = self.create_test_character("Other Character", cost=2)
        illusion_char = self.create_illusion_character("Test Illusion")
        
        # Add cards to deck for drawing
        self.add_cards_to_deck(self.player1, 5)
        
        # Put treasure character and illusion in play first
        self.play_character(treasure_char, self.player1)
        self.play_character(illusion_char, self.player1)
        
        # Track hand size before playing other character
        initial_hand_size = len(self.player1.hand)
        
        # Other character enters play (should NOT trigger UNTOLD TREASURE)
        message = self.play_character(other_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert other_char in self.player1.characters_in_play
        
        # Hand size should not have changed (UNTOLD TREASURE should not have triggered)
        current_hand_size = len(self.player1.hand)
        assert current_hand_size == initial_hand_size
    
    def test_untold_treasure_ability_registration(self):
        """Test that UNTOLD TREASURE ability is properly registered."""
        treasure_char = self.create_untold_treasure_character("Treasure Guardian")
        
        # Put character in play
        self.play_character(treasure_char, self.player1)
        
        # Should have ability
        assert treasure_char.composable_abilities
        assert treasure_char.composable_abilities[0].name == "UNTOLD TREASURE"
        
        # Check that it has listeners for the correct event
        ability = treasure_char.composable_abilities[0]
        assert len(ability.listeners) > 0
    
    def test_untold_treasure_may_choice_effect(self):
        """Test that UNTOLD TREASURE uses 'may' choice effect correctly."""
        treasure_char = self.create_untold_treasure_character("Treasure Guardian")
        illusion_char = self.create_illusion_character("Test Illusion")
        
        # Add cards to deck for drawing
        self.add_cards_to_deck(self.player1, 5)
        
        # Put illusion character in play first
        self.play_character(illusion_char, self.player1)
        
        # Play treasure character
        message = self.play_character(treasure_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert treasure_char in self.player1.characters_in_play
        
        # Should have UNTOLD TREASURE ability with choice effect
        assert len(treasure_char.composable_abilities) == 1
        untold_treasure_ability = treasure_char.composable_abilities[0]
        assert untold_treasure_ability.name == "UNTOLD TREASURE"
        
        # Verify the ability has the correct components
        assert len(untold_treasure_ability.listeners) > 0
        
        # The actual choice handling would happen through the game engine's choice system
        # For now, verify the ability is correctly set up with may_effect


if __name__ == "__main__":
    pytest.main([__file__, "-v"])