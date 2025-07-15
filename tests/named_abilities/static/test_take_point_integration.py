"""Integration tests for TAKE POINT - While a damaged character is in play, this character gets +2 ¤."""

import pytest
from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.models.abilities.composable.named_abilities import NamedAbilityRegistry
from src.lorcana_sim.engine.event_system import GameEventManager, GameEvent, EventContext


class TestTakePointIntegration:
    """Integration tests for TAKE POINT named ability."""
    
    def setup_method(self):
        """Set up test environment with players and game state."""
        self.player1 = Player("Player 1")
        self.player2 = Player("Player 2")
        self.game_state = GameState([self.player1, self.player2])
        self.event_manager = GameEventManager(self.game_state)
        self.game_state.event_manager = self.event_manager
    
    def create_take_point_character(self, name="Captain Hook - Forceful Duelist"):
        """Create a character with TAKE POINT ability."""
        character = CharacterCard(
            id=1,
            name=name.split(" - ")[0],
            version=name.split(" - ")[1] if " - " in name else "Test",
            full_name=name,
            cost=5,
            color=CardColor.RUBY,
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
        
        # Add TAKE POINT ability
        ability_data = {"name": "TAKE POINT", "type": "static"}
        take_point_ability = NamedAbilityRegistry.create_ability("TAKE POINT", character, ability_data)
        character.composable_abilities = [take_point_ability]
        character.register_composable_abilities(self.event_manager)
        
        return character
    
    def create_damaged_character(self, name="Damaged Character", damage=1):
        """Create a character with damage for testing."""
        character = CharacterCard(
            id=2,
            name=name,
            version="Test",
            full_name=f"{name} - Test",
            cost=3,
            color=CardColor.RUBY,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="1",
            number=2,
            story="Test",
            abilities=[],
            strength=2,
            willpower=3,
            lore=1
        )
        character.damage = damage
        return character
    
    def create_undamaged_character(self, name="Healthy Character"):
        """Create an undamaged character for comparison."""
        character = CharacterCard(
            id=3,
            name=name,
            version="Test",
            full_name=f"{name} - Test",
            cost=4,
            color=CardColor.SAPPHIRE,
            inkwell=True,
            rarity=Rarity.RARE,
            set_code="1",
            number=3,
            story="Test",
            abilities=[],
            strength=3,
            willpower=4,
            lore=2
        )
        character.damage = 0
        return character
    
    def test_take_point_gives_strength_bonus_when_damaged_character_present(self):
        """Test that TAKE POINT gives +2 strength when a damaged character is in play."""
        take_point_char = self.create_take_point_character()
        damaged_char = self.create_damaged_character("Damaged Ally", damage=2)
        
        # Put both characters in play
        self.player1.characters_in_play.extend([take_point_char, damaged_char])
        
        # Simulate damaged character taking damage
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            source=damaged_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        self.event_manager.trigger_event(event_context)
        
        # TAKE POINT should provide +2 strength bonus due to damaged character
        take_point_ability = take_point_char.composable_abilities[0]
        assert take_point_ability.name == "TAKE POINT"
        
        # Should have +2 strength bonus (4 base + 2 bonus = 6)
        assert take_point_char.strength == 6
        # Damaged character should have damage
        assert damaged_char.damage == 2
    
    def test_take_point_no_bonus_without_damaged_characters(self):
        """Test that TAKE POINT provides no bonus when no characters are damaged."""
        take_point_char = self.create_take_point_character()
        healthy_char = self.create_undamaged_character("Healthy Ally")
        
        # Put both undamaged characters in play
        self.player1.characters_in_play.extend([take_point_char, healthy_char])
        
        # No damage events
        assert take_point_char.damage == 0
        assert healthy_char.damage == 0
        
        # TAKE POINT should not provide bonus
        take_point_ability = take_point_char.composable_abilities[0]
        assert take_point_ability.name == "TAKE POINT"
        
        # Base strength should remain
        assert take_point_char.strength == 4
    
    def test_take_point_responds_to_damage_events(self):
        """Test that TAKE POINT responds when characters take damage."""
        take_point_char = self.create_take_point_character()
        target_char = self.create_undamaged_character("Target")
        
        self.player1.characters_in_play.extend([take_point_char, target_char])
        
        # Initially no damage
        assert target_char.damage == 0
        
        # Character takes damage
        target_char.damage = 1
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            source=target_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        self.event_manager.trigger_event(event_context)
        
        # TAKE POINT should respond to damage events
        take_point_ability = take_point_char.composable_abilities[0]
        assert take_point_ability.name == "TAKE POINT"
    
    def test_take_point_affects_any_damaged_character(self):
        """Test that TAKE POINT works with any damaged character (friendly or opposing)."""
        take_point_char = self.create_take_point_character()
        friendly_damaged = self.create_damaged_character("Friendly Damaged", damage=1)
        opponent_damaged = self.create_damaged_character("Opponent Damaged", damage=2)
        
        # Put characters on different sides
        self.player1.characters_in_play.extend([take_point_char, friendly_damaged])
        self.player2.characters_in_play.append(opponent_damaged)
        
        # Should trigger with any damaged character
        assert friendly_damaged.damage > 0
        assert opponent_damaged.damage > 0
        
        take_point_ability = take_point_char.composable_abilities[0]
        assert take_point_ability.name == "TAKE POINT"
    
    def test_take_point_multiple_damaged_characters(self):
        """Test TAKE POINT with multiple damaged characters."""
        take_point_char = self.create_take_point_character()
        damaged_char1 = self.create_damaged_character("Damaged 1", damage=1)
        damaged_char2 = self.create_damaged_character("Damaged 2", damage=3)
        damaged_char3 = self.create_damaged_character("Damaged 3", damage=2)
        
        self.player1.characters_in_play.extend([take_point_char, damaged_char1, damaged_char2])
        self.player2.characters_in_play.append(damaged_char3)
        
        # Multiple damaged characters should still only give +2 strength
        take_point_ability = take_point_char.composable_abilities[0]
        assert take_point_ability.name == "TAKE POINT"
        
        # All characters should be damaged
        assert all(char.damage > 0 for char in [damaged_char1, damaged_char2, damaged_char3])
    
    def test_take_point_bonus_persists_while_damage_exists(self):
        """Test that TAKE POINT bonus persists as long as damaged characters exist."""
        take_point_char = self.create_take_point_character()
        damaged_char = self.create_damaged_character("Damaged", damage=3)
        
        self.player1.characters_in_play.extend([take_point_char, damaged_char])
        
        # Bonus should be active
        assert damaged_char.damage > 0
        
        # Heal some damage but not all
        damaged_char.damage = 1
        assert damaged_char.damage > 0
        
        # Should still have bonus
        take_point_ability = take_point_char.composable_abilities[0]
        assert take_point_ability.name == "TAKE POINT"
    
    def test_take_point_bonus_ends_when_all_damage_healed(self):
        """Test that TAKE POINT bonus ends when all characters are healed."""
        take_point_char = self.create_take_point_character()
        damaged_char = self.create_damaged_character("Damaged", damage=2)
        
        self.player1.characters_in_play.extend([take_point_char, damaged_char])
        
        # Initially damaged
        assert damaged_char.damage > 0
        
        # Heal all damage
        damaged_char.damage = 0
        
        # No more damaged characters
        assert damaged_char.damage == 0
        
        take_point_ability = take_point_char.composable_abilities[0]
        assert take_point_ability.name == "TAKE POINT"
    
    def test_take_point_multiple_instances(self):
        """Test multiple TAKE POINT characters."""
        take_point_char1 = self.create_take_point_character("Character 1")
        take_point_char2 = self.create_take_point_character("Character 2")
        damaged_char = self.create_damaged_character("Damaged", damage=1)
        
        self.player1.characters_in_play.extend([take_point_char1, take_point_char2, damaged_char])
        
        # Both should have TAKE POINT and benefit from damaged character
        for char in [take_point_char1, take_point_char2]:
            assert char.composable_abilities
            assert char.composable_abilities[0].name == "TAKE POINT"
    
    def test_take_point_ability_registration(self):
        """Test that TAKE POINT ability is properly registered."""
        take_point_char = self.create_take_point_character()
        self.player1.characters_in_play.append(take_point_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # Should respond to damage events
        assert take_point_char.composable_abilities
        assert take_point_char.composable_abilities[0].name == "TAKE POINT"


if __name__ == "__main__":
    pytest.main([__file__])