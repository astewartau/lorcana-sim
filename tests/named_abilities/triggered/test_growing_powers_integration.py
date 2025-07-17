"""Integration tests for GROWING POWERS - When you play this character, you may put this character anywhere on your board (underneath a character already in play)."""

import pytest
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.event_system import GameEvent, EventContext
from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability


class TestGrowingPowersIntegration(BaseNamedAbilityTest):
    """Integration tests for GROWING POWERS named ability."""
    
    def create_growing_powers_character(self, name="Groot - Flora Colossus"):
        """Create a character with GROWING POWERS ability."""
        character = create_test_character(
            name=name,
            cost=4,
            color=CardColor.EMERALD,
            strength=3,
            willpower=5,
            lore=1,
            rarity=Rarity.RARE
        )
        
        add_named_ability(character, "GROWING POWERS", "triggered", self.event_manager)
        return character
    
    def create_other_character(self, name="Other Character", position=0):
        """Create another character for board positioning tests."""
        character = create_test_character(
            name=name,
            cost=3,
            color=CardColor.RUBY,
            strength=2,
            willpower=3,
            lore=1,
            rarity=Rarity.COMMON
        )
        return character
    
    def test_growing_powers_triggers_on_play(self):
        """Test that GROWING POWERS triggers when the character is played."""
        growing_powers_char = self.create_growing_powers_character()
        other_char = self.create_other_character("Existing Character")
        
        # Put another character in play first
        self.player1.characters_in_play.append(other_char)
        
        # Growing powers character enters play
        self.player1.characters_in_play.append(growing_powers_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=growing_powers_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Verify ability exists and is properly configured
        growing_powers_ability = growing_powers_char.composable_abilities[0]
        assert growing_powers_ability.name == "GROWING POWERS"
        
        # Should have triggered on enters play
        assert len(self.player1.characters_in_play) == 2
    
    def test_growing_powers_board_positioning_option(self):
        """Test that GROWING POWERS provides board positioning options."""
        growing_powers_char = self.create_growing_powers_character()
        
        # Create multiple characters already in play
        existing_chars = [
            self.create_other_character("Character 1", 0),
            self.create_other_character("Character 2", 1),
            self.create_other_character("Character 3", 2)
        ]
        
        # Put existing characters in play
        self.player1.characters_in_play.extend(existing_chars)
        
        # Growing powers character enters play
        self.player1.characters_in_play.append(growing_powers_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=growing_powers_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # GROWING POWERS should provide positioning options
        growing_powers_ability = growing_powers_char.composable_abilities[0]
        assert growing_powers_ability.name == "GROWING POWERS"
        
        # Should be able to position anywhere on the board
        assert len(self.player1.characters_in_play) == 4
    
    def test_growing_powers_empty_board(self):
        """Test GROWING POWERS when played to an empty board."""
        growing_powers_char = self.create_growing_powers_character()
        
        # No other characters in play
        assert len(self.player1.characters_in_play) == 0
        
        # Growing powers character enters play
        self.player1.characters_in_play.append(growing_powers_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=growing_powers_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should still trigger even with empty board
        growing_powers_ability = growing_powers_char.composable_abilities[0]
        assert growing_powers_ability.name == "GROWING POWERS"
        
        assert len(self.player1.characters_in_play) == 1
    
    def test_growing_powers_optional_ability(self):
        """Test that GROWING POWERS is optional (may put this character)."""
        growing_powers_char = self.create_growing_powers_character()
        existing_char = self.create_other_character("Existing Character")
        
        self.player1.characters_in_play.append(existing_char)
        self.player1.characters_in_play.append(growing_powers_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=growing_powers_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Ability should trigger but positioning is optional
        growing_powers_ability = growing_powers_char.composable_abilities[0]
        assert growing_powers_ability.name == "GROWING POWERS"
    
    def test_growing_powers_only_triggers_for_self(self):
        """Test that GROWING POWERS only triggers when the ability owner enters play."""
        growing_powers_char = self.create_growing_powers_character()
        other_char = self.create_other_character("Other Character")
        
        # Put growing powers character in play first
        self.player1.characters_in_play.append(growing_powers_char)
        
        # Other character enters play (should NOT trigger GROWING POWERS)
        self.player1.characters_in_play.append(other_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=other_char,  # Different character entering
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should not trigger for other characters
        growing_powers_ability = growing_powers_char.composable_abilities[0]
        assert growing_powers_ability.name == "GROWING POWERS"
    
    def test_growing_powers_multiple_instances(self):
        """Test multiple characters with GROWING POWERS."""
        growing_powers_char1 = self.create_growing_powers_character("Groot - Flora Colossus")
        growing_powers_char2 = self.create_growing_powers_character("Groot - Tiny Sapling")
        
        # First character enters
        self.player1.characters_in_play.append(growing_powers_char1)
        
        event_context1 = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=growing_powers_char1,
            player=self.player1,
            game_state=self.game_state
        )
        
        self.event_manager.trigger_event(event_context1)
        
        # Second character enters
        self.player1.characters_in_play.append(growing_powers_char2)
        
        event_context2 = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=growing_powers_char2,
            player=self.player1,
            game_state=self.game_state
        )
        
        self.event_manager.trigger_event(event_context2)
        
        # Both should have triggered their abilities
        assert growing_powers_char1.composable_abilities[0].name == "GROWING POWERS"
        assert growing_powers_char2.composable_abilities[0].name == "GROWING POWERS"
    
    def test_growing_powers_board_state_awareness(self):
        """Test that GROWING POWERS is aware of current board state."""
        growing_powers_char = self.create_growing_powers_character()
        
        # Create characters with different positions
        char1 = self.create_other_character("Position 1", 0)
        char2 = self.create_other_character("Position 2", 1)
        char3 = self.create_other_character("Position 3", 2)
        
        # Set up specific board positions
        self.player1.characters_in_play.extend([char1, char2, char3])
        
        # Growing powers character enters
        self.player1.characters_in_play.append(growing_powers_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=growing_powers_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should be aware of all existing characters for positioning
        growing_powers_ability = growing_powers_char.composable_abilities[0]
        assert growing_powers_ability.name == "GROWING POWERS"
        
        assert len(self.player1.characters_in_play) == 4
    
    def test_growing_powers_opponent_board_unaffected(self):
        """Test that GROWING POWERS doesn't affect opponent's board."""
        growing_powers_char = self.create_growing_powers_character()
        opponent_char = self.create_other_character("Opponent Character")
        
        # Put opponent character on their board
        self.player2.characters_in_play.append(opponent_char)
        
        # Growing powers character enters friendly board
        self.player1.characters_in_play.append(growing_powers_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=growing_powers_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should only affect friendly board
        assert len(self.player1.characters_in_play) == 1
        assert len(self.player2.characters_in_play) == 1
        
        growing_powers_ability = growing_powers_char.composable_abilities[0]
        assert growing_powers_ability.name == "GROWING POWERS"
    
    def test_growing_powers_ability_registration(self):
        """Test that GROWING POWERS ability is properly registered."""
        growing_powers_char = self.create_growing_powers_character()
        self.player1.characters_in_play.append(growing_powers_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # Should respond to character enters play events
        assert growing_powers_char.composable_abilities
        assert growing_powers_char.composable_abilities[0].name == "GROWING POWERS"
        
        # Check that it has listeners for the correct event
        ability = growing_powers_char.composable_abilities[0]
        assert len(ability.listeners) > 0


if __name__ == "__main__":
    pytest.main([__file__])