"""Tests for cross-ability interactions and general execution framework."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.engine.event_system import GameEvent
from lorcana_sim.models.game.game_state import GameAction
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestAbilityExecutionFramework:
    """Test the general ability execution framework and cross-ability interactions."""
    
    def test_multiple_triggered_abilities_register_properly(self):
        """Test that multiple triggered abilities from different characters register properly."""
        # Create different triggered abilities
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create characters with triggered abilities
        support_char = create_character_with_ability("Supporter", support_ability, lore=2)
        normal_char = create_test_character("Normal", lore=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char, normal_char], []
        )
        
        # Verify only triggered abilities are registered
        quest_listeners = engine.event_manager._event_listeners.get(GameEvent.CHARACTER_QUESTS, [])
        assert len(quest_listeners) == 1  # Only Support should be registered
        assert quest_listeners[0] == support_ability
    
    def test_ability_registration_and_unregistration_lifecycle(self):
        """Test that abilities are properly registered when characters enter and leave play."""
        # Create triggered ability
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        support_char = create_character_with_ability("Supporter", support_ability, willpower=1)
        attacker = create_test_character("Attacker", strength=2)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char], [attacker]
        )
        
        # Verify ability is registered
        assert len(engine.event_manager._event_listeners[GameEvent.CHARACTER_QUESTS]) == 1
        
        # Switch to opponent and banish the support character
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
    
    def test_passive_abilities_dont_register_for_events(self):
        """Test that passive abilities don't register for event triggering."""
        # Create passive abilities
        evasive_ability = KeywordRegistry.create_keyword_ability('Evasive')
        bodyguard_ability = KeywordRegistry.create_keyword_ability('Bodyguard')
        ward_ability = KeywordRegistry.create_keyword_ability('Ward')
        
        # Create characters with passive abilities
        evasive_char = create_character_with_ability("Evasive", evasive_ability)
        bodyguard_char = create_character_with_ability("Bodyguard", bodyguard_ability)
        ward_char = create_character_with_ability("Ward", ward_ability)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [evasive_char, bodyguard_char, ward_char], []
        )
        
        # Verify no passive abilities registered for events
        for event_type in GameEvent:
            listeners = engine.event_manager._event_listeners.get(event_type, [])
            assert len(listeners) == 0, f"Passive abilities should not register for {event_type}"
    
    def test_event_manager_rebuilds_listeners_correctly(self):
        """Test that the event manager can rebuild its listeners from current game state."""
        # Create triggered abilities
        support_ability1 = KeywordRegistry.create_keyword_ability('Support')
        support_ability2 = KeywordRegistry.create_keyword_ability('Support')
        
        support_char1 = create_character_with_ability("Supporter1", support_ability1)
        support_char2 = create_character_with_ability("Supporter2", support_ability2)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char1, support_char2], []
        )
        
        # Verify both abilities are registered
        assert len(engine.event_manager._event_listeners[GameEvent.CHARACTER_QUESTS]) == 2
        
        # Clear all listeners
        engine.event_manager._event_listeners.clear()
        assert len(engine.event_manager._event_listeners.get(GameEvent.CHARACTER_QUESTS, [])) == 0
        
        # Rebuild listeners
        engine.event_manager.rebuild_listeners()
        
        # Verify listeners were restored
        assert len(engine.event_manager._event_listeners[GameEvent.CHARACTER_QUESTS]) == 2
    
    def test_cross_ability_interactions_bodyguard_vs_evasive(self):
        """Test how different abilities interact - Bodyguard vs Evasive targeting."""
        # Create abilities
        bodyguard_ability = KeywordRegistry.create_keyword_ability('Bodyguard')
        evasive_ability = KeywordRegistry.create_keyword_ability('Evasive')
        
        # Create characters
        bodyguard_char = create_character_with_ability("Bodyguard", bodyguard_ability)
        evasive_char = create_character_with_ability("Evasive", evasive_ability) 
        normal_attacker = create_test_character("Attacker")
        
        # Setup game - defenders have both Bodyguard and Evasive
        game_state, validator, engine = setup_game_with_characters(
            [bodyguard_char, evasive_char], [normal_attacker]
        )
        
        # Switch to attacker
        game_state.current_player_index = 1
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Normal attacker can't challenge Evasive, even with Bodyguard present
        # This tests that multiple passive abilities work together correctly
        assert len(challenge_actions) == 1  # Can only challenge Bodyguard
        
        action, params = challenge_actions[0]
        assert params['defender'] == bodyguard_char  # Must be the bodyguard
        
        # Double-check individual ability rules
        assert validator.can_challenge(normal_attacker, bodyguard_char) == True
        assert validator.can_challenge(normal_attacker, evasive_char) == False
    
    def test_damage_integration_with_resist_and_bodyguard(self):
        """Test damage calculation works with multiple abilities."""
        # Create abilities
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        bodyguard_ability = KeywordRegistry.create_keyword_ability('Bodyguard')
        
        # Create characters - bodyguard with resist  
        tanky_bodyguard = create_character_with_ability("Tank Guard", bodyguard_ability, willpower=6)
        tanky_bodyguard.abilities.append(resist_ability)  # Add Resist to the same character
        
        normal_char = create_test_character("Squishy", willpower=2)
        strong_attacker = create_test_character("Dragon", strength=5)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [tanky_bodyguard, normal_char], [strong_attacker]
        )
        
        # Switch to attacker
        game_state.current_player_index = 1
        
        # Verify targeting: can only challenge bodyguard due to Bodyguard ability
        legal_actions = validator.get_all_legal_actions()
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        assert len(challenge_actions) == 1
        action, params = challenge_actions[0]
        assert params['defender'] == tanky_bodyguard
        
        # Execute the challenge
        success, message = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': strong_attacker,
            'defender': tanky_bodyguard
        })
        
        assert success == True
        
        # Verify damage was reduced by Resist: 5 base damage - 2 resist = 3 damage
        expected_damage = 5 - 2
        assert tanky_bodyguard.damage == expected_damage
        
        # Bodyguard should still be alive (6 willpower - 3 damage = 3 remaining)
        assert tanky_bodyguard.is_alive == True
        
        # Normal character should be untouched
        assert normal_char.damage == 0
        assert normal_char.is_alive == True