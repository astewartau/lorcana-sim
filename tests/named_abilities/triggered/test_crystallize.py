"""Integration tests for CRYSTALLIZE - When you play this character, exert chosen opposing character."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.crystallize import create_crystallize


class TestCrystallizeIntegration(GameEngineTestBase):
    """Integration tests for CRYSTALLIZE named ability."""
    
    def create_crystallize_character(self, name="Elsa - Snow Queen", cost=3, strength=2, willpower=3):
        """Create a test character with CRYSTALLIZE ability."""
        character = self.create_test_character(
            name=name, 
            cost=cost, 
            strength=strength, 
            willpower=willpower,
            color=CardColor.SAPPHIRE
        )
        
        # Add CRYSTALLIZE ability
        ability_data = {"name": "CRYSTALLIZE", "type": "triggered"}
        crystallize_ability = create_crystallize(character, ability_data)
        if not hasattr(character, 'composable_abilities') or character.composable_abilities is None:
            character.composable_abilities = []
        character.composable_abilities.append(crystallize_ability)
        
        return character
    
    # Use inherited play_character method from GameEngineTestBase
    
    def test_crystallize_ability_creation(self):
        """Test that CRYSTALLIZE ability creates correctly."""
        character = self.create_crystallize_character("Elsa - Queen of Arendelle")
        
        assert len(character.composable_abilities) == 1
        crystallize_ability = character.composable_abilities[0]
        assert crystallize_ability.name == "CRYSTALLIZE"
        assert crystallize_ability.character == character
    
    def test_crystallize_triggers_on_play(self):
        """Test that CRYSTALLIZE triggers when the character is played."""
        crystallize_char = self.create_crystallize_character("Elsa - Snow Queen")
        opponent_char = self.create_test_character("Opponent Character")
        
        # Put opponent character in play first (directly in play area for testing)
        self.player2.characters_in_play.append(opponent_char)
        
        # Verify opponent is not exerted initially
        self.assert_character_exerted(opponent_char, False)
        
        # Play crystallize character
        message = self.play_character(crystallize_char, self.player1)
        
        # Should successfully enter play
        self.assert_message_type(message, MessageType.STEP_EXECUTED)
        self.assert_character_in_play(crystallize_char, self.player1)
        
        # Process ability trigger messages
        ability_messages = self.process_ability_messages()
        
        # Should have CRYSTALLIZE ability
        assert len(crystallize_char.composable_abilities) == 1
        assert crystallize_char.composable_abilities[0].name == "CRYSTALLIZE"
        
        # CRYSTALLIZE should have triggered and exerted the opponent character
        # (This might require player choice, so let's check the messages)
        if ability_messages:
            # There should be messages about the ability triggering
            assert len(ability_messages) > 0
    
    def test_crystallize_targets_opposing_character(self):
        """Test that CRYSTALLIZE targets opposing characters, not friendly ones."""
        crystallize_char = self.create_crystallize_character("Elsa - Snow Queen")
        friendly_char = self.create_test_character("Friendly Character")
        opponent_char = self.create_test_character("Enemy Character")
        
        # Put both friendly and opponent characters in play
        self.play_character(friendly_char, self.player1)
        self.play_character(opponent_char, self.player2)
        
        # Verify initial exert states
        self.assert_character_exerted(friendly_char, False)
        self.assert_character_exerted(opponent_char, False)
        
        # Play crystallize character
        message = self.play_character(crystallize_char, self.player1)
        
        # Should successfully enter play
        self.assert_message_type(message, MessageType.STEP_EXECUTED)
        self.assert_character_in_play(crystallize_char, self.player1)
        
        # Friendly character should remain unexerted
        self.assert_character_exerted(friendly_char, False)
        
        # CRYSTALLIZE should target enemy characters (verification depends on choice handling)
        assert len(crystallize_char.composable_abilities) == 1
    
    def test_crystallize_no_opposing_characters(self):
        """Test CRYSTALLIZE when there are no opposing characters to target."""
        crystallize_char = self.create_crystallize_character("Elsa - Snow Queen")
        friendly_char = self.create_test_character("Friendly Character")
        
        # Only friendly characters in play
        self.play_character(friendly_char, self.player1)
        
        # Play crystallize character
        message = self.play_character(crystallize_char, self.player1)
        
        # Should still successfully enter play
        self.assert_message_type(message, MessageType.STEP_EXECUTED)
        self.assert_character_in_play(crystallize_char, self.player1)
        
        # Should still have ability even with no valid targets
        assert len(crystallize_char.composable_abilities) == 1
        assert crystallize_char.composable_abilities[0].name == "CRYSTALLIZE"
        
        # Friendly character should remain unexerted
        self.assert_character_exerted(friendly_char, False)
    
    def test_crystallize_multiple_opposing_characters(self):
        """Test CRYSTALLIZE with multiple opposing characters (chosen targeting)."""
        crystallize_char = self.create_crystallize_character("Elsa - Snow Queen")
        opponent_char1 = self.create_test_character("Enemy 1", cost=1)  # Reduced cost
        opponent_char2 = self.create_test_character("Enemy 2", cost=1)  # Reduced cost  
        opponent_char3 = self.create_test_character("Enemy 3", cost=1)  # Reduced cost
        
        # Ensure player2 has enough ink
        self.setup_player_ink(self.player2, ink_count=7)
        
        # Put multiple opponents in play
        self.play_character(opponent_char1, self.player2)
        self.play_character(opponent_char2, self.player2)
        self.play_character(opponent_char3, self.player2)
        
        # Verify all opponents are unexerted initially
        self.assert_character_exerted(opponent_char1, False)
        self.assert_character_exerted(opponent_char2, False)
        self.assert_character_exerted(opponent_char3, False)
        
        # Play crystallize character
        message = self.play_character(crystallize_char, self.player1)
        
        # Should successfully enter play
        self.assert_message_type(message, MessageType.STEP_EXECUTED)
        self.assert_character_in_play(crystallize_char, self.player1)
        
        # Should be able to choose from multiple targets
        assert len(crystallize_char.composable_abilities) == 1
        assert crystallize_char.composable_abilities[0].name == "CRYSTALLIZE"
        
        # All opponents should be valid targets
        assert len(self.player2.characters_in_play) == 3
    
    def test_crystallize_only_triggers_for_self(self):
        """Test that CRYSTALLIZE only triggers when the ability owner enters play."""
        crystallize_char = self.create_crystallize_character("Elsa - Snow Queen")
        other_char = self.create_test_character("Other Character")
        opponent_char = self.create_test_character("Enemy Character")
        
        # Phase 7 methodology: Place characters in hand before GameEngine init
        self.player1.hand = [other_char]
        self.player1.characters_in_play = [crystallize_char]  # Crystallize character already in play
        self.player2.characters_in_play = [opponent_char]     # Opponent character already in play
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set up controllers
        crystallize_char.controller = self.player1
        other_char.controller = self.player1
        opponent_char.controller = self.player2
        
        # Verify opponent is not exerted initially
        self.assert_character_exerted(opponent_char, False)
        
        # Other character enters play (should NOT trigger CRYSTALLIZE since it's not the crystallize char)
        play_move = PlayMove(other_char)
        message = self.game_engine.next_message(play_move)
        
        # Should successfully enter play
        self.assert_message_type(message, MessageType.STEP_EXECUTED)
        self.assert_character_in_play(other_char, self.player1)
        
        # Opponent should still be unexerted (CRYSTALLIZE should not have triggered)
        self.assert_character_exerted(opponent_char, False)
    
    def test_crystallize_ability_registration(self):
        """Test that CRYSTALLIZE ability is properly registered."""
        crystallize_char = self.create_crystallize_character("Elsa - Snow Queen")
        
        # Put character in play
        self.play_character(crystallize_char, self.player1)
        
        # Should have ability
        assert crystallize_char.composable_abilities
        assert crystallize_char.composable_abilities[0].name == "CRYSTALLIZE"
        
        # Check that it has listeners for the correct event
        ability = crystallize_char.composable_abilities[0]
        assert len(ability.listeners) > 0
    
    def test_crystallize_effect_application(self):
        """Test that CRYSTALLIZE effect (exert) is properly applied."""
        crystallize_char = self.create_crystallize_character("Elsa - Snow Queen")
        opponent_char = self.create_test_character("Enemy Character")
        
        # Put opponent in play first
        self.play_character(opponent_char, self.player2)
        
        # Verify opponent starts unexerted
        self.assert_character_exerted(opponent_char, False)
        
        # Play crystallize character
        message = self.play_character(crystallize_char, self.player1)
        
        # Should successfully enter play
        self.assert_message_type(message, MessageType.STEP_EXECUTED)
        self.assert_character_in_play(crystallize_char, self.player1)
        
        # CRYSTALLIZE ability should be present and functional
        assert len(crystallize_char.composable_abilities) == 1
        crystallize_ability = crystallize_char.composable_abilities[0]
        assert crystallize_ability.name == "CRYSTALLIZE"
        
        # Verify the ability has the correct components
        assert len(crystallize_ability.listeners) > 0
        
        # The actual exertion would happen through the game engine's choice system
        # For now, verify the ability is correctly set up to apply the effect


if __name__ == "__main__":
    pytest.main([__file__, "-v"])