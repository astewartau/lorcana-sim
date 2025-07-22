"""Integration tests for DANCE-OFF - When this character or any of your Mickey Mouse characters challenges, gain 1 lore."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, ChallengeMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.dance_off import create_dance_off


class TestDanceOffIntegration(GameEngineTestBase):
    """Integration tests for DANCE-OFF named ability."""
    
    def create_dance_off_character(self, name="Dance Character", cost=3, strength=2, willpower=3):
        """Create a test character with DANCE-OFF ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            color=CardColor.AMBER,
            subtypes=["Hero"]
        )
        
        # Add the DANCE-OFF ability
        ability_data = {"name": "DANCE-OFF", "type": "triggered"}
        dance_off_ability = create_dance_off(character, ability_data)
        if not hasattr(character, 'composable_abilities') or character.composable_abilities is None:
            character.composable_abilities = []
        character.composable_abilities.append(dance_off_ability)
        return character
    
    def create_mickey_mouse_character(self, name="Mickey Mouse", cost=2, strength=1, willpower=2):
        """Create a Mickey Mouse character."""
        return self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            color=CardColor.AMBER,
            subtypes=["Hero", "Mouse"]
        )
    
    def test_dance_off_creation(self):
        """Unit test: Verify DANCE-OFF ability creates correctly."""
        character = self.create_dance_off_character()
        
        assert len(character.composable_abilities) == 1
        ability = character.composable_abilities[0]
        assert "DANCE-OFF" in ability.name
    
    def test_dance_off_triggers_when_self_challenges(self):
        """Integration test: DANCE-OFF triggers when the character itself challenges."""
        # Create character with DANCE-OFF ability
        dance_character = self.create_dance_off_character(
            name="Dance Character", 
            cost=4, 
            strength=3
        )
        
        # Create opponent character to challenge
        opponent_character = self.create_test_character(
            name="Opponent Character",
            strength=2,
            willpower=3
        )
        
        # Set up game state - put character in hand BEFORE GameEngine init to register abilities
        self.player1.hand = [dance_character]
        self.player2.characters_in_play = [opponent_character]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        dance_character.controller = self.player1
        opponent_character.controller = self.player2
        
        # Play the dance character to register abilities properly
        play_move = PlayMove(dance_character)
        play_message = self.game_engine.next_message(play_move)
        
        # Verify the character was played
        assert play_message.type == MessageType.STEP_EXECUTED
        assert dance_character in self.player1.characters_in_play
        
        # Process any enter-play triggers
        enter_play_message = self.game_engine.next_message()
        if enter_play_message.type == MessageType.STEP_EXECUTED:
            # There was an enter-play trigger, process it
            pass
        
        # Make dance character ready to challenge (not exerted, dry ink)
        dance_character.exerted = False
        dance_character.is_dry = True
        
        # Make opponent character challengeable (exerted)
        opponent_character.exerted = True
        opponent_character.is_dry = True
        
        # Record initial lore
        initial_lore = self.player1.lore
        
        # Perform the challenge
        challenge_move = ChallengeMove(dance_character, opponent_character)
        message = self.game_engine.next_message(challenge_move)
        
        # Verify challenge occurred
        assert message.type == MessageType.STEP_EXECUTED
        # Verify challenge action occurred
        assert message.type == MessageType.STEP_EXECUTED
        
        # Get the DANCE-OFF ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Get the lore gain effect message
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Try one more message call in case there's another queued effect
        try:
            extra_message = self.game_engine.next_message()
        except Exception as e:
            pass  # No more messages available
        
        # Verify lore was gained
        assert self.player1.lore == initial_lore + 1
    
    def test_dance_off_triggers_when_mickey_mouse_challenges(self):
        """Integration test: DANCE-OFF triggers when a Mickey Mouse character challenges."""
        # Create character with DANCE-OFF ability
        dance_character = self.create_dance_off_character(
            name="Dance Character", 
            cost=4
        )
        
        # Create Mickey Mouse character
        mickey_character = self.create_mickey_mouse_character(
            name="Mickey Mouse",
            strength=3
        )
        
        # Create opponent character to challenge
        opponent_character = self.create_test_character(
            name="Opponent Character",
            strength=2,
            willpower=3
        )
        
        # Set up game state
        self.player1.characters_in_play = [dance_character, mickey_character]
        self.player2.characters_in_play = [opponent_character]
        
        # Make Mickey ready to challenge
        mickey_character.exerted = False
        mickey_character.is_dry = True
        
        # Make opponent challengeable
        opponent_character.exerted = True
        opponent_character.is_dry = True
        
        # Set controllers
        dance_character.controller = self.player1
        mickey_character.controller = self.player1
        opponent_character.controller = self.player2
        
        # Record initial lore
        initial_lore = self.player1.lore
        
        # Mickey challenges
        challenge_move = ChallengeMove(mickey_character, opponent_character)
        message = self.game_engine.next_message(challenge_move)
        
        # Verify challenge occurred
        assert message.type == MessageType.STEP_EXECUTED
        # Verify challenge action occurred
        assert message.type == MessageType.STEP_EXECUTED
        
        # Get the DANCE-OFF ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Get the lore gain effect message
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Try one more message call in case there's another queued effect
        try:
            extra_message = self.game_engine.next_message()
        except Exception as e:
            pass  # No more messages available
        
        # Verify lore was gained
        assert self.player1.lore == initial_lore + 1
    
    def test_dance_off_does_not_trigger_on_opponent_challenge(self):
        """Test that DANCE-OFF does not trigger when opponent's characters challenge."""
        # Create character with DANCE-OFF ability
        dance_character = self.create_dance_off_character(
            name="Dance Character"
        )
        
        # Create opponent characters
        opponent_attacker = self.create_test_character(
            name="Opponent Attacker",
            strength=3
        )
        opponent_defender = self.create_test_character(
            name="Opponent Defender",
            strength=2,
            willpower=3
        )
        
        # Set up game state
        self.player1.characters_in_play = [dance_character]
        self.player2.characters_in_play = [opponent_attacker, opponent_defender]
        
        # Set up for opponent challenge
        opponent_attacker.exerted = False
        opponent_attacker.is_dry = True
        opponent_defender.exerted = True
        opponent_defender.is_dry = True
        
        # Set controllers
        dance_character.controller = self.player1
        opponent_attacker.controller = self.player2
        opponent_defender.controller = self.player2
        
        # Switch to player 2's turn
        self.game_state.current_player_index = 1
        
        # Record initial lore
        initial_lore = self.player1.lore
        
        # Opponent challenges their own character (no trigger expected)
        challenge_move = ChallengeMove(opponent_attacker, opponent_defender)
        message = self.game_engine.next_message(challenge_move)
        
        # Verify challenge occurred
        assert message.type == MessageType.STEP_EXECUTED
        # Verify challenge action occurred
        assert message.type == MessageType.STEP_EXECUTED
        
        # DANCE-OFF should NOT trigger - player1's lore should not increase
        assert self.player1.lore == initial_lore
    
    def test_dance_off_with_multiple_mickey_mouse_characters(self):
        """Test DANCE-OFF with multiple Mickey Mouse characters."""
        # Create character with DANCE-OFF ability
        dance_character = self.create_dance_off_character(
            name="Dance Character"
        )
        
        # Create multiple Mickey Mouse characters
        mickey1 = self.create_mickey_mouse_character(
            name="Mickey Mouse",
            strength=2
        )
        mickey2 = self.create_mickey_mouse_character(
            name="Mickey Mouse", 
            strength=3
        )
        
        # Create opponent characters for each Mickey to challenge
        opponent1 = self.create_test_character(name="Opponent 1", willpower=2)
        opponent2 = self.create_test_character(name="Opponent 2", willpower=3)
        
        # Set up game state
        self.player1.characters_in_play = [dance_character, mickey1, mickey2]
        self.player2.characters_in_play = [opponent1, opponent2]
        
        # Set up for challenges
        mickey1.exerted = False
        mickey1.is_dry = True
        mickey2.exerted = False  
        mickey2.is_dry = True
        opponent1.exerted = True
        opponent1.is_dry = True
        opponent2.exerted = True
        opponent2.is_dry = True
        
        # Set controllers
        for char in [dance_character, mickey1, mickey2]:
            char.controller = self.player1
        for char in [opponent1, opponent2]:
            char.controller = self.player2
        
        # Record initial lore
        initial_lore = self.player1.lore
        
        # First Mickey challenges
        challenge_move1 = ChallengeMove(mickey1, opponent1)
        message1 = self.game_engine.next_message(challenge_move1)
        
        # Verify first challenge
        assert message1.type == MessageType.STEP_EXECUTED
        
        # Get DANCE-OFF trigger and effect
        trigger_message1 = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message1.event_data is not None or trigger_message1.step is not None
        
        effect_message1 = self.game_engine.next_message()
        # Verify effect message
        assert effect_message1.type == MessageType.STEP_EXECUTED
        
        # Verify lore increased by 1
        assert self.player1.lore == initial_lore + 1
        
        # Second Mickey challenges (if still able)
        if mickey2.exerted == False and len([c for c in self.player2.characters_in_play if c.exerted]) > 0:
            challenge_move2 = ChallengeMove(mickey2, opponent2)
            message2 = self.game_engine.next_message(challenge_move2)
            
            # Verify second challenge
            assert message2.type == MessageType.STEP_EXECUTED
            
            # Get second DANCE-OFF trigger and effect
            trigger_message2 = self.game_engine.next_message()
            # Check that message has event data about the ability trigger
            assert trigger_message2.event_data is not None or trigger_message2.step is not None
            
            effect_message2 = self.game_engine.next_message()
            # Verify effect message
            assert effect_message2.type == MessageType.STEP_EXECUTED
            
            # Verify total lore increased by 2
            assert self.player1.lore == initial_lore + 2
    
    def test_dance_off_no_valid_targets(self):
        """Test DANCE-OFF when character wants to challenge but no valid targets exist."""
        # Create character with DANCE-OFF ability
        dance_character = self.create_dance_off_character(
            name="Dance Character", 
            strength=3
        )
        
        # Create opponent character that cannot be challenged (not exerted)
        opponent_character = self.create_test_character(
            name="Ready Opponent",
            strength=2,
            willpower=3
        )
        
        # Set up game state
        self.player1.characters_in_play = [dance_character]
        self.player2.characters_in_play = [opponent_character]
        
        # Make dance character ready but opponent not challengeable
        dance_character.exerted = False
        dance_character.is_dry = True
        opponent_character.exerted = False  # Not exerted = not challengeable
        opponent_character.is_dry = True
        
        # Set controllers
        dance_character.controller = self.player1
        opponent_character.controller = self.player2
        
        # Record initial lore
        initial_lore = self.player1.lore
        
        # Attempting to challenge should fail - no valid targets
        # DANCE-OFF should not trigger if no challenge actually occurs
        
        # Verify no valid challenge targets exist
        from lorcana_sim.engine.move_validator import MoveValidator
        validator = MoveValidator(self.game_state)
        challenges = validator.get_possible_challenges()
        assert len(challenges) == 0, "Should be no valid challenges when opponent is ready"
        
        # Lore should remain unchanged
        assert self.player1.lore == initial_lore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])