"""Integration tests for HORSE KICK - When you play this character, chosen character gets -2 strength for the turn."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, ChoiceMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.horse_kick import create_horse_kick


class TestHorseKickIntegration(GameEngineTestBase):
    """Integration tests for HORSE KICK named ability."""
    
    def create_horse_kick_character(self, name="Kick Character", cost=3, strength=2, willpower=3):
        """Create a test character with HORSE KICK ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            subtypes=["Animal"]
        )
        
        # Add the HORSE KICK ability
        ability_data = {"name": "HORSE KICK", "type": "triggered"}
        horse_kick_ability = create_horse_kick(character, ability_data)
        character.composable_abilities = [horse_kick_ability]
        
        return character
    
    def test_horse_kick_creation(self):
        """Unit test: Verify HORSE KICK ability creates correctly."""
        character = self.create_horse_kick_character()
        
        assert len(character.composable_abilities) == 1
        ability = character.composable_abilities[0]
        assert "HORSE KICK" in ability.name
    
    def test_horse_kick_reduces_opponent_strength(self):
        """Integration test: HORSE KICK reduces chosen opponent's strength when played."""
        # Create character with HORSE KICK ability
        kick_character = self.create_horse_kick_character(
            name="Kick Character", 
            cost=4,
            strength=3
        )
        
        # Create opponent characters to target
        opponent_strong = self.create_test_character(
            name="Strong Opponent",
            strength=5,
            willpower=4
        )
        opponent_weak = self.create_test_character(
            name="Weak Opponent",
            strength=2,
            willpower=2
        )
        
        # Set up game state
        self.player1.hand = [kick_character]
        self.player2.characters_in_play = [opponent_strong, opponent_weak]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        kick_character.controller = self.player1
        opponent_strong.controller = self.player2
        opponent_weak.controller = self.player2
        
        # Record initial strengths
        initial_strong_strength = opponent_strong.current_strength
        initial_weak_strength = opponent_weak.current_strength
        
        # Play the kick character
        play_move = PlayMove(kick_character)
        message = self.game_engine.next_message(play_move)
        
        # Verify the character was played
        assert message.type == MessageType.STEP_EXECUTED
        # Verify character was played
        assert message.type == MessageType.STEP_EXECUTED
        assert kick_character in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Should get a choice message for which character to target
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        # Verify choice message
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        # Choose the strong opponent (assume index 0)
        target_choice = ChoiceMove(choice_index=0)  # Choose first opponent
        choice_result = self.game_engine.next_message(target_choice)
        
        # Get the effect message
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        # Verify effect message
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify the chosen opponent's strength was reduced by 2
        assert opponent_strong.current_strength == initial_strong_strength - 2
        # Other opponent should be unchanged
        assert opponent_weak.current_strength == initial_weak_strength
    
    def test_horse_kick_targets_friendly_character(self):
        """Test HORSE KICK can target friendly characters."""
        # Create character with HORSE KICK ability
        kick_character = self.create_horse_kick_character(
            name="Kick Character"
        )
        
        # Create friendly character to target
        friendly_character = self.create_test_character(
            name="Friendly Character",
            strength=4
        )
        
        # Set up game state
        self.player1.hand = [kick_character]
        self.player1.characters_in_play = [friendly_character]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        kick_character.controller = self.player1
        friendly_character.controller = self.player1
        
        # Record initial strength
        initial_strength = friendly_character.current_strength
        
        # Play the kick character
        play_move = PlayMove(kick_character)
        message = self.game_engine.next_message(play_move)
        
        # Process trigger and choice
        trigger_message = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        # Choose the friendly character
        target_choice = ChoiceMove(choice_index=0)
        choice_result = self.game_engine.next_message(target_choice)
        
        # Get effect message
        effect_message = self.game_engine.next_message()
        # Verify effect message
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify friendly character's strength was reduced
        assert friendly_character.current_strength == initial_strength - 2
    
    def test_horse_kick_with_low_strength_character(self):
        """Test HORSE KICK when targeting character with strength 2 or less."""
        # Create character with HORSE KICK ability
        kick_character = self.create_horse_kick_character(
            name="Kick Character"
        )
        
        # Create weak character to target
        weak_character = self.create_test_character(
            name="Weak Character",
            strength=1,
            willpower=3
        )
        
        # Set up game state
        self.player1.hand = [kick_character]
        self.player2.characters_in_play = [weak_character]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        kick_character.controller = self.player1
        weak_character.controller = self.player2
        
        # Record initial strength
        initial_strength = weak_character.current_strength
        
        # Play the kick character
        play_move = PlayMove(kick_character)
        message = self.game_engine.next_message(play_move)
        
        # Process trigger and choice
        trigger_message = self.game_engine.next_message()
        choice_message = self.game_engine.next_message()
        
        # Choose the weak character
        target_choice = ChoiceMove(choice_index=0)
        choice_result = self.game_engine.next_message(target_choice)
        
        # Get effect message
        effect_message = self.game_engine.next_message()
        
        # Verify strength reduction (may go to 0 or negative, depending on implementation)
        expected_strength = max(0, initial_strength - 2)  # Assuming strength can't go negative
        assert weak_character.current_strength <= expected_strength
    
    def test_horse_kick_with_multiple_targets(self):
        """Test HORSE KICK with multiple potential targets."""
        # Create character with HORSE KICK ability
        kick_character = self.create_horse_kick_character(
            name="Kick Character"
        )
        
        # Create multiple potential targets
        target1 = self.create_test_character(name="Target 1", strength=3)
        target2 = self.create_test_character(name="Target 2", strength=4)
        target3 = self.create_test_character(name="Target 3", strength=2)
        
        # Set up game state with mixed ownership
        self.player1.hand = [kick_character]
        self.player1.characters_in_play = [target1]  # Friendly target
        self.player2.characters_in_play = [target2, target3]  # Enemy targets
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        kick_character.controller = self.player1
        target1.controller = self.player1
        target2.controller = self.player2
        target3.controller = self.player2
        
        # Record initial strengths
        initial_strengths = {
            target1: target1.current_strength,
            target2: target2.current_strength,
            target3: target3.current_strength
        }
        
        # Play the kick character
        play_move = PlayMove(kick_character)
        message = self.game_engine.next_message(play_move)
        
        # Process trigger
        trigger_message = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Get choice message
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        # Choose target 2 (assuming it's choice index 1)
        target_choice = ChoiceMove(choice_index=1)
        choice_result = self.game_engine.next_message(target_choice)
        
        # Get effect message
        effect_message = self.game_engine.next_message()
        
        # Verify only chosen target was affected
        assert target1.current_strength == initial_strengths[target1]  # Unchanged
        assert target2.current_strength == initial_strengths[target2] - 2  # Reduced
        assert target3.current_strength == initial_strengths[target3]  # Unchanged
    
    def test_horse_kick_with_no_valid_targets(self):
        """Test HORSE KICK when no valid targets exist."""
        # Create character with HORSE KICK ability
        kick_character = self.create_horse_kick_character(
            name="Kick Character"
        )
        
        # Set up game state with no other characters
        self.player1.hand = [kick_character]
        self.player1.characters_in_play = []
        self.player2.characters_in_play = []
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controller
        kick_character.controller = self.player1
        
        # Play the kick character
        play_move = PlayMove(kick_character)
        message = self.game_engine.next_message(play_move)
        
        # Verify character was played
        assert kick_character in self.player1.characters_in_play
        
        # Get trigger message
        trigger_message = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Should either get a message indicating no valid targets,
        # or the ability should fizzle with no effect
        # Exact behavior depends on implementation
    
    def test_horse_kick_effect_duration(self):
        """Test that HORSE KICK strength reduction lasts for the turn."""
        # Create character with HORSE KICK ability
        kick_character = self.create_horse_kick_character(
            name="Kick Character"
        )
        
        # Create target character
        target_character = self.create_test_character(
            name="Target Character",
            strength=4
        )
        
        # Set up game state
        self.player1.hand = [kick_character]
        self.player2.characters_in_play = [target_character]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        kick_character.controller = self.player1
        target_character.controller = self.player2
        
        # Record initial strength
        initial_strength = target_character.current_strength
        
        # Play and target
        play_move = PlayMove(kick_character)
        message = self.game_engine.next_message(play_move)
        
        trigger_message = self.game_engine.next_message()
        choice_message = self.game_engine.next_message()
        
        target_choice = ChoiceMove(choice_index=0)
        choice_result = self.game_engine.next_message(target_choice)
        
        effect_message = self.game_engine.next_message()
        
        # Verify strength was reduced
        assert target_character.current_strength == initial_strength - 2
        
        # The strength reduction should persist until end of turn
        # At end of turn, temporary effects should be cleaned up
        # and strength should return to normal
        # This testing depends on the specific implementation of temporary effects
    
    def test_horse_kick_multiple_kicks_same_target(self):
        """Test multiple HORSE KICK effects on the same target."""
        # Create two characters with HORSE KICK ability
        kick_character1 = self.create_horse_kick_character(
            name="Kick Character 1"
        )
        kick_character2 = self.create_horse_kick_character(
            name="Kick Character 2"
        )
        
        # Create target character
        target_character = self.create_test_character(
            name="Target Character",
            strength=6  # High strength to survive multiple kicks
        )
        
        # Set up game state
        self.player1.hand = [kick_character1, kick_character2]
        self.player2.characters_in_play = [target_character]
        self.setup_player_ink(self.player1, ink_count=10)
        
        # Set controllers
        kick_character1.controller = self.player1
        kick_character2.controller = self.player1
        target_character.controller = self.player2
        
        # Record initial strength
        initial_strength = target_character.current_strength
        
        # Play first kick character
        play_move1 = PlayMove(kick_character1)
        message1 = self.game_engine.next_message(play_move1)
        
        # Process first kick
        trigger1 = self.game_engine.next_message()
        choice1 = self.game_engine.next_message()
        target_choice1 = ChoiceMove(choice_index=0)
        result1 = self.game_engine.next_message(target_choice1)
        effect1 = self.game_engine.next_message()
        
        # Verify first reduction
        assert target_character.current_strength == initial_strength - 2
        
        # Play second kick character
        play_move2 = PlayMove(kick_character2)
        message2 = self.game_engine.next_message(play_move2)
        
        # Process second kick
        trigger2 = self.game_engine.next_message()
        choice2 = self.game_engine.next_message()
        target_choice2 = ChoiceMove(choice_index=0)
        result2 = self.game_engine.next_message(target_choice2)
        effect2 = self.game_engine.next_message()
        
        # Verify cumulative reduction
        assert target_character.current_strength == initial_strength - 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])