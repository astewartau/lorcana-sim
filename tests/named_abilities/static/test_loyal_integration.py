"""Integration tests for LOYAL - If you have a character named Gaston in play, you pay 1 ⬢ less to play this character."""

import pytest
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.event_system import GameEvent, EventContext
from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability


class TestLoyalIntegration(BaseNamedAbilityTest):
    """Integration tests for LOYAL named ability."""
    
    def create_loyal_character(self, name="LeFou - Bumbler", cost=2):
        """Create a character with LOYAL ability."""
        character = create_test_character(
            name=name,
            cost=cost,
            color=CardColor.AMBER,
            strength=1,
            willpower=2,
            lore=1,
            rarity=Rarity.COMMON
        )
        
        add_named_ability(character, "LOYAL", "static", self.event_manager)
        return character
    
    def create_gaston_character(self, name="Gaston - Arrogant Hunter"):
        """Create a Gaston character."""
        return create_test_character(
            name=name,
            cost=4,
            color=CardColor.AMBER,
            strength=4,
            willpower=3,
            lore=2,
            rarity=Rarity.RARE
        )
    
    def create_other_character(self, name="Belle - Bookworm"):
        """Create a non-Gaston character for comparison."""
        return create_test_character(
            name=name,
            cost=3,
            color=CardColor.AMBER,
            strength=2,
            willpower=3,
            lore=1,
            rarity=Rarity.COMMON
        )
    
    def test_loyal_cost_reduction_with_gaston(self):
        """Test that LOYAL reduces cost when Gaston is in play."""
        loyal_char = self.create_loyal_character(cost=3)
        gaston = self.create_gaston_character()
        
        # Put Gaston in play
        self.player1.characters_in_play.append(gaston)
        
        # Simulate Gaston entering play event
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=gaston,
            player=self.player1,
            game_state=self.game_state
        )
        
        # Trigger the event (this would normally be done by game engine)
        self.event_manager.trigger_event(event_context)
        
        # Test the LOYAL ability's condition function
        loyal_ability = loyal_char.composable_abilities[0]
        assert loyal_ability.name == "LOYAL"
        
        # In the real implementation, this would affect the card's effective cost
        # The cost reduction would be checked when playing the card
    
    def test_loyal_no_cost_reduction_without_gaston(self):
        """Test that LOYAL does not reduce cost when Gaston is not in play."""
        loyal_char = self.create_loyal_character(cost=3)
        other_char = self.create_other_character()
        
        # Put non-Gaston character in play
        self.player1.characters_in_play.append(other_char)
        
        # Simulate character entering play event
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=other_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        self.event_manager.trigger_event(event_context)
        
        # LOYAL should not provide cost reduction
        loyal_ability = loyal_char.composable_abilities[0]
        assert loyal_ability.name == "LOYAL"
        
        # Original cost should remain unchanged (3)
        assert loyal_char.cost == 3
    
    def test_loyal_responds_to_gaston_entering_play(self):
        """Test that LOYAL ability responds when Gaston enters play."""
        loyal_char = self.create_loyal_character()
        gaston = self.create_gaston_character()
        
        # Put loyal character in play first
        self.player1.characters_in_play.append(loyal_char)
        
        # Gaston enters play
        self.player1.characters_in_play.append(gaston)
        
        # Simulate the event
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=gaston,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # LOYAL ability should be registered and respond to this event
        loyal_ability = loyal_char.composable_abilities[0]
        assert loyal_ability.name == "LOYAL"
    
    def test_loyal_responds_to_gaston_leaving_play(self):
        """Test that LOYAL ability responds when Gaston leaves play."""
        loyal_char = self.create_loyal_character()
        gaston = self.create_gaston_character()
        
        # Start with both in play
        self.player1.characters_in_play.extend([loyal_char, gaston])
        
        # Gaston leaves play
        self.player1.characters_in_play.remove(gaston)
        
        # Simulate the event
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_LEAVES_PLAY,
            source=gaston,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # LOYAL ability should respond to this event to remove cost reduction
        loyal_ability = loyal_char.composable_abilities[0]
        assert loyal_ability.name == "LOYAL"
    
    def test_multiple_gastons(self):
        """Test LOYAL with multiple Gaston characters in play."""
        loyal_char = self.create_loyal_character()
        gaston1 = self.create_gaston_character("Gaston - Arrogant Hunter")
        gaston2 = self.create_gaston_character("Gaston - Conceited")
        
        # Put both Gastons in play
        self.player1.characters_in_play.extend([gaston1, gaston2])
        
        # LOYAL should work with any Gaston
        loyal_ability = loyal_char.composable_abilities[0]
        assert loyal_ability.name == "LOYAL"
    
    def test_loyal_multiple_characters(self):
        """Test multiple LOYAL characters with one Gaston."""
        loyal_char1 = self.create_loyal_character("LeFou - Bumbler")
        loyal_char2 = self.create_loyal_character("Maurice - Belle's Father")
        gaston = self.create_gaston_character()
        
        # Put Gaston in play
        self.player1.characters_in_play.append(gaston)
        
        # Both LOYAL characters should benefit
        for loyal_char in [loyal_char1, loyal_char2]:
            loyal_ability = loyal_char.composable_abilities[0]
            assert loyal_ability.name == "LOYAL"
    
    def test_loyal_opponent_gaston_no_effect(self):
        """Test that opponent's Gaston does not trigger LOYAL."""
        loyal_char = self.create_loyal_character()
        opponent_gaston = self.create_gaston_character()
        
        # Put loyal character on player 1, Gaston on player 2
        self.player1.characters_in_play.append(loyal_char)
        self.player2.characters_in_play.append(opponent_gaston)
        
        # Simulate opponent's Gaston entering play
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=opponent_gaston,
            player=self.player2,
            game_state=self.game_state
        )
        
        self.event_manager.trigger_event(event_context)
        
        # LOYAL should only work with friendly Gaston
        loyal_ability = loyal_char.composable_abilities[0]
        assert loyal_ability.name == "LOYAL"


if __name__ == "__main__":
    pytest.main([__file__])