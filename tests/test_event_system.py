"""Tests for the event system and triggered abilities."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.engine.event_system import GameEvent, EventContext
from lorcana_sim.models.game.game_state import GameAction
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestEventSystem:
    """Test the event system and triggered abilities."""
    
    def test_support_triggers_on_quest(self):
        """Test that Support ability triggers when character quests."""
        # Create Support ability
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create characters with different lore values for interesting support
        support_char = create_character_with_ability("Supporter", support_ability, lore=2)
        target_char = create_test_character("Target", lore=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char, target_char], []
        )
        
        # Verify Support ability is registered for triggering
        assert len(engine.event_manager._event_listeners[GameEvent.CHARACTER_QUESTS]) == 1
        
        # Quest with the Support character
        success, message = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': support_char})
        
        # Verify the quest succeeded
        assert success == True
        assert "quested" in message
        assert "Triggered" in message  # Should show triggered abilities
        assert "supported" in message.lower()
        
        # Verify support bonus was applied
        # The support character should have given its lore (2) as bonus to target
        # Original quest: support_char lore (2) + support bonus to target (2) = 4 total lore
        assert target_char.temporary_lore_bonus == 2
    
    def test_support_only_triggers_for_own_character(self):
        """Test that Support only triggers when the character with Support quests."""
        # Create abilities
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create characters
        support_char = create_character_with_ability("Supporter", support_ability, lore=2)
        normal_char = create_test_character("Normal", lore=1)
        target_char = create_test_character("Target", lore=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char, normal_char, target_char], []
        )
        
        # Quest with the normal character (not the support character)
        success, message = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': normal_char})
        
        # Verify the quest succeeded but no support triggered
        assert success == True
        assert "quested" in message
        assert "Triggered" not in message  # Should NOT show triggered abilities
        assert "supported" not in message.lower()
        
        # Verify no support bonus was applied to any character
        assert not hasattr(target_char, 'temporary_lore_bonus') or target_char.temporary_lore_bonus == 0
    
    def test_event_manager_registers_abilities_on_character_play(self):
        """Test that event manager registers new triggered abilities when characters are played."""
        # Create Support ability
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        support_char = create_character_with_ability("Supporter", support_ability)
        
        # Setup game with no characters initially
        game_state, validator, engine = setup_game_with_characters([], [])
        
        # Initially no listeners
        assert len(engine.event_manager._event_listeners.get(GameEvent.CHARACTER_QUESTS, [])) == 0
        
        # Add character to hand and play it
        game_state.current_player.hand.append(support_char)
        # Add ink to afford the character (add cards to inkwell)
        for i in range(10):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        success, message = engine.execute_action(GameAction.PLAY_CHARACTER, {'card': support_char})
        
        # Verify character was played
        assert success == True
        
        # Verify the triggered ability was registered
        assert len(engine.event_manager._event_listeners[GameEvent.CHARACTER_QUESTS]) == 1
    
    def test_event_manager_unregisters_abilities_on_character_banishment(self):
        """Test that abilities are unregistered when characters are banished."""
        # Create characters with Support
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        support_char = create_character_with_ability("Supporter", support_ability, willpower=1)
        attacker = create_test_character("Attacker", strength=2)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char], [attacker]
        )
        
        # Verify ability is registered
        assert len(engine.event_manager._event_listeners[GameEvent.CHARACTER_QUESTS]) == 1
        
        # Switch to opponent to challenge
        game_state.current_player_index = 1
        
        # Challenge and banish the support character
        success, message = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': attacker, 
            'defender': support_char
        })
        
        # Verify challenge succeeded and character was banished
        assert success == True
        assert "banished" in message
        
        # Verify the ability was unregistered
        assert len(engine.event_manager._event_listeners.get(GameEvent.CHARACTER_QUESTS, [])) == 0
    
    def test_multiple_support_characters_all_trigger(self):
        """Test that multiple Support characters can all trigger on different quests."""
        # Create multiple Support characters
        support_ability1 = KeywordRegistry.create_keyword_ability('Support')
        support_ability2 = KeywordRegistry.create_keyword_ability('Support')
        
        support_char1 = create_character_with_ability("Supporter1", support_ability1, lore=1)
        support_char2 = create_character_with_ability("Supporter2", support_ability2, lore=2)
        target_char = create_test_character("Target", lore=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char1, support_char2, target_char], []
        )
        
        # Verify both Support abilities are registered
        assert len(engine.event_manager._event_listeners[GameEvent.CHARACTER_QUESTS]) == 2
        
        # Quest with first support character
        success1, message1 = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': support_char1})
        assert success1 == True
        assert "supported" in message1.lower()
        
        # Clear temporary bonus and ready the second character
        target_char.temporary_lore_bonus = 0
        support_char2.exerted = False
        
        # Quest with second support character
        success2, message2 = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': support_char2})
        assert success2 == True
        assert "supported" in message2.lower()
        
        # The second support character should support the first one (since target was cleared)
        # Verify the second support gave its lore value (2) as bonus to support_char1
        assert getattr(support_char1, 'temporary_lore_bonus', 0) == 2