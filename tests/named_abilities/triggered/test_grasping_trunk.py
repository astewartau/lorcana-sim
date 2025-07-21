"""Integration tests for GRASPING TRUNK - When this character quests, gain lore equal to the lore value of chosen opposing character."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, QuestMove, ChoiceMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.grasping_trunk import create_grasping_trunk


class TestGraspingTrunkIntegration(GameEngineTestBase):
    """Integration tests for GRASPING TRUNK named ability."""
    
    def create_grasping_trunk_character(self, name="Trunk Character", cost=3, strength=2, willpower=3, lore=1):
        """Create a test character with GRASPING TRUNK ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            lore=lore,
            subtypes=["Animal"]
        )
        
        # Add the GRASPING TRUNK ability
        ability_data = {"name": "GRASPING TRUNK", "type": "triggered"}
        grasping_trunk_ability = create_grasping_trunk(character, ability_data)
        character.composable_abilities = [grasping_trunk_ability]
        
        return character
    
    def test_grasping_trunk_creation(self):
        """Unit test: Verify GRASPING TRUNK ability creates correctly."""
        character = self.create_grasping_trunk_character()
        
        assert len(character.composable_abilities) == 1
        ability = character.composable_abilities[0]
        assert "GRASPING TRUNK" in ability.name
    
    def test_grasping_trunk_gains_lore_from_chosen_opponent(self):
        """Integration test: GRASPING TRUNK gains lore equal to chosen opponent's lore when questing."""
        # Create character with GRASPING TRUNK ability
        trunk_character = self.create_grasping_trunk_character(
            name="Trunk Character", 
            cost=4,
            lore=2
        )
        
        # Create opponent characters with different lore values
        opponent_high_lore = self.create_test_character(
            name="High Lore Opponent",
            lore=3
        )
        opponent_low_lore = self.create_test_character(
            name="Low Lore Opponent", 
            lore=1
        )
        
        # Set up game state
        self.player1.characters_in_play = [trunk_character]
        self.player2.characters_in_play = [opponent_high_lore, opponent_low_lore]
        
        # Make trunk character ready to quest
        trunk_character.exerted = False
        trunk_character.is_dry = True
        trunk_character.controller = self.player1
        
        # Set opponent controllers
        opponent_high_lore.controller = self.player2
        opponent_low_lore.controller = self.player2
        
        # Record initial lore
        initial_player_lore = self.player1.lore
        
        # Quest with the trunk character
        quest_move = QuestMove(trunk_character)
        quest_message = self.game_engine.next_message(quest_move)
        
        # Verify quest occurred
        assert quest_message.type == MessageType.STEP_EXECUTED
        # Verify quest action occurred
        assert quest_message.type == MessageType.STEP_EXECUTED
        
        # Should gain normal lore from questing first
        assert self.player1.lore == initial_player_lore + trunk_character.lore
        
        # Get the GRASPING TRUNK trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Should get a choice message for which opponent to target
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        # Verify choice message
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        # Choose the high lore opponent (assume index 0)
        target_choice = ChoiceMove(choice_index=0)  # Choose first opponent
        choice_result = self.game_engine.next_message(target_choice)
        
        # Get the effect message
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        # Verify effect message
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify additional lore was gained equal to chosen opponent's lore
        expected_total_lore = initial_player_lore + trunk_character.lore + opponent_high_lore.lore
        assert self.player1.lore == expected_total_lore
    
    def test_grasping_trunk_with_different_lore_values(self):
        """Test GRASPING TRUNK with opponents having various lore values."""
        # Create character with GRASPING TRUNK ability
        trunk_character = self.create_grasping_trunk_character(
            name="Trunk Character",
            lore=1
        )
        
        # Create opponents with different lore values
        zero_lore_opponent = self.create_test_character(
            name="Zero Lore Opponent",
            lore=0
        )
        high_lore_opponent = self.create_test_character(
            name="High Lore Opponent",
            lore=4
        )
        
        # Set up game state
        self.player1.characters_in_play = [trunk_character]
        self.player2.characters_in_play = [zero_lore_opponent, high_lore_opponent]
        
        trunk_character.exerted = False
        trunk_character.is_dry = True
        trunk_character.controller = self.player1
        
        zero_lore_opponent.controller = self.player2
        high_lore_opponent.controller = self.player2
        
        # Record initial lore
        initial_player_lore = self.player1.lore
        
        # Quest with trunk character
        quest_move = QuestMove(trunk_character)
        quest_message = self.game_engine.next_message(quest_move)
        
        # Process normal quest lore gain
        normal_lore_gained = trunk_character.lore
        
        # Get trigger and choice messages
        trigger_message = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        # Choose the high lore opponent
        target_choice = ChoiceMove(choice_index=1)  # Assume second choice is high lore
        choice_result = self.game_engine.next_message(target_choice)
        
        # Get effect message
        effect_message = self.game_engine.next_message()
        
        # Verify total lore gain
        expected_total = initial_player_lore + normal_lore_gained + high_lore_opponent.lore
        assert self.player1.lore == expected_total
    
    def test_grasping_trunk_with_no_opposing_characters(self):
        """Test GRASPING TRUNK when no opposing characters are in play."""
        # Create character with GRASPING TRUNK ability
        trunk_character = self.create_grasping_trunk_character(
            name="Trunk Character"
        )
        
        # Set up game state with no opponents
        self.player1.characters_in_play = [trunk_character]
        self.player2.characters_in_play = []  # No opponents
        
        trunk_character.exerted = False
        trunk_character.is_dry = True
        trunk_character.controller = self.player1
        
        # Record initial lore
        initial_player_lore = self.player1.lore
        
        # Quest with trunk character
        quest_move = QuestMove(trunk_character)
        quest_message = self.game_engine.next_message(quest_move)
        
        # Should still get normal quest lore
        assert self.player1.lore == initial_player_lore + trunk_character.lore
        
        # Get trigger message
        trigger_message = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Should not get a choice message since no valid targets
        # Or should get a message indicating no valid targets
        # The exact behavior depends on implementation
    
    def test_grasping_trunk_with_multiple_quests(self):
        """Test GRASPING TRUNK triggers multiple times with multiple quests."""
        # Create multiple characters with GRASPING TRUNK
        trunk_character1 = self.create_grasping_trunk_character(
            name="Trunk Character 1",
            lore=1
        )
        trunk_character2 = self.create_grasping_trunk_character(
            name="Trunk Character 2",
            lore=2
        )
        
        # Create opponent
        opponent = self.create_test_character(
            name="Opponent",
            lore=2
        )
        
        # Set up game state
        self.player1.characters_in_play = [trunk_character1, trunk_character2]
        self.player2.characters_in_play = [opponent]
        
        # Make both characters ready to quest
        trunk_character1.exerted = False
        trunk_character1.is_dry = True
        trunk_character2.exerted = False
        trunk_character2.is_dry = True
        
        trunk_character1.controller = self.player1
        trunk_character2.controller = self.player1
        opponent.controller = self.player2
        
        # Record initial lore
        initial_lore = self.player1.lore
        
        # Quest with first character
        quest_move1 = QuestMove(trunk_character1)
        quest_message1 = self.game_engine.next_message(quest_move1)
        
        # Process first quest
        trigger_message1 = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message1.event_data is not None or trigger_message1.step is not None
        
        choice_message1 = self.game_engine.next_message()
        assert choice_message1.type == MessageType.CHOICE_REQUIRED
        
        target_choice1 = ChoiceMove(choice_index=0)
        choice_result1 = self.game_engine.next_message(target_choice1)
        
        effect_message1 = self.game_engine.next_message()
        
        # Verify first quest results
        expected_after_first = initial_lore + trunk_character1.lore + opponent.lore
        assert self.player1.lore == expected_after_first
        
        # Quest with second character
        quest_move2 = QuestMove(trunk_character2)
        quest_message2 = self.game_engine.next_message(quest_move2)
        
        # Process second quest
        trigger_message2 = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message2.event_data is not None or trigger_message2.step is not None
        
        choice_message2 = self.game_engine.next_message()
        target_choice2 = ChoiceMove(choice_index=0)
        choice_result2 = self.game_engine.next_message(target_choice2)
        
        effect_message2 = self.game_engine.next_message()
        
        # Verify total lore after both quests
        expected_final = expected_after_first + trunk_character2.lore + opponent.lore
        assert self.player1.lore == expected_final
    
    def test_grasping_trunk_does_not_trigger_on_other_character_quest(self):
        """Test that GRASPING TRUNK only triggers when the character with the ability quests."""
        # Create character with GRASPING TRUNK ability
        trunk_character = self.create_grasping_trunk_character(
            name="Trunk Character"
        )
        
        # Create normal character without ability
        normal_character = self.create_test_character(
            name="Normal Character",
            lore=1
        )
        
        # Create opponent
        opponent = self.create_test_character(
            name="Opponent",
            lore=3
        )
        
        # Set up game state
        self.player1.characters_in_play = [trunk_character, normal_character]
        self.player2.characters_in_play = [opponent]
        
        # Make normal character ready to quest, trunk character not ready
        trunk_character.exerted = True     # Can't quest
        normal_character.exerted = False   # Can quest
        normal_character.is_dry = True
        
        trunk_character.controller = self.player1
        normal_character.controller = self.player1
        opponent.controller = self.player2
        
        # Record initial lore
        initial_lore = self.player1.lore
        
        # Quest with normal character (not the trunk character)
        quest_move = QuestMove(normal_character)
        quest_message = self.game_engine.next_message(quest_move)
        
        # Should get normal quest lore only
        assert self.player1.lore == initial_lore + normal_character.lore
        
        # GRASPING TRUNK should NOT trigger
        # No additional lore should be gained
        # (No trigger message or choice should appear)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])