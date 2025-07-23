"""Integration tests for EXCEPTIONAL POWER - When you play this character, exert all opposing characters."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.exceptional_power import create_exceptional_power


class TestExceptionalPowerIntegration(GameEngineTestBase):
    """Integration tests for EXCEPTIONAL POWER named ability."""
    
    def create_exceptional_power_character(self, name="Power Character", cost=6, strength=4, willpower=6):
        """Create a test character with EXCEPTIONAL POWER ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            color=CardColor.RUBY,
            subtypes=["Hero"]
        )
        
        # Add the EXCEPTIONAL POWER ability
        ability_data = {"name": "EXCEPTIONAL POWER", "type": "triggered"}
        exceptional_power_ability = create_exceptional_power(character, ability_data)
        if not hasattr(character, 'composable_abilities') or character.composable_abilities is None:
            character.composable_abilities = []
        character.composable_abilities.append(exceptional_power_ability)
        return character
    
    def test_exceptional_power_creation(self):
        """Unit test: Verify EXCEPTIONAL POWER ability creates correctly."""
        character = self.create_exceptional_power_character()
        
        assert len(character.composable_abilities) == 1
        ability = character.composable_abilities[0]
        assert "EXCEPTIONAL POWER" in ability.name
    
    def test_exceptional_power_exerts_all_opposing_characters(self):
        """Integration test: EXCEPTIONAL POWER exerts all opposing characters when played."""
        # Create character with EXCEPTIONAL POWER ability
        power_character = self.create_exceptional_power_character(
            name="Power Character", 
            cost=6, 
            strength=4,
            willpower=5
        )
        
        # Create multiple opposing characters (all ready initially)
        opponent1 = self.create_test_character(
            name="Opponent 1",
            strength=2,
            willpower=3
        )
        opponent2 = self.create_test_character(
            name="Opponent 2",
            strength=3,
            willpower=2
        )
        opponent3 = self.create_test_character(
            name="Opponent 3",
            strength=1,
            willpower=4
        )
        
        # Set up game state - use proper infrastructure  
        self.setup_player_ink(self.player1, ink_count=7)
        self.setup_player_ink(self.player2, ink_count=7)
        
        # Play all three opponents directly by adding them to player2's characters in play
        # This bypasses the potentially buggy play_character method for setup
        self.player2.characters_in_play.extend([opponent1, opponent2, opponent3])
        
        # Make all opponent characters ready (not exerted)
        opponent1.exerted = False
        opponent2.exerted = False
        opponent3.exerted = False
        
        # Set controllers
        power_character.controller = self.player1
        opponent1.controller = self.player2
        opponent2.controller = self.player2
        opponent3.controller = self.player2
        
        # Verify initial states - all opponents are ready
        assert not opponent1.exerted
        assert not opponent2.exerted
        assert not opponent3.exerted
        
        # Play the power character using proper infrastructure
        message = self.play_character(power_character, self.player1)
        
        # Verify the character was played
        assert message.type == MessageType.STEP_EXECUTED
        # Verify character was played
        assert message.type == MessageType.STEP_EXECUTED
        assert power_character in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Get the effect execution message
        # All three exertions happen in one TargetedEffect execution
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify all opponents are now exerted
        assert opponent1.exerted, "Opponent 1 should be exerted"
        assert opponent2.exerted, "Opponent 2 should be exerted"
        assert opponent3.exerted, "Opponent 3 should be exerted"
        
        # Verify power character itself is not affected
        assert not power_character.exerted, "Power character should remain ready"
    
    def test_exceptional_power_with_no_opposing_characters(self):
        """Test EXCEPTIONAL POWER when no opposing characters are in play."""
        # Create character with EXCEPTIONAL POWER ability
        power_character = self.create_exceptional_power_character(
            name="Power Character"
        )
        
        # Set up game state with no opponent characters
        self.setup_player_ink(self.player1, ink_count=7)
        # No opponent characters needed for this test
        
        # Set controller
        power_character.controller = self.player1
        
        # Play the power character using proper infrastructure
        message = self.play_character(power_character, self.player1)
        
        # Verify the character was played
        assert message.type == MessageType.STEP_EXECUTED
        assert power_character in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # No effect should occur since no opposing characters exist
        # Power character should remain ready
        assert not power_character.exerted
    
    def test_exceptional_power_with_already_exerted_opponents(self):
        """Test EXCEPTIONAL POWER with opponents that are already exerted."""
        # Create character with EXCEPTIONAL POWER ability
        power_character = self.create_exceptional_power_character(
            name="Power Character"
        )
        
        # Create opposing characters that are already exerted
        exerted_opponent1 = self.create_test_character(name="Already Exerted 1")
        exerted_opponent2 = self.create_test_character(name="Already Exerted 2")
        ready_opponent = self.create_test_character(name="Ready Opponent")
        
        # Set up game state
        self.setup_player_ink(self.player1, ink_count=7)
        self.setup_player_ink(self.player2, ink_count=7)
        
        # Add characters to player2's characters in play
        self.player2.characters_in_play.extend([exerted_opponent1, exerted_opponent2, ready_opponent])
        
        # Set initial exerted states
        exerted_opponent1.exerted = True   # Already exerted
        exerted_opponent2.exerted = True   # Already exerted
        ready_opponent.exerted = False     # Ready
        
        # Set controllers
        power_character.controller = self.player1
        exerted_opponent1.controller = self.player2
        exerted_opponent2.controller = self.player2
        ready_opponent.controller = self.player2
        
        # Play the power character using proper infrastructure
        message = self.play_character(power_character, self.player1)
        
        # Verify the character was played
        assert message.type == MessageType.STEP_EXECUTED
        assert power_character in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Get the effect execution message
        # All exertions happen in one TargetedEffect execution
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify all opponents are exerted (already exerted ones remain exerted, ready one becomes exerted)
        assert exerted_opponent1.exerted, "Already exerted opponent 1 should remain exerted"
        assert exerted_opponent2.exerted, "Already exerted opponent 2 should remain exerted"
        assert ready_opponent.exerted, "Ready opponent should now be exerted"
    
    def test_exceptional_power_with_mixed_opponent_states(self):
        """Test EXCEPTIONAL POWER with opponents in various states."""
        # Create character with EXCEPTIONAL POWER ability
        power_character = self.create_exceptional_power_character(
            name="Power Character"
        )
        
        # Create opponents with different properties
        ready_strong = self.create_test_character(
            name="Ready Strong",
            strength=5,
            willpower=4
        )
        exerted_weak = self.create_test_character(
            name="Exerted Weak", 
            strength=1,
            willpower=1
        )
        damaged_ready = self.create_test_character(
            name="Damaged Ready",
            strength=2,
            willpower=3
        )
        
        # Apply damage to the damaged character
        damaged_ready.damage = 1
        
        # Set up game state
        self.setup_player_ink(self.player1, ink_count=7)
        self.setup_player_ink(self.player2, ink_count=7)
        
        # Add characters to player2's characters in play
        self.player2.characters_in_play.extend([ready_strong, exerted_weak, damaged_ready])
        
        # Set initial states
        ready_strong.exerted = False
        exerted_weak.exerted = True
        damaged_ready.exerted = False
        
        # Set controllers
        power_character.controller = self.player1
        for opponent in [ready_strong, exerted_weak, damaged_ready]:
            opponent.controller = self.player2
        
        # Play the power character using proper infrastructure
        message = self.play_character(power_character, self.player1)
        
        # Verify the character was played
        assert message.type == MessageType.STEP_EXECUTED
        assert power_character in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Get the effect execution message
        # All exertions happen in one TargetedEffect execution
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify all opponents are now exerted, regardless of their other properties
        assert ready_strong.exerted, "Ready strong opponent should be exerted"
        assert exerted_weak.exerted, "Already exerted weak opponent should remain exerted"
        assert damaged_ready.exerted, "Damaged ready opponent should be exerted"
        
        # Verify other properties are unchanged
        assert ready_strong.damage == 0, "Strong opponent should have no damage"
        assert damaged_ready.damage == 1, "Damaged opponent should retain damage"
    
    def test_exceptional_power_does_not_affect_friendly_characters(self):
        """Test that EXCEPTIONAL POWER only affects opposing characters, not friendly ones."""
        # Create character with EXCEPTIONAL POWER ability
        power_character = self.create_exceptional_power_character(
            name="Power Character"
        )
        
        # Create friendly characters
        friendly1 = self.create_test_character(name="Friendly 1")
        friendly2 = self.create_test_character(name="Friendly 2")
        
        # Create opposing characters
        opponent1 = self.create_test_character(name="Opponent 1")
        opponent2 = self.create_test_character(name="Opponent 2")
        
        # Set up game state
        self.setup_player_ink(self.player1, ink_count=7)
        self.setup_player_ink(self.player2, ink_count=7)
        
        # Add characters to their respective players
        self.player1.characters_in_play.extend([friendly1, friendly2])
        self.player2.characters_in_play.extend([opponent1, opponent2])
        
        # Make all characters ready initially
        friendly1.exerted = False
        friendly2.exerted = False
        opponent1.exerted = False
        opponent2.exerted = False
        
        # Set controllers
        power_character.controller = self.player1
        friendly1.controller = self.player1
        friendly2.controller = self.player1
        opponent1.controller = self.player2
        opponent2.controller = self.player2
        
        # Play the power character using proper infrastructure
        message = self.play_character(power_character, self.player1)
        
        # Verify the character was played
        assert message.type == MessageType.STEP_EXECUTED
        assert power_character in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Get effect messages for each opponent
        effect_messages = []
        for _ in range(2):  # Two opponent characters
            effect_message = self.game_engine.next_message()
            effect_messages.append(effect_message)
        
        # Verify only opponent characters are exerted
        assert not friendly1.exerted, "Friendly 1 should remain ready"
        assert not friendly2.exerted, "Friendly 2 should remain ready"
        assert not power_character.exerted, "Power character should remain ready"
        
        # Verify opponent characters are exerted
        assert opponent1.exerted, "Opponent 1 should be exerted"
        assert opponent2.exerted, "Opponent 2 should be exerted"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])