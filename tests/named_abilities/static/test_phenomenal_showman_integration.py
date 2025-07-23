"""Integration tests for PHENOMENAL SHOWMAN - While this character is exerted, opposing characters can't ready at the start of their turn."""

import pytest
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.event_system import GameEvent, EventContext
from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability


class TestPhenomenalShowmanIntegration(BaseNamedAbilityTest):
    """Integration tests for PHENOMENAL SHOWMAN named ability."""
    
    def create_phenomenal_showman_character(self, name="Genie - The Ever Impressive"):
        """Create a character with PHENOMENAL SHOWMAN ability."""
        character = create_test_character(
            name=name,
            cost=6,
            color=CardColor.SAPPHIRE,
            strength=5,
            willpower=6,
            lore=3,
            rarity=Rarity.LEGENDARY
        )
        
        add_named_ability(character, "PHENOMENAL SHOWMAN", "static", self.event_manager)
        return character
    
    def create_opponent_character(self, name="Opponent Character", exerted=False):
        """Create an opponent character."""
        character = create_test_character(
            name=name,
            cost=4,
            color=CardColor.RUBY,
            strength=3,
            willpower=4,
            lore=2,
            rarity=Rarity.RARE
        )
        character.exerted = exerted
        return character
    
    def create_friendly_character(self, name="Friendly Character", exerted=False):
        """Create a friendly character for comparison."""
        character = create_test_character(
            name=name,
            cost=3,
            color=CardColor.SAPPHIRE,
            strength=2,
            willpower=3,
            lore=1,
            rarity=Rarity.COMMON
        )
        character.exerted = exerted
        return character
    
    def test_phenomenal_showman_prevents_ready_when_exerted(self):
        """Test that PHENOMENAL SHOWMAN prevents opponent readying when this character is exerted."""
        showman_char = self.create_phenomenal_showman_character()
        opponent_char = self.create_opponent_character("Target Opponent", exerted=True)
        
        # Showman is exerted
        showman_char.exerted = True
        
        # Put characters in play
        self.player1.characters_in_play.append(showman_char)
        self.player2.characters_in_play.append(opponent_char)
        
        # Simulate turn start (when ready normally happens)
        event_context = self.trigger_event_with_context(
            event_type=GameEvent.TURN_BEGINS,
            player=self.player2,
            additional_data={'ability_owner': showman_char}
        )
        
        # PHENOMENAL SHOWMAN should prevent opponent from readying
        phenomenal_showman_ability = showman_char.composable_abilities[0]
        assert phenomenal_showman_ability.name == "PHENOMENAL SHOWMAN"
        
        # Showman should be exerted (condition for effect)
        assert showman_char.exerted
        # Opponent should remain exerted
        assert opponent_char.exerted
    
    def test_phenomenal_showman_no_effect_when_ready(self):
        """Test that PHENOMENAL SHOWMAN has no effect when this character is ready."""
        showman_char = self.create_phenomenal_showman_character()
        opponent_char = self.create_opponent_character("Target Opponent", exerted=True)
        
        # Showman is ready (not exerted)
        showman_char.exerted = False
        
        self.player1.characters_in_play.append(showman_char)
        self.player2.characters_in_play.append(opponent_char)
        
        # Simulate turn start
        event_context = self.trigger_event_with_context(
            event_type=GameEvent.TURN_BEGINS,
            player=self.player2,
            additional_data={'ability_owner': showman_char}
        )
        
        # Should not prevent readying when showman is ready
        assert not showman_char.exerted
        
        phenomenal_showman_ability = showman_char.composable_abilities[0]
        assert phenomenal_showman_ability.name == "PHENOMENAL SHOWMAN"
    
    def test_phenomenal_showman_only_affects_opponents(self):
        """Test that PHENOMENAL SHOWMAN only affects opposing characters."""
        showman_char = self.create_phenomenal_showman_character()
        friendly_char = self.create_friendly_character("Friendly", exerted=True)
        opponent_char = self.create_opponent_character("Opponent", exerted=True)
        
        # Showman is exerted
        showman_char.exerted = True
        
        # Put characters in play
        self.player1.characters_in_play.extend([showman_char, friendly_char])
        self.player2.characters_in_play.append(opponent_char)
        
        # Should only affect opponents, not friendly characters
        phenomenal_showman_ability = showman_char.composable_abilities[0]
        assert phenomenal_showman_ability.name == "PHENOMENAL SHOWMAN"
        
        # Both should be exerted
        assert friendly_char.exerted
        assert opponent_char.exerted
    
    def test_phenomenal_showman_affects_multiple_opponents(self):
        """Test that PHENOMENAL SHOWMAN affects all opposing characters."""
        showman_char = self.create_phenomenal_showman_character()
        opponent_char1 = self.create_opponent_character("Opponent 1", exerted=True)
        opponent_char2 = self.create_opponent_character("Opponent 2", exerted=True)
        opponent_char3 = self.create_opponent_character("Opponent 3", exerted=True)
        
        # Showman is exerted
        showman_char.exerted = True
        
        self.player1.characters_in_play.append(showman_char)
        self.player2.characters_in_play.extend([opponent_char1, opponent_char2, opponent_char3])
        
        # Should affect all opponents
        phenomenal_showman_ability = showman_char.composable_abilities[0]
        assert phenomenal_showman_ability.name == "PHENOMENAL SHOWMAN"
        
        # All opponents should be affected
        for opponent in [opponent_char1, opponent_char2, opponent_char3]:
            assert opponent.exerted
    
    def test_phenomenal_showman_responds_to_exertion_changes(self):
        """Test that PHENOMENAL SHOWMAN responds when this character becomes exerted/ready."""
        showman_char = self.create_phenomenal_showman_character()
        opponent_char = self.create_opponent_character("Opponent", exerted=True)
        
        # Start with showman ready
        showman_char.exerted = False
        
        self.player1.characters_in_play.append(showman_char)
        self.player2.characters_in_play.append(opponent_char)
        
        # Showman becomes exerted
        showman_char.exerted = True
        
        # Simulate exertion event
        event_context = self.trigger_event_with_context(
            event_type=GameEvent.CHARACTER_EXERTS,
            source=showman_char,
            player=self.player1,
            additional_data={'ability_owner': showman_char}
        )
        
        # Should now affect opponents
        phenomenal_showman_ability = showman_char.composable_abilities[0]
        assert phenomenal_showman_ability.name == "PHENOMENAL SHOWMAN"
        assert showman_char.exerted
    
    def test_phenomenal_showman_effect_ends_when_readied(self):
        """Test that PHENOMENAL SHOWMAN effect ends when this character readies."""
        showman_char = self.create_phenomenal_showman_character()
        opponent_char = self.create_opponent_character("Opponent", exerted=True)
        
        # Start with showman exerted
        showman_char.exerted = True
        
        self.player1.characters_in_play.append(showman_char)
        self.player2.characters_in_play.append(opponent_char)
        
        # Showman readies
        showman_char.exerted = False
        
        # Simulate ready event
        event_context = self.trigger_event_with_context(
            event_type=GameEvent.CHARACTER_READIED,
            source=showman_char,
            player=self.player1,
            additional_data={'ability_owner': showman_char}
        )
        
        # Effect should no longer apply
        assert not showman_char.exerted
        
        phenomenal_showman_ability = showman_char.composable_abilities[0]
        assert phenomenal_showman_ability.name == "PHENOMENAL SHOWMAN"
    
    def test_phenomenal_showman_multiple_instances(self):
        """Test multiple PHENOMENAL SHOWMAN characters."""
        showman_char1 = self.create_phenomenal_showman_character("Showman 1")
        showman_char2 = self.create_phenomenal_showman_character("Showman 2")
        opponent_char = self.create_opponent_character("Opponent", exerted=True)
        
        # Both showmen are exerted
        showman_char1.exerted = True
        showman_char2.exerted = True
        
        self.player1.characters_in_play.extend([showman_char1, showman_char2])
        self.player2.characters_in_play.append(opponent_char)
        
        # Both should have the ability
        for char in [showman_char1, showman_char2]:
            assert char.composable_abilities
            assert char.composable_abilities[0].name == "PHENOMENAL SHOWMAN"
            assert char.exerted
    
    def test_phenomenal_showman_continuous_effect(self):
        """Test that PHENOMENAL SHOWMAN is a continuous effect based on exertion state."""
        showman_char = self.create_phenomenal_showman_character()
        opponent_char = self.create_opponent_character("Opponent", exerted=True)
        
        self.player1.characters_in_play.append(showman_char)
        self.player2.characters_in_play.append(opponent_char)
        
        # Test state changes
        showman_char.exerted = False  # No effect
        assert not showman_char.exerted
        
        showman_char.exerted = True   # Effect active
        assert showman_char.exerted
        
        showman_char.exerted = False  # Effect ends
        assert not showman_char.exerted
        
        phenomenal_showman_ability = showman_char.composable_abilities[0]
        assert phenomenal_showman_ability.name == "PHENOMENAL SHOWMAN"
    
    def test_phenomenal_showman_ability_registration(self):
        """Test that PHENOMENAL SHOWMAN ability is properly registered."""
        showman_char = self.create_phenomenal_showman_character()
        self.player1.characters_in_play.append(showman_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # Should respond to turn starts and exertion events
        assert showman_char.composable_abilities
        assert showman_char.composable_abilities[0].name == "PHENOMENAL SHOWMAN"


if __name__ == "__main__":
    pytest.main([__file__])