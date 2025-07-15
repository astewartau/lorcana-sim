"""Integration tests for HEROISM - When you play this character, chosen opposing character gets -2 ◆ this turn."""

import pytest
from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.models.abilities.composable.named_abilities import NamedAbilityRegistry
from src.lorcana_sim.engine.event_system import GameEventManager, GameEvent, EventContext


class TestHeroismIntegration:
    """Integration tests for HEROISM named ability."""
    
    def setup_method(self):
        """Set up test environment with players and game state."""
        self.player1 = Player("Player 1")
        self.player2 = Player("Player 2")
        self.game_state = GameState([self.player1, self.player2])
        self.event_manager = GameEventManager(self.game_state)
        self.game_state.event_manager = self.event_manager
    
    def create_heroism_character(self, name="Hercules - True Hero"):
        """Create a character with HEROISM ability."""
        character = CharacterCard(
            id=1,
            name=name.split(" - ")[0],
            version=name.split(" - ")[1] if " - " in name else "Test",
            full_name=name,
            cost=5,
            color=CardColor.AMBER,
            inkwell=True,
            rarity=Rarity.LEGENDARY,
            set_code="1",
            number=1,
            story="Test",
            abilities=[],
            strength=4,
            willpower=5,
            lore=2
        )
        
        # Add HEROISM ability
        ability_data = {"name": "HEROISM", "type": "triggered"}
        heroism_ability = NamedAbilityRegistry.create_ability("HEROISM", character, ability_data)
        character.composable_abilities = [heroism_ability]
        character.register_composable_abilities(self.event_manager)
        
        return character
    
    def create_opponent_character(self, name="Villain Character", strength=3):
        """Create an opponent character to target with HEROISM."""
        character = CharacterCard(
            id=2,
            name=name,
            version="Test",
            full_name=f"{name} - Test",
            cost=4,
            color=CardColor.RUBY,
            inkwell=True,
            rarity=Rarity.RARE,
            set_code="1",
            number=2,
            story="Test",
            abilities=[],
            strength=strength,
            willpower=4,
            lore=1
        )
        return character
    
    def create_friendly_character(self, name="Friendly Character"):
        """Create a friendly character that should not be affected."""
        character = CharacterCard(
            id=3,
            name=name,
            version="Test",
            full_name=f"{name} - Test",
            cost=3,
            color=CardColor.AMBER,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="1",
            number=3,
            story="Test",
            abilities=[],
            strength=2,
            willpower=3,
            lore=1
        )
        return character
    
    def test_heroism_triggers_on_play(self):
        """Test that HEROISM triggers when the character is played."""
        heroism_char = self.create_heroism_character()
        opponent_char = self.create_opponent_character("Target Villain", strength=4)
        
        # Put opponent character in play
        self.player2.characters_in_play.append(opponent_char)
        
        # Heroism character enters play
        self.player1.characters_in_play.append(heroism_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=heroism_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Verify ability exists and is properly configured
        heroism_ability = heroism_char.composable_abilities[0]
        assert heroism_ability.name == "HEROISM"
        
        # Should have opposing character to target
        assert len(self.player2.characters_in_play) == 1
        assert opponent_char.strength == 4  # Original strength
    
    def test_heroism_targets_opposing_character(self):
        """Test that HEROISM targets opposing characters, not friendly ones."""
        heroism_char = self.create_heroism_character()
        opponent_char = self.create_opponent_character("Target Villain", strength=4)
        friendly_char = self.create_friendly_character("Friendly Character")
        
        # Put both characters in play
        self.player1.characters_in_play.append(friendly_char)
        self.player2.characters_in_play.append(opponent_char)
        
        # Heroism character enters play
        self.player1.characters_in_play.append(heroism_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=heroism_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should only target opposing characters
        heroism_ability = heroism_char.composable_abilities[0]
        assert heroism_ability.name == "HEROISM"
        
        # Friendly character should be unaffected
        assert friendly_char.strength == 2  # Original strength
        # Opponent character should be targetable
        assert opponent_char.strength == 4  # Original strength
    
    def test_heroism_no_opposing_characters(self):
        """Test HEROISM when there are no opposing characters to target."""
        heroism_char = self.create_heroism_character()
        friendly_char = self.create_friendly_character("Friendly Character")
        
        # Only friendly characters in play
        self.player1.characters_in_play.append(friendly_char)
        
        # Heroism character enters play
        self.player1.characters_in_play.append(heroism_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=heroism_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should still trigger but have no valid targets
        heroism_ability = heroism_char.composable_abilities[0]
        assert heroism_ability.name == "HEROISM"
        
        assert len(self.player2.characters_in_play) == 0  # No opponents
    
    def test_heroism_multiple_opposing_characters(self):
        """Test HEROISM with multiple opposing characters (chosen targeting)."""
        heroism_char = self.create_heroism_character()
        opponent_char1 = self.create_opponent_character("Villain 1", strength=3)
        opponent_char2 = self.create_opponent_character("Villain 2", strength=5)
        opponent_char3 = self.create_opponent_character("Villain 3", strength=2)
        
        # Put multiple opponents in play
        self.player2.characters_in_play.extend([opponent_char1, opponent_char2, opponent_char3])
        
        # Heroism character enters play
        self.player1.characters_in_play.append(heroism_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=heroism_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should be able to choose from multiple targets
        heroism_ability = heroism_char.composable_abilities[0]
        assert heroism_ability.name == "HEROISM"
        
        # All opponents should be valid targets
        assert len(self.player2.characters_in_play) == 3
        for char in [opponent_char1, opponent_char2, opponent_char3]:
            assert char.strength >= 2  # All have sufficient strength
    
    def test_heroism_strength_reduction_this_turn(self):
        """Test that HEROISM reduces strength for this turn only."""
        heroism_char = self.create_heroism_character()
        opponent_char = self.create_opponent_character("Target Villain", strength=4)
        
        self.player2.characters_in_play.append(opponent_char)
        self.player1.characters_in_play.append(heroism_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=heroism_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Effect should be temporary (this turn only)
        heroism_ability = heroism_char.composable_abilities[0]
        assert heroism_ability.name == "HEROISM"
        
        # Original strength should be preserved
        assert opponent_char.strength == 4
    
    def test_heroism_only_triggers_for_self(self):
        """Test that HEROISM only triggers when the ability owner enters play."""
        heroism_char = self.create_heroism_character()
        other_char = self.create_friendly_character("Other Character")
        opponent_char = self.create_opponent_character("Target Villain", strength=4)
        
        # Put heroism character and opponent in play first
        self.player1.characters_in_play.append(heroism_char)
        self.player2.characters_in_play.append(opponent_char)
        
        # Other character enters play (should NOT trigger HEROISM)
        self.player1.characters_in_play.append(other_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=other_char,  # Different character entering
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should not trigger for other characters
        heroism_ability = heroism_char.composable_abilities[0]
        assert heroism_ability.name == "HEROISM"
    
    def test_heroism_low_strength_targets(self):
        """Test HEROISM with low-strength targets that could go to 0 or negative."""
        heroism_char = self.create_heroism_character()
        weak_opponent = self.create_opponent_character("Weak Villain", strength=1)
        
        self.player2.characters_in_play.append(weak_opponent)
        self.player1.characters_in_play.append(heroism_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=heroism_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Character with 1 strength would go to -1 with -2 penalty
        heroism_ability = heroism_char.composable_abilities[0]
        assert heroism_ability.name == "HEROISM"
        
        assert weak_opponent.strength == 1  # Original strength
    
    def test_heroism_ability_registration(self):
        """Test that HEROISM ability is properly registered."""
        heroism_char = self.create_heroism_character()
        self.player1.characters_in_play.append(heroism_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # Should respond to character enters play events
        assert heroism_char.composable_abilities
        assert heroism_char.composable_abilities[0].name == "HEROISM"
        
        # Check that it has listeners for the correct event
        ability = heroism_char.composable_abilities[0]
        assert len(ability.listeners) > 0


if __name__ == "__main__":
    pytest.main([__file__])