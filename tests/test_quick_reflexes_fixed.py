"""Final test demonstrating Quick Reflexes working correctly as a static ability."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.engine.game_moves import PlayMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities import NamedAbilityRegistry


class TestQuickReflexesFixed(GameEngineTestBase):
    """Test that Quick Reflexes is correctly implemented as a static ability."""
    
    def test_quick_reflexes_static_ability_works(self):
        """Test that Quick Reflexes grants Evasive during controller's turn."""
        # Create a character
        character = self.create_test_character(
            name="Test Character",
            cost=2,
            strength=2,
            willpower=3
        )
        
        # Add Quick Reflexes using the registry (as card loader would)
        ability_data = {"name": "QUICK REFLEXES", "type": "static"}
        quick_reflexes = NamedAbilityRegistry.create_ability("QUICK REFLEXES", character, ability_data)
        assert quick_reflexes is not None, "QUICK REFLEXES should be registered"
        character.composable_abilities.append(quick_reflexes)
        
        # Set controller
        character.controller = self.player1
        
        # Add to hand
        self.player1.hand.append(character)
        
        # Play the character
        play_msg = self.game_engine.next_message(PlayMove(character))
        assert play_msg.type == MessageType.STEP_EXECUTED
        
        # Process all messages
        messages = []
        while True:
            msg = self.game_engine.next_message()
            if msg.type == MessageType.ACTION_REQUIRED:
                break
            messages.append(msg.step)
            if len(messages) > 10:
                break
        
        print("\n=== MESSAGES ===")
        for msg in messages:
            print(f"- {msg}")
        
        # Check final state
        print("\n=== FINAL STATE ===")
        print(f"Character in play: {character in self.player1.characters_in_play}")
        print(f"Current player: {self.game_state.current_player.name}")
        print(f"Character controller: {character.controller.name}")
        print(f"Has Evasive: {character.has_evasive_ability()}")
        print(f"Metadata: {character.metadata}")
        print(f"Active abilities: {character.get_active_abilities(self.game_state)}")
        
        # Verify character has Evasive
        assert character in self.player1.characters_in_play
        assert character.has_evasive_ability(), "Character should have Evasive during controller's turn"
        
        # The ability messages should have included Quick Reflexes
        quick_reflexes_triggered = any("QUICK REFLEXES" in msg for msg in messages)
        assert quick_reflexes_triggered, "QUICK REFLEXES should have triggered when character was played"
        
        print("\n✅ SUCCESS: Quick Reflexes correctly grants Evasive during controller's turn!")
        
    def test_quick_reflexes_turns_off_on_opponent_turn(self):
        """Test that Quick Reflexes removes Evasive during opponent's turn."""
        # Create character with Quick Reflexes
        character = self.create_test_character(
            name="Test Character",
            cost=2,
            strength=2,
            willpower=3
        )
        
        ability_data = {"name": "QUICK REFLEXES", "type": "static"}
        quick_reflexes = NamedAbilityRegistry.create_ability("QUICK REFLEXES", character, ability_data)
        character.composable_abilities.append(quick_reflexes)
        character.controller = self.player1
        
        # Play character
        self.play_character(character, self.player1)
        self.process_ability_messages()
        
        # Should have Evasive during controller's turn
        assert character.has_evasive_ability()
        
        # Pass turn
        from lorcana_sim.engine.game_moves import PassMove
        self.game_engine.next_message(PassMove())
        self.process_ability_messages()
        
        # Should lose Evasive during opponent's turn
        print(f"\nAfter turn change:")
        print(f"Current player: {self.game_state.current_player.name}")
        print(f"Has Evasive: {character.has_evasive_ability()}")
        
        assert not character.has_evasive_ability(), "Character should lose Evasive during opponent's turn"
        
        print("\n✅ SUCCESS: Quick Reflexes correctly removes Evasive during opponent's turn!")