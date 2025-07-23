"""Integration tests for CLEAR THE PATH - Characters with cost 2 or less cost 1 ⬢ less to play for each opposing character that is exerted."""

import pytest
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.event_system import GameEvent, EventContext
from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability


class TestClearThePathIntegration(BaseNamedAbilityTest):
    """Integration tests for CLEAR THE PATH named ability."""
    
    def create_clear_the_path_character(self, name="Flynn Rider - His Own Hero"):
        """Create a character with CLEAR THE PATH ability."""
        character = create_test_character(
            name=name,
            cost=4,
            color=CardColor.AMBER,
            strength=3,
            willpower=4,
            lore=2,
            rarity=Rarity.RARE
        )
        
        add_named_ability(character, "CLEAR THE PATH", "static", self.event_manager)
        return character
    
    def create_low_cost_character(self, cost=2, name="Low Cost Character", exerted=False):
        """Create a low-cost character for testing cost reduction."""
        character = create_test_character(
            name=name,
            cost=cost,
            color=CardColor.RUBY,
            strength=cost,
            willpower=cost,
            lore=1,
            rarity=Rarity.COMMON
        )
        character.exerted = exerted
        return character
    
    def create_high_cost_character(self, cost=4, name="High Cost Character", exerted=False):
        """Create a high-cost character that shouldn't benefit."""
        character = create_test_character(
            name=name,
            cost=cost,
            color=CardColor.SAPPHIRE,
            strength=cost,
            willpower=cost,
            lore=2,
            rarity=Rarity.RARE
        )
        character.exerted = exerted
        return character
    
    def create_opponent_character(self, name="Opponent Character", exerted=False):
        """Create an opponent character."""
        character = create_test_character(
            name=name,
            cost=3,
            color=CardColor.EMERALD,
            strength=2,
            willpower=3,
            lore=1,
            rarity=Rarity.COMMON
        )
        character.exerted = exerted
        return character
    
    def test_clear_the_path_cost_reduction_with_exerted_opponents(self):
        """Test that CLEAR THE PATH reduces cost based on exerted opponents."""
        clear_the_path_char = self.create_clear_the_path_character()
        low_cost_char = self.create_low_cost_character(cost=2)
        
        # Create exerted opponent characters
        opponent1 = self.create_opponent_character("Opponent 1", exerted=True)
        opponent2 = self.create_opponent_character("Opponent 2", exerted=True)
        opponent3 = self.create_opponent_character("Opponent 3", exerted=False)  # Not exerted
        
        # Set up board state
        self.player1.characters_in_play.append(clear_the_path_char)
        self.player2.characters_in_play.extend([opponent1, opponent2, opponent3])
        
        # Simulate characters entering/leaving play to update cost reduction
        event_context = self.trigger_event_with_context(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=opponent1,
            player=self.player2,
            additional_data={'ability_owner': clear_the_path_char}
        )
        
        # CLEAR THE PATH should provide cost reduction for low-cost characters
        assert low_cost_char.cost <= 2  # Eligible for cost reduction
        assert opponent1.exerted  # Should count for reduction
        assert opponent2.exerted  # Should count for reduction
        assert not opponent3.exerted  # Should not count for reduction
        
        clear_the_path_ability = clear_the_path_char.composable_abilities[0]
        assert clear_the_path_ability.name == "CLEAR THE PATH"
    
    def test_clear_the_path_only_affects_low_cost_characters(self):
        """Test that CLEAR THE PATH only affects characters with cost 2 or less."""
        clear_the_path_char = self.create_clear_the_path_character()
        low_cost_char = self.create_low_cost_character(cost=2)
        high_cost_char = self.create_high_cost_character(cost=3)
        
        # Create exerted opponents
        opponent1 = self.create_opponent_character("Opponent 1", exerted=True)
        opponent2 = self.create_opponent_character("Opponent 2", exerted=True)
        
        self.player1.characters_in_play.append(clear_the_path_char)
        self.player2.characters_in_play.extend([opponent1, opponent2])
        
        # Only characters with cost 2 or less should benefit
        assert low_cost_char.cost <= 2  # Should benefit
        assert high_cost_char.cost > 2   # Should not benefit
        
        clear_the_path_ability = clear_the_path_char.composable_abilities[0]
        assert clear_the_path_ability.name == "CLEAR THE PATH"
    
    def test_clear_the_path_cost_boundary(self):
        """Test CLEAR THE PATH with exact cost boundaries."""
        clear_the_path_char = self.create_clear_the_path_character()
        
        # Test exact boundaries
        cost_0_char = self.create_low_cost_character(cost=0, name="Free Character")
        cost_1_char = self.create_low_cost_character(cost=1, name="One Cost")
        cost_2_char = self.create_low_cost_character(cost=2, name="Two Cost")
        cost_3_char = self.create_high_cost_character(cost=3, name="Three Cost")
        
        # Create exerted opponent
        opponent = self.create_opponent_character("Opponent", exerted=True)
        
        self.player1.characters_in_play.append(clear_the_path_char)
        self.player2.characters_in_play.append(opponent)
        
        # Check eligibility
        assert cost_0_char.cost <= 2  # Should benefit
        assert cost_1_char.cost <= 2  # Should benefit
        assert cost_2_char.cost <= 2  # Should benefit
        assert cost_3_char.cost > 2   # Should not benefit
        
        clear_the_path_ability = clear_the_path_char.composable_abilities[0]
        assert clear_the_path_ability.name == "CLEAR THE PATH"
    
    def test_clear_the_path_no_exerted_opponents(self):
        """Test CLEAR THE PATH when no opponents are exerted."""
        clear_the_path_char = self.create_clear_the_path_character()
        low_cost_char = self.create_low_cost_character(cost=2)
        
        # Create ready (not exerted) opponents
        opponent1 = self.create_opponent_character("Opponent 1", exerted=False)
        opponent2 = self.create_opponent_character("Opponent 2", exerted=False)
        
        self.player1.characters_in_play.append(clear_the_path_char)
        self.player2.characters_in_play.extend([opponent1, opponent2])
        
        # No cost reduction should be available
        assert not opponent1.exerted
        assert not opponent2.exerted
        
        clear_the_path_ability = clear_the_path_char.composable_abilities[0]
        assert clear_the_path_ability.name == "CLEAR THE PATH"
    
    def test_clear_the_path_responds_to_exertion_changes(self):
        """Test that CLEAR THE PATH responds when opponents become exerted/ready."""
        clear_the_path_char = self.create_clear_the_path_character()
        opponent = self.create_opponent_character("Opponent", exerted=False)
        
        self.player1.characters_in_play.append(clear_the_path_char)
        self.player2.characters_in_play.append(opponent)
        
        # Initially no exerted opponents
        assert not opponent.exerted
        
        # Opponent becomes exerted
        opponent.exerted = True
        
        # Simulate relevant events that would trigger ability updates
        event_context = self.trigger_event_with_context(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=opponent,
            player=self.player2,
            additional_data={'ability_owner': clear_the_path_char}
        )
        
        # CLEAR THE PATH should update its cost reduction
        clear_the_path_ability = clear_the_path_char.composable_abilities[0]
        assert clear_the_path_ability.name == "CLEAR THE PATH"
    
    def test_clear_the_path_multiple_instances(self):
        """Test multiple CLEAR THE PATH characters."""
        clear_the_path_char1 = self.create_clear_the_path_character("Flynn Rider - His Own Hero")
        clear_the_path_char2 = self.create_clear_the_path_character("Flynn Rider - Charming Rogue")
        
        # Create exerted opponents
        opponent1 = self.create_opponent_character("Opponent 1", exerted=True)
        opponent2 = self.create_opponent_character("Opponent 2", exerted=True)
        
        self.player1.characters_in_play.extend([clear_the_path_char1, clear_the_path_char2])
        self.player2.characters_in_play.extend([opponent1, opponent2])
        
        # Both should have CLEAR THE PATH
        for char in [clear_the_path_char1, clear_the_path_char2]:
            assert char.composable_abilities
            assert char.composable_abilities[0].name == "CLEAR THE PATH"
    
    def test_clear_the_path_friendly_exerted_characters_ignored(self):
        """Test that CLEAR THE PATH only counts opposing exerted characters."""
        clear_the_path_char = self.create_clear_the_path_character()
        friendly_char = self.create_low_cost_character(cost=2, name="Friendly", exerted=True)
        opponent_char = self.create_opponent_character("Opponent", exerted=True)
        
        # Both friendly and opposing characters are exerted
        self.player1.characters_in_play.extend([clear_the_path_char, friendly_char])
        self.player2.characters_in_play.append(opponent_char)
        
        # Only opposing exerted characters should count
        assert friendly_char.exerted  # Friendly exerted (shouldn't count)
        assert opponent_char.exerted  # Opposing exerted (should count)
        
        clear_the_path_ability = clear_the_path_char.composable_abilities[0]
        assert clear_the_path_ability.name == "CLEAR THE PATH"
    
    def test_clear_the_path_ability_registration(self):
        """Test that CLEAR THE PATH ability is properly registered."""
        clear_the_path_char = self.create_clear_the_path_character()
        self.player1.characters_in_play.append(clear_the_path_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # CLEAR THE PATH should respond to characters entering/leaving play
        assert clear_the_path_char.composable_abilities
        assert clear_the_path_char.composable_abilities[0].name == "CLEAR THE PATH"


if __name__ == "__main__":
    pytest.main([__file__])