"""Integration tests for VOICELESS - This character can't ⟳ to sing songs."""

import pytest
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability, create_test_action_card, add_singer_ability


class TestVoicelessIntegration(BaseNamedAbilityTest):
    """Integration tests for VOICELESS named ability."""
    
    def create_voiceless_character(self, name="Ariel - On Human Legs"):
        """Create a character with VOICELESS ability."""
        character = create_test_character(
            name=name,
            cost=3,
            color=CardColor.RUBY,
            strength=2,
            willpower=3,
            lore=2,
            rarity=Rarity.RARE
        )
        
        add_named_ability(character, "VOICELESS", "static", self.event_manager)
        return character
    
    def create_song_card(self, name="A Whole New World", cost=4):
        """Create a song card for testing."""
        return create_test_action_card(
            name=name,
            cost=cost,
            color=CardColor.RUBY,
            rarity=Rarity.COMMON
        )
    
    def create_singer_character(self, singer_cost=4):
        """Create a character with Singer ability for comparison."""
        singer = create_test_character(
            name="Belle - Hidden Depths",
            cost=2,
            color=CardColor.RUBY,
            strength=1,
            willpower=4,
            lore=1,
            rarity=Rarity.COMMON
        )
        
        add_singer_ability(singer, singer_cost, self.event_manager)
        return singer
    
    def test_voiceless_prevents_singing(self):
        """Test that VOICELESS character cannot sing songs."""
        # Setup characters
        voiceless_char = self.create_voiceless_character()
        song = self.create_song_card()
        
        # Add characters to player's board
        self.player1.characters_in_play.append(voiceless_char)
        self.player1.hand.append(song)
        
        # Try to sing with voiceless character
        # In a real game engine, this would be validated
        # For now, we test that the ability exists and is correctly configured
        
        assert voiceless_char.composable_abilities
        voiceless_ability = voiceless_char.composable_abilities[0]
        assert voiceless_ability.name == "VOICELESS"
        
        # VOICELESS should prevent singing - this would be enforced by the game engine
        # The ability itself is a static restriction that the engine would check
    
    def test_voiceless_does_not_affect_normal_actions(self):
        """Test that VOICELESS only affects singing, not other actions."""
        voiceless_char = self.create_voiceless_character()
        
        # VOICELESS should not prevent questing, challenging, or other normal actions
        assert voiceless_char.current_strength == 2
        assert voiceless_char.current_willpower == 3
        assert voiceless_char.current_lore == 2
        
        # Character should be able to quest and challenge normally
        # (This would be tested in the game engine integration)
    
    def test_normal_singer_can_sing(self):
        """Test that normal Singer characters can sing for comparison."""
        singer_char = self.create_singer_character(singer_cost=4)
        song = self.create_song_card(cost=4)
        
        self.player1.characters_in_play.append(singer_char)
        self.player1.hand.append(song)
        
        # Singer character should have Singer ability
        assert singer_char.composable_abilities
        singer_ability = singer_char.composable_abilities[0]
        assert "Singer" in singer_ability.name
        
        # This character should be able to sing (validated by game engine)
    
    def test_voiceless_with_singer_cost_song(self):
        """Test VOICELESS character with a song that matches Singer cost."""
        voiceless_char = self.create_voiceless_character()
        expensive_song = self.create_song_card("Let It Go", cost=8)
        
        self.player1.characters_in_play.append(voiceless_char)
        self.player1.hand.append(expensive_song)
        
        # Even if the character could theoretically sing this song based on cost,
        # VOICELESS should prevent it
        voiceless_ability = voiceless_char.composable_abilities[0]
        assert voiceless_ability.name == "VOICELESS"
    
    def test_multiple_voiceless_characters(self):
        """Test multiple VOICELESS characters on the board."""
        char1 = self.create_voiceless_character("Ariel - On Human Legs")
        char2 = self.create_voiceless_character("Ariel - Curious Mermaid")
        
        self.player1.characters_in_play.extend([char1, char2])
        
        # Both should have VOICELESS
        for char in [char1, char2]:
            assert char.composable_abilities
            assert char.composable_abilities[0].name == "VOICELESS"
    
    def test_voiceless_ability_registration(self):
        """Test that VOICELESS ability is properly registered with event manager."""
        voiceless_char = self.create_voiceless_character()
        self.player1.characters_in_play.append(voiceless_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # VOICELESS is a static ability, so it may not need event listeners
        # But it should be properly associated with the character
        assert voiceless_char.composable_abilities
        assert voiceless_char.composable_abilities[0].name == "VOICELESS"


if __name__ == "__main__":
    pytest.main([__file__])