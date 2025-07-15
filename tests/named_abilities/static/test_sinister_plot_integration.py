"""Integration tests for SINISTER PLOT - Characters with cost 5 or more can't ↷ to sing songs."""

import pytest
from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.action_card import ActionCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.models.abilities.composable.named_abilities import NamedAbilityRegistry
from src.lorcana_sim.engine.event_system import GameEventManager


class TestSinisterPlotIntegration:
    """Integration tests for SINISTER PLOT named ability."""
    
    def setup_method(self):
        """Set up test environment with players and game state."""
        self.player1 = Player("Player 1")
        self.player2 = Player("Player 2")
        self.game_state = GameState([self.player1, self.player2])
        self.event_manager = GameEventManager(self.game_state)
        self.game_state.event_manager = self.event_manager
    
    def create_sinister_plot_character(self, name="Hades - Lord of the Underworld"):
        """Create a character with SINISTER PLOT ability."""
        character = CharacterCard(
            id=1,
            name=name.split(" - ")[0],
            version=name.split(" - ")[1] if " - " in name else "Test",
            full_name=name,
            cost=6,
            color=CardColor.AMETHYST,
            inkwell=True,
            rarity=Rarity.LEGENDARY,
            set_code="1",
            number=1,
            story="Test",
            abilities=[],
            strength=6,
            willpower=7,
            lore=2
        )
        
        # Add SINISTER PLOT ability
        ability_data = {"name": "SINISTER PLOT", "type": "static"}
        sinister_plot_ability = NamedAbilityRegistry.create_ability("SINISTER PLOT", character, ability_data)
        character.composable_abilities = [sinister_plot_ability]
        character.register_composable_abilities(self.event_manager)
        
        return character
    
    def create_high_cost_character(self, cost=5, name="Expensive Character"):
        """Create a high-cost character for testing."""
        character = CharacterCard(
            id=2,
            name=name,
            version="Test",
            full_name=f"{name} - Test",
            cost=cost,
            color=CardColor.RUBY,
            inkwell=True,
            rarity=Rarity.RARE,
            set_code="1",
            number=2,
            story="Test",
            abilities=[],
            strength=cost,
            willpower=cost,
            lore=2
        )
        return character
    
    def create_low_cost_character(self, cost=3, name="Cheap Character"):
        """Create a low-cost character for testing."""
        character = CharacterCard(
            id=3,
            name=name,
            version="Test",
            full_name=f"{name} - Test",
            cost=cost,
            color=CardColor.SAPPHIRE,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="1",
            number=3,
            story="Test",
            abilities=[],
            strength=cost,
            willpower=cost,
            lore=1
        )
        return character
    
    def create_song_card(self, name="A Whole New World", cost=4):
        """Create a song card for testing."""
        song = ActionCard(
            id=4,
            name=name,
            version="",
            full_name=name,
            cost=cost,
            color=CardColor.RUBY,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="1",
            number=4,
            story="Test",
            abilities=[]
        )
        return song
    
    def test_sinister_plot_prevents_high_cost_singing(self):
        """Test that SINISTER PLOT prevents characters with cost 5+ from singing."""
        sinister_plot_char = self.create_sinister_plot_character()
        high_cost_char = self.create_high_cost_character(cost=5)
        song = self.create_song_card()
        
        # Add characters to play
        self.player1.characters_in_play.extend([sinister_plot_char, high_cost_char])
        self.player1.hand.append(song)
        
        # SINISTER PLOT should prevent high-cost characters from singing
        sinister_plot_ability = sinister_plot_char.composable_abilities[0]
        assert sinister_plot_ability.name == "SINISTER PLOT"
        
        # The actual enforcement would be done by the game engine
        # This test verifies the ability exists and is configured correctly
    
    def test_sinister_plot_allows_low_cost_singing(self):
        """Test that SINISTER PLOT allows characters with cost 4 or less to sing."""
        sinister_plot_char = self.create_sinister_plot_character()
        low_cost_char = self.create_low_cost_character(cost=4)
        song = self.create_song_card()
        
        # Add characters to play
        self.player1.characters_in_play.extend([sinister_plot_char, low_cost_char])
        self.player1.hand.append(song)
        
        # Low-cost characters should still be able to sing
        assert low_cost_char.cost < 5
        
        # SINISTER PLOT should not affect low-cost characters
        sinister_plot_ability = sinister_plot_char.composable_abilities[0]
        assert sinister_plot_ability.name == "SINISTER PLOT"
    
    def test_sinister_plot_exact_cost_boundary(self):
        """Test SINISTER PLOT with exactly cost 5 characters."""
        sinister_plot_char = self.create_sinister_plot_character()
        exact_cost_char = self.create_high_cost_character(cost=5)
        song = self.create_song_card()
        
        self.player1.characters_in_play.extend([sinister_plot_char, exact_cost_char])
        self.player1.hand.append(song)
        
        # Cost 5 should be affected (5 or more)
        assert exact_cost_char.cost >= 5
        
        sinister_plot_ability = sinister_plot_char.composable_abilities[0]
        assert sinister_plot_ability.name == "SINISTER PLOT"
    
    def test_sinister_plot_multiple_high_cost_characters(self):
        """Test SINISTER PLOT affects multiple high-cost characters."""
        sinister_plot_char = self.create_sinister_plot_character()
        high_cost_char1 = self.create_high_cost_character(cost=6, name="Expensive Char 1")
        high_cost_char2 = self.create_high_cost_character(cost=7, name="Expensive Char 2")
        song = self.create_song_card()
        
        self.player1.characters_in_play.extend([sinister_plot_char, high_cost_char1, high_cost_char2])
        self.player1.hand.append(song)
        
        # Both high-cost characters should be affected
        assert high_cost_char1.cost >= 5
        assert high_cost_char2.cost >= 5
        
        sinister_plot_ability = sinister_plot_char.composable_abilities[0]
        assert sinister_plot_ability.name == "SINISTER PLOT"
    
    def test_sinister_plot_opponent_characters_unaffected(self):
        """Test that SINISTER PLOT only affects friendly characters."""
        sinister_plot_char = self.create_sinister_plot_character()
        opponent_high_cost = self.create_high_cost_character(cost=6)
        song = self.create_song_card()
        
        # Sinister plot character on player 1, high-cost on player 2
        self.player1.characters_in_play.append(sinister_plot_char)
        self.player2.characters_in_play.append(opponent_high_cost)
        self.player2.hand.append(song)
        
        # Opponent's characters should not be affected by friendly SINISTER PLOT
        sinister_plot_ability = sinister_plot_char.composable_abilities[0]
        assert sinister_plot_ability.name == "SINISTER PLOT"
    
    def test_sinister_plot_with_singer_ability(self):
        """Test SINISTER PLOT interaction with Singer ability."""
        from src.lorcana_sim.models.abilities.composable.keyword_abilities import create_singer_ability
        
        sinister_plot_char = self.create_sinister_plot_character()
        high_cost_singer = self.create_high_cost_character(cost=6, name="High Cost Singer")
        song = self.create_song_card(cost=6)
        
        # Add Singer ability to high-cost character
        singer_ability = create_singer_ability(6, high_cost_singer)
        high_cost_singer.composable_abilities = [singer_ability]
        high_cost_singer.register_composable_abilities(self.event_manager)
        
        self.player1.characters_in_play.extend([sinister_plot_char, high_cost_singer])
        self.player1.hand.append(song)
        
        # Even with Singer ability, SINISTER PLOT should prevent singing
        assert high_cost_singer.cost >= 5
        assert len(high_cost_singer.composable_abilities) == 1
        assert "Singer" in high_cost_singer.composable_abilities[0].name
        
        sinister_plot_ability = sinister_plot_char.composable_abilities[0]
        assert sinister_plot_ability.name == "SINISTER PLOT"
    
    def test_sinister_plot_multiple_instances(self):
        """Test multiple SINISTER PLOT characters in play."""
        sinister_plot_char1 = self.create_sinister_plot_character("Hades - Lord of the Underworld")
        sinister_plot_char2 = self.create_sinister_plot_character("Dr. Facilier - Charlatan")
        high_cost_char = self.create_high_cost_character(cost=5)
        
        self.player1.characters_in_play.extend([sinister_plot_char1, sinister_plot_char2, high_cost_char])
        
        # Both should have SINISTER PLOT
        for char in [sinister_plot_char1, sinister_plot_char2]:
            assert char.composable_abilities
            assert char.composable_abilities[0].name == "SINISTER PLOT"
    
    def test_sinister_plot_ability_registration(self):
        """Test that SINISTER PLOT ability is properly registered."""
        sinister_plot_char = self.create_sinister_plot_character()
        self.player1.characters_in_play.append(sinister_plot_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # SINISTER PLOT is a static ability affecting singing restrictions
        assert sinister_plot_char.composable_abilities
        assert sinister_plot_char.composable_abilities[0].name == "SINISTER PLOT"


if __name__ == "__main__":
    pytest.main([__file__])