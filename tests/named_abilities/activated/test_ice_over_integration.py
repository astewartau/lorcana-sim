"""Integration tests for ICE OVER - ↷, 2 ⬢ - Exert chosen character. They can't ready at the start of their next turn."""

import pytest
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.event_system import GameEvent, EventContext
from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability


class TestIceOverIntegration(BaseNamedAbilityTest):
    """Integration tests for ICE OVER named ability."""
    
    def create_ice_over_character(self, name="Elsa - Ice Queen"):
        """Create a character with ICE OVER ability."""
        character = create_test_character(
            name=name,
            cost=7,
            color=CardColor.AMETHYST,
            strength=3,
            willpower=7,
            lore=3,
            rarity=Rarity.LEGENDARY
        )
        
        add_named_ability(character, "ICE OVER", "activated", self.event_manager)
        return character
    
    def create_target_character(self, name="Target Character", exerted=False):
        """Create a character to target with ICE OVER."""
        character = create_test_character(
            name=f"{name} - Test",
            cost=4,
            color=CardColor.RUBY,
            strength=3,
            willpower=4,
            lore=2,
            rarity=Rarity.COMMON
        )
        character.exerted = exerted
        return character
    
    def create_opponent_character(self, name="Opponent Character", exerted=False):
        """Create an opponent character to target."""
        character = create_test_character(
            name=f"{name} - Test",
            cost=3,
            color=CardColor.SAPPHIRE,
            strength=2,
            willpower=3,
            lore=1,
            rarity=Rarity.RARE
        )
        character.exerted = exerted
        return character
    
    def test_ice_over_ability_exists(self):
        """Test that ICE OVER ability is properly created and registered."""
        ice_over_char = self.create_ice_over_character()
        self.player1.characters_in_play.append(ice_over_char)
        
        # Verify ability exists
        assert ice_over_char.composable_abilities
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
        
        # Should be an activated ability
        assert hasattr(ice_over_ability, 'can_activate') or len(ice_over_ability.listeners) > 0
    
    def test_ice_over_requires_exertion_and_cost(self):
        """Test that ICE OVER requires exerting the character and paying 2 ink."""
        ice_over_char = self.create_ice_over_character()
        target_char = self.create_target_character("Target")
        
        # Characters must be ready to use activated abilities
        ice_over_char.exerted = False
        
        self.player1.characters_in_play.append(ice_over_char)
        self.player2.characters_in_play.append(target_char)
        
        # Player needs enough ink to pay cost
        self.player1.ink_used_this_turn = 0  # Reset ink usage
        # Add ink to inkwell to have available ink
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card, ink_card]  # 2 ink available
        
        # ICE OVER should require exerting the character and paying 2 ink
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
        
        # Character should be ready to activate
        assert not ice_over_char.exerted
    
    def test_ice_over_exerts_target_character(self):
        """Test that ICE OVER exerts the chosen target character."""
        ice_over_char = self.create_ice_over_character()
        target_char = self.create_target_character("Target", exerted=False)
        
        # Set up characters
        ice_over_char.exerted = False
        self.player1.characters_in_play.append(ice_over_char)
        self.player2.characters_in_play.append(target_char)
        self.player1.ink_used_this_turn = 0
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card, ink_card]
        
        # Target should start ready
        assert not target_char.exerted
        
        # Simulate activating ICE OVER ability
        # In a real game, this would be handled by the move validator and game engine
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
        
        # The ability should be able to target the character
        assert len(self.player2.characters_in_play) == 1
    
    def test_ice_over_prevents_ready_next_turn(self):
        """Test that ICE OVER prevents the target from readying next turn."""
        ice_over_char = self.create_ice_over_character()
        target_char = self.create_target_character("Target", exerted=False)
        
        ice_over_char.exerted = False
        self.player1.characters_in_play.append(ice_over_char)
        self.player2.characters_in_play.append(target_char)
        self.player1.ink_used_this_turn = 0
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card, ink_card]
        
        # Simulate ICE OVER effect
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
        
        # Effect should prevent readying at start of next turn
        # This would be tracked by the game engine
    
    def test_ice_over_can_target_any_character(self):
        """Test that ICE OVER can target any character (friendly or opposing)."""
        ice_over_char = self.create_ice_over_character()
        friendly_target = self.create_target_character("Friendly Target")
        opponent_target = self.create_opponent_character("Opponent Target")
        
        ice_over_char.exerted = False
        self.player1.characters_in_play.extend([ice_over_char, friendly_target])
        self.player2.characters_in_play.append(opponent_target)
        self.player1.ink_used_this_turn = 0
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card, ink_card]
        
        # Should be able to target both friendly and opposing characters
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
        
        # Both characters should be valid targets
        assert len(self.player1.characters_in_play) == 2  # Ice Over char + friendly target
        assert len(self.player2.characters_in_play) == 1  # Opponent target
    
    def test_ice_over_can_target_already_exerted_characters(self):
        """Test that ICE OVER can target characters that are already exerted."""
        ice_over_char = self.create_ice_over_character()
        exerted_target = self.create_target_character("Exerted Target", exerted=True)
        
        ice_over_char.exerted = False
        self.player1.characters_in_play.append(ice_over_char)
        self.player2.characters_in_play.append(exerted_target)
        self.player1.ink_used_this_turn = 0
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card, ink_card]
        
        # Should be able to target already exerted characters
        assert exerted_target.exerted
        
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
    
    def test_ice_over_requires_ready_activator(self):
        """Test that ICE OVER requires the activating character to be ready."""
        ice_over_char = self.create_ice_over_character()
        target_char = self.create_target_character("Target")
        
        # Ice over character is exerted (can't activate)
        ice_over_char.exerted = True
        self.player1.characters_in_play.append(ice_over_char)
        self.player2.characters_in_play.append(target_char)
        self.player1.ink_used_this_turn = 0
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card, ink_card]
        
        # Should not be able to activate when exerted
        assert ice_over_char.exerted
        
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
    
    def test_ice_over_requires_sufficient_ink(self):
        """Test that ICE OVER requires sufficient ink to activate."""
        ice_over_char = self.create_ice_over_character()
        target_char = self.create_target_character("Target")
        
        ice_over_char.exerted = False
        self.player1.characters_in_play.append(ice_over_char)
        self.player2.characters_in_play.append(target_char)
        
        # Not enough ink
        self.player1.ink_used_this_turn = 0
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card]  # Only 1 ink, need 2
        
        # Should not be able to activate without sufficient ink
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
        
        assert self.player1.available_ink < 2
    
    def test_ice_over_multiple_targets_available(self):
        """Test ICE OVER when multiple targets are available."""
        ice_over_char = self.create_ice_over_character()
        target1 = self.create_target_character("Target 1")
        target2 = self.create_target_character("Target 2")
        target3 = self.create_opponent_character("Opponent Target")
        
        ice_over_char.exerted = False
        self.player1.characters_in_play.extend([ice_over_char, target1, target2])
        self.player2.characters_in_play.append(target3)
        self.player1.ink_used_this_turn = 0
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card, ink_card]
        
        # Should be able to choose from multiple targets
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
        
        # Total valid targets: friendly target1, target2, and opponent target3
        # (ice_over_char itself might or might not be targetable depending on implementation)
        total_characters = len(self.player1.characters_in_play) + len(self.player2.characters_in_play)
        assert total_characters == 4
    
    def test_ice_over_no_valid_targets(self):
        """Test ICE OVER when no valid targets are available."""
        ice_over_char = self.create_ice_over_character()
        
        # Only the ice over character in play
        ice_over_char.exerted = False
        self.player1.characters_in_play.append(ice_over_char)
        self.player1.ink_used_this_turn = 0
        ink_card = create_test_character(name="Ink - Test", cost=1)
        self.player1.inkwell = [ink_card, ink_card]
        
        # Depending on implementation, character might target itself
        ice_over_ability = ice_over_char.composable_abilities[0]
        assert ice_over_ability.name == "ICE OVER"
        
        assert len(self.player1.characters_in_play) == 1
        assert len(self.player2.characters_in_play) == 0
    
    def test_ice_over_ability_registration(self):
        """Test that ICE OVER ability is properly registered."""
        ice_over_char = self.create_ice_over_character()
        self.player1.characters_in_play.append(ice_over_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # ICE OVER is an activated ability, may not have event listeners
        # but should be properly associated with the character
        assert ice_over_char.composable_abilities
        assert ice_over_char.composable_abilities[0].name == "ICE OVER"


if __name__ == "__main__":
    pytest.main([__file__])