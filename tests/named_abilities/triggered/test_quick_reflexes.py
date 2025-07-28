"""Integration tests for QUICK REFLEXES - During your turn, this character gains Evasive."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, PassMove, ChallengeMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.static.quick_reflexes import create_quick_reflexes


class TestQuickReflexesIntegration(GameEngineTestBase):
    """Integration tests for QUICK REFLEXES named ability."""
    
    def create_quick_reflexes_character(self, name="Nick Wilde", cost=3, strength=2, willpower=3):
        """Create a test character with QUICK REFLEXES ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower
        )
        
        # Add QUICK REFLEXES ability
        ability_data = {"name": "QUICK REFLEXES", "type": "triggered"}
        quick_reflexes_ability = create_quick_reflexes(character, ability_data)
        character.composable_abilities.append(quick_reflexes_ability)
        
        return character
    
    def create_normal_character(self, name="Normal Character", cost=2, strength=1, willpower=2):
        """Create a normal character without any special abilities."""
        return self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower
        )
    
    def test_quick_reflexes_ability_creation(self):
        """Test that QUICK REFLEXES ability creates correctly."""
        character = self.create_quick_reflexes_character("Nick Wilde")
        
        # Should have exactly one ability
        assert len(character.composable_abilities) == 1
        
        # Ability should be named correctly
        ability = character.composable_abilities[0]
        assert ability.name == "QUICK REFLEXES"
    
    def test_quick_reflexes_grants_evasive_on_controllers_turn(self):
        """Test that character gains Evasive during controller's turn."""
        # Create character with QUICK REFLEXES
        quick_char = self.create_quick_reflexes_character("Nick Wilde - Sly Fox")
        quick_char.controller = self.game_state.current_player  # Current player is already set by base class
        
        # Play the character using the helper method
        self.play_character(quick_char, quick_char.controller)
        
        # Process any triggered abilities
        self.process_ability_messages()
        
        # Verify character has Evasive during controller's turn
        assert quick_char.has_evasive_ability()
        assert quick_char.metadata.get('has_evasive', False)
        assert 'Evasive' in quick_char.get_active_abilities(self.game_state)
    
    def test_quick_reflexes_removes_evasive_on_opponents_turn(self):
        """Test that character loses Evasive during opponent's turn."""
        # Create character with QUICK REFLEXES
        quick_char = self.create_quick_reflexes_character("Nick Wilde - Sly Fox")
        quick_char.controller = self.player1
        
        # Play the character using the helper method (ensures proper turn setup)
        self.play_character(quick_char, self.player1)
        self.process_ability_messages()
        
        # Verify character has Evasive during controller's turn
        assert quick_char.has_evasive_ability()
        
        # Pass turn to switch to opponent
        self.game_engine.next_message(PassMove())
        self.process_ability_messages()
        
        # Verify character lost Evasive on opponent's turn
        assert not quick_char.has_evasive_ability()
        assert not quick_char.metadata.get('has_evasive', False)
        assert 'Evasive' not in quick_char.get_active_abilities(self.game_engine.game_state)
    
    def test_quick_reflexes_immediate_on_play(self):
        """Test that character gets Evasive immediately when played during controller's turn."""
        # Create character with QUICK REFLEXES
        quick_char = self.create_quick_reflexes_character("Nick Wilde - Sly Fox")
        quick_char.controller = self.player1
        
        # Initially character should not have Evasive
        assert not quick_char.has_evasive_ability()
        
        # Play the character using the helper method
        self.play_character(quick_char, self.player1)
        self.process_ability_messages()
        
        # Should immediately have Evasive since it's controller's turn
        assert quick_char.has_evasive_ability()
        assert quick_char.metadata.get('has_evasive', False)
    
    def test_quick_reflexes_challenge_interaction(self):
        """Test that QUICK REFLEXES Evasive properly prevents challenges."""
        # Create characters
        quick_char = self.create_quick_reflexes_character("Nick Wilde - Sly Fox")
        quick_char.controller = self.player1
        
        normal_char = self.create_normal_character("Normal Attacker")
        normal_char.controller = self.player2
        
        # Play the quick character on player1's turn
        self.play_character(quick_char, self.player1)
        self.process_ability_messages()
        
        # Verify quick character has Evasive during controller's turn
        assert quick_char.has_evasive_ability()
        
        # Put normal character directly in play for player2
        self.player2.characters_in_play.append(normal_char)
        normal_char.is_dry = True  # Ready to act
        
        # Switch turns - Pass to opponent
        self.game_engine.next_message(PassMove())
        self.process_ability_messages()
        
        # Verify quick character lost evasive (it's now opponent's turn)
        assert not quick_char.has_evasive_ability()
        
    def test_quick_reflexes_turn_transitions(self):
        """Test that QUICK REFLEXES properly handles multiple turn transitions."""
        # Create character with QUICK REFLEXES
        quick_char = self.create_quick_reflexes_character("Nick Wilde - Sly Fox")
        quick_char.controller = self.player1
        
        # Play character and verify initial Evasive state
        self.play_character(quick_char, self.player1)
        self.process_ability_messages()
        assert quick_char.has_evasive_ability()
        
        # Pass turn to player2 (Alice -> Bob)
        self.game_engine.next_message(PassMove())
        self.process_ability_messages()
        
        # Should lose Evasive on opponent's turn
        assert not quick_char.has_evasive_ability()
        
        # Pass through Bob's turn to get back to Alice
        # Bob advances to his PLAY phase quickly, then passes to Alice
        self.game_engine.next_message(PassMove())  # Bob READY -> Bob PLAY
        self.process_ability_messages()
        
        self.game_engine.next_message(PassMove())  # Bob PLAY -> Alice READY
        self.process_ability_messages()
        
        # Should regain Evasive when back to controller's turn
        assert quick_char.has_evasive_ability()
    
    def test_quick_reflexes_with_display_info(self):
        """Test that QUICK REFLEXES shows up correctly in display info."""
        # Create character with QUICK REFLEXES
        quick_char = self.create_quick_reflexes_character("Nick Wilde - Sly Fox")
        quick_char.controller = self.player1
        
        # Play character on controller's turn
        self.play_character(quick_char, self.player1)
        self.process_ability_messages()
        
        # During controller's turn - should show both abilities
        display_info = quick_char.get_display_info(self.game_engine.game_state)
        abilities = display_info['abilities']
        assert 'QUICK REFLEXES' in abilities
        assert 'Evasive' in abilities
        
        # Pass turn to opponent
        self.game_engine.next_message(PassMove())
        self.process_ability_messages()
        
        # During opponent's turn - should show QUICK REFLEXES but not Evasive
        display_info = quick_char.get_display_info(self.game_engine.game_state)
        abilities = display_info['abilities']
        assert 'QUICK REFLEXES' in abilities
        assert 'Evasive' not in abilities
    
    def test_quick_reflexes_state_persistence(self):
        """Test that QUICK REFLEXES state changes persist correctly."""
        # Create two characters with QUICK REFLEXES
        quick_char = self.create_quick_reflexes_character("Nick Wilde - Sly Fox")
        quick_char.controller = self.player1
        
        quick_char2 = self.create_quick_reflexes_character("Nick Wilde - Copy")  
        quick_char2.controller = self.player1
        
        # Both should have unique IDs (test state key uniqueness)
        assert id(quick_char) != id(quick_char2)
        
        # Play both characters
        self.play_character(quick_char, self.player1)
        self.process_ability_messages()
        
        self.player1.hand.append(quick_char2)
        self.game_engine.next_message(PlayMove(quick_char2))
        self.process_ability_messages()
        
        # Both should have Evasive during controller's turn
        assert quick_char.has_evasive_ability()
        assert quick_char2.has_evasive_ability()
        
        # State changes should be independent
        quick_char.metadata.pop('has_evasive', None)
        assert not quick_char.has_evasive_ability()
        assert quick_char2.has_evasive_ability()  # Other character unaffected
    
    def test_quick_reflexes_multiple_triggers(self):
        """Test that QUICK REFLEXES handles multiple evaluation triggers correctly."""
        # Create character with QUICK REFLEXES
        quick_char = self.create_quick_reflexes_character("Nick Wilde - Sly Fox")
        quick_char.controller = self.player1
        
        # Play character and verify initial state
        self.play_character(quick_char, self.player1)
        self.process_ability_messages()
        
        # Should have Evasive during controller's turn
        assert quick_char.has_evasive_ability()
        
        # One complete turn cycle to test trigger handling
        # Pass to opponent (Alice PLAY -> Bob READY)
        self.game_engine.next_message(PassMove())
        self.process_ability_messages()
        assert not quick_char.has_evasive_ability()
        
        # Pass through Bob's turn to get back to Alice
        self.game_engine.next_message(PassMove())  # Bob READY -> Bob PLAY
        self.process_ability_messages()
        assert not quick_char.has_evasive_ability()  # Still Bob's turn
        
        # Pass back to Alice (Bob PLAY -> Alice READY)
        self.game_engine.next_message(PassMove())
        self.process_ability_messages()
        assert quick_char.has_evasive_ability()  # Back to controller's turn