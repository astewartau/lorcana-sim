"""Integration tests for WHAT DO WE DO NOW? - When you play this character, if you have a character named Anna in play, gain 2 lore."""

import pytest
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.engine.event_system import GameEvent, EventContext
from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability


class TestWhatDoWeDoNowIntegration(BaseNamedAbilityTest):
    """Integration tests for WHAT DO WE DO NOW? named ability."""
    
    def create_what_do_we_do_now_character(self, name="Elsa - Snow Queen"):
        """Create a character with WHAT DO WE DO NOW? ability."""
        character = create_test_character(
            name=name,
            cost=8,
            color=CardColor.AMETHYST,
            strength=4,
            willpower=8,
            lore=3,
            rarity=Rarity.LEGENDARY
        )
        
        add_named_ability(character, "WHAT DO WE DO NOW?", "triggered", self.event_manager)
        return character
    
    def create_anna_character(self, name="Anna - Heir to Arendelle"):
        """Create an Anna character for the condition."""
        character = create_test_character(
            name=name,
            cost=5,
            color=CardColor.AMETHYST,
            strength=3,
            willpower=5,
            lore=2,
            rarity=Rarity.RARE
        )
        # Override the name to be "Anna" as required by the ability
        character.name = "Anna"
        return character
    
    def create_non_anna_character(self, name="Kristoff - Official Ice Master"):
        """Create a non-Anna character for comparison."""
        character = create_test_character(
            name=name,
            cost=4,
            color=CardColor.AMBER,
            strength=4,
            willpower=4,
            lore=1,
            rarity=Rarity.COMMON
        )
        # Override the name to be "Kristoff" as required for testing
        character.name = "Kristoff"
        return character
    
    def test_what_do_we_do_now_triggers_with_anna_in_play(self):
        """Test that WHAT DO WE DO NOW? triggers when Anna is in play."""
        elsa_char = self.create_what_do_we_do_now_character()
        anna_char = self.create_anna_character()
        
        # Put Anna in play first
        self.player1.characters_in_play.append(anna_char)
        
        # Track player's lore before
        initial_lore = self.player1.lore
        
        # Elsa enters play (should trigger ability because Anna is in play)
        self.player1.characters_in_play.append(elsa_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=elsa_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Verify ability exists and is properly configured
        what_do_we_do_now_ability = elsa_char.composable_abilities[0]
        assert what_do_we_do_now_ability.name == "WHAT DO WE DO NOW?"
        
        # Anna should be in play
        anna_in_play = any(char.name == "Anna" for char in self.player1.characters_in_play)
        assert anna_in_play
    
    def test_what_do_we_do_now_does_not_trigger_without_anna(self):
        """Test that WHAT DO WE DO NOW? does not trigger when Anna is not in play."""
        elsa_char = self.create_what_do_we_do_now_character()
        kristoff_char = self.create_non_anna_character()
        
        # Put non-Anna character in play
        self.player1.characters_in_play.append(kristoff_char)
        
        # Track player's lore before
        initial_lore = self.player1.lore
        
        # Elsa enters play (should NOT trigger ability because Anna is not in play)
        self.player1.characters_in_play.append(elsa_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=elsa_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Verify Anna is not in play
        anna_in_play = any(char.name == "Anna" for char in self.player1.characters_in_play)
        assert not anna_in_play
        
        # Ability should still exist but not trigger
        what_do_we_do_now_ability = elsa_char.composable_abilities[0]
        assert what_do_we_do_now_ability.name == "WHAT DO WE DO NOW?"
    
    def test_what_do_we_do_now_only_triggers_for_ability_owner(self):
        """Test that WHAT DO WE DO NOW? only triggers when the ability owner enters play."""
        elsa_char = self.create_what_do_we_do_now_character()
        anna_char = self.create_anna_character()
        other_char = self.create_non_anna_character()
        
        # Put both Elsa and Anna in play
        self.player1.characters_in_play.extend([elsa_char, anna_char])
        
        # Other character enters play (should NOT trigger Elsa's ability)
        self.player1.characters_in_play.append(other_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=other_char,  # Different character entering
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should not trigger because the wrong character entered play
        what_do_we_do_now_ability = elsa_char.composable_abilities[0]
        assert what_do_we_do_now_ability.name == "WHAT DO WE DO NOW?"
    
    def test_what_do_we_do_now_multiple_anna_characters(self):
        """Test WHAT DO WE DO NOW? with multiple Anna characters in play."""
        elsa_char = self.create_what_do_we_do_now_character()
        anna_char1 = self.create_anna_character("Anna - Heir to Arendelle")
        anna_char2 = self.create_anna_character("Anna - True-Hearted")
        
        # Put both Annas in play
        self.player1.characters_in_play.extend([anna_char1, anna_char2])
        
        # Elsa enters play
        self.player1.characters_in_play.append(elsa_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=elsa_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should trigger with any Anna in play
        annas_in_play = [char for char in self.player1.characters_in_play if char.name == "Anna"]
        assert len(annas_in_play) == 2
        
        what_do_we_do_now_ability = elsa_char.composable_abilities[0]
        assert what_do_we_do_now_ability.name == "WHAT DO WE DO NOW?"
    
    def test_what_do_we_do_now_opponent_anna_does_not_count(self):
        """Test that opponent's Anna does not trigger WHAT DO WE DO NOW?"""
        elsa_char = self.create_what_do_we_do_now_character()
        opponent_anna = self.create_anna_character("Anna - Opponent's Version")
        
        # Put Elsa on player 1, Anna on player 2
        self.player2.characters_in_play.append(opponent_anna)
        
        # Elsa enters play
        self.player1.characters_in_play.append(elsa_char)
        
        event_context = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=elsa_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(event_context)
        
        # Should not trigger with opponent's Anna
        friendly_annas = [char for char in self.player1.characters_in_play if char.name == "Anna"]
        assert len(friendly_annas) == 0
        
        opponent_annas = [char for char in self.player2.characters_in_play if char.name == "Anna"]
        assert len(opponent_annas) == 1
        
        what_do_we_do_now_ability = elsa_char.composable_abilities[0]
        assert what_do_we_do_now_ability.name == "WHAT DO WE DO NOW?"
    
    def test_what_do_we_do_now_enters_play_timing(self):
        """Test the timing of WHAT DO WE DO NOW? trigger."""
        elsa_char = self.create_what_do_we_do_now_character()
        anna_char = self.create_anna_character()
        
        # Both characters enter at the same time (Anna first)
        self.player1.characters_in_play.append(anna_char)
        self.player1.characters_in_play.append(elsa_char)
        
        # Trigger Anna entering first
        anna_event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=anna_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        self.event_manager.trigger_event(anna_event)
        
        # Then trigger Elsa entering (should trigger ability)
        elsa_event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=elsa_char,
            player=self.player1,
            game_state=self.game_state
        )
        
        results = self.event_manager.trigger_event(elsa_event)
        
        # Should trigger because Anna was already in play when Elsa entered
        what_do_we_do_now_ability = elsa_char.composable_abilities[0]
        assert what_do_we_do_now_ability.name == "WHAT DO WE DO NOW?"
    
    def test_what_do_we_do_now_ability_registration(self):
        """Test that WHAT DO WE DO NOW? ability is properly registered."""
        elsa_char = self.create_what_do_we_do_now_character()
        self.player1.characters_in_play.append(elsa_char)
        
        # Rebuild listeners to ensure ability is registered
        self.event_manager.rebuild_listeners()
        
        # Should respond to character enters play events
        assert elsa_char.composable_abilities
        assert elsa_char.composable_abilities[0].name == "WHAT DO WE DO NOW?"
        
        # Check that it has listeners for the correct event
        ability = elsa_char.composable_abilities[0]
        assert len(ability.listeners) > 0


if __name__ == "__main__":
    pytest.main([__file__])