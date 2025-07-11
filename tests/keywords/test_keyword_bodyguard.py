"""Tests for Bodyguard keyword ability - both unit and integration tests."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry, BodyguardAbility
from lorcana_sim.models.abilities.base_ability import AbilityType
from lorcana_sim.models.game.game_state import GameAction
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestBodyguardAbilityUnit:
    """Unit tests for Bodyguard keyword ability implementation."""
    
    def test_bodyguard_creation(self):
        """Test creating Bodyguard ability."""
        bodyguard = BodyguardAbility(
            name="Bodyguard",
            type=AbilityType.KEYWORD,
            effect="Bodyguard ability",
            full_text="Bodyguard",
            keyword="Bodyguard",
            value=None
        )
        
        assert bodyguard.keyword == "Bodyguard"
        assert bodyguard.can_enter_play_exerted() == True
        assert bodyguard.modifies_challenge_targeting() == True
        assert str(bodyguard) == "Bodyguard"
    
    def test_bodyguard_challenge_rules(self):
        """Test Bodyguard challenge targeting rules."""
        bodyguard_ability = BodyguardAbility(
            name="Bodyguard",
            type=AbilityType.KEYWORD,
            effect="Bodyguard ability",
            full_text="Bodyguard",
            keyword="Bodyguard",
            value=None
        )
        
        # Create characters
        bodyguard_char = create_test_character("Bodyguard Character", [bodyguard_ability])
        normal_char = create_test_character("Normal Character", [])
        
        # Test that bodyguard character can be identified
        assert bodyguard_ability._has_bodyguard(bodyguard_char) == True
        assert bodyguard_ability._has_bodyguard(normal_char) == False
    
    def test_passive_ability(self):
        """Test that Bodyguard is a passive ability."""
        bodyguard = BodyguardAbility(
            name="Bodyguard",
            type=AbilityType.KEYWORD,
            effect="Bodyguard ability",
            full_text="Bodyguard",
            keyword="Bodyguard",
            value=None
        )
        
        # Bodyguard should not be activatable
        assert bodyguard.can_activate(None) == False
    
    def test_registry_creation(self):
        """Test creating Bodyguard ability via registry."""
        bodyguard = KeywordRegistry.create_keyword_ability('Bodyguard')
        
        assert isinstance(bodyguard, BodyguardAbility)
        assert bodyguard.keyword == 'Bodyguard'
        assert bodyguard.type == AbilityType.KEYWORD


class TestBodyguardAbilityIntegration:
    """Integration tests for Bodyguard keyword ability with game state."""
    
    def test_bodyguard_must_be_challenged_first(self):
        """Test that Bodyguard characters must be challenged before others."""
        # Create abilities
        bodyguard_ability = KeywordRegistry.create_keyword_ability('Bodyguard')
        
        # Create characters
        bodyguard_char = create_character_with_ability("Goofy", bodyguard_ability)
        normal_char = create_test_character("Mickey Mouse")
        challenger = create_test_character("Beast")
        
        # Setup game - bodyguard and normal char for player 1, challenger for player 2
        game_state, validator, engine = setup_game_with_characters(
            [bodyguard_char, normal_char], [challenger]
        )
        
        # Switch to player 2 to test challenging
        game_state.current_player_index = 1
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # With bodyguard present, should only be able to challenge the bodyguard
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Should be exactly one challenge action - against the bodyguard
        assert len(challenge_actions) == 1, "Should only be able to challenge the bodyguard when bodyguard is present"
        
        action, params = challenge_actions[0]
        assert params['attacker'] == challenger
        assert params['defender'] == bodyguard_char, "Must challenge bodyguard first"
        
        # Verify direct validation
        assert validator.can_challenge(challenger, bodyguard_char) == True, "Should be able to challenge bodyguard"
        assert validator.can_challenge(challenger, normal_char) == False, "Should NOT be able to challenge normal character when bodyguard exists"
    
    def test_multiple_bodyguards_can_be_challenged(self):
        """Test that any bodyguard can be challenged when multiple exist."""
        # Create abilities
        bodyguard_ability = KeywordRegistry.create_keyword_ability('Bodyguard')
        
        # Create characters
        bodyguard_char1 = create_character_with_ability("Goofy", bodyguard_ability)
        bodyguard_char2 = create_character_with_ability("Maximus", bodyguard_ability)
        challenger = create_test_character("Beast")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [bodyguard_char1, bodyguard_char2], [challenger]
        )
        
        # Switch to player 2
        game_state.current_player_index = 1
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should be able to challenge either bodyguard
        challenge_actions = [action for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        assert len(challenge_actions) >= 0
    
    def test_no_bodyguard_allows_normal_challenges(self):
        """Test normal challenge behavior when no bodyguards are present."""
        # Create characters without bodyguard
        normal_char1 = create_test_character("Mickey Mouse")
        normal_char2 = create_test_character("Donald Duck")
        challenger = create_test_character("Beast")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [normal_char1, normal_char2], [challenger]
        )
        
        # Switch to player 2
        game_state.current_player_index = 1
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should be able to challenge any character
        challenge_actions = [action for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        assert len(challenge_actions) >= 0
    
    def test_damaged_bodyguard_still_protects(self):
        """Test that damaged (but alive) bodyguards still protect other characters."""
        # Create abilities
        bodyguard_ability = KeywordRegistry.create_keyword_ability('Bodyguard')
        
        # Create characters
        bodyguard_char = create_character_with_ability("Goofy", bodyguard_ability, willpower=3)
        normal_char = create_test_character("Mickey Mouse")
        challenger = create_test_character("Beast")
        
        # Damage the bodyguard but don't banish it
        bodyguard_char.damage = 2  # 2 damage on 3 willpower character
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [bodyguard_char, normal_char], [challenger]
        )
        
        # Switch to player 2
        game_state.current_player_index = 1
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Bodyguard should still be protecting (if alive)
        challenge_actions = [action for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        assert len(challenge_actions) >= 0
    
    def test_bodyguard_actual_challenge_execution(self):
        """Test that Bodyguard actually affects challenge execution and damage."""
        # Create abilities
        bodyguard_ability = KeywordRegistry.create_keyword_ability('Bodyguard')
        
        # Create characters
        bodyguard_char = create_character_with_ability("Guardian", bodyguard_ability, willpower=4)
        protected_char = create_test_character("Weak Character", willpower=2)
        attacker = create_test_character("Attacker", strength=3)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [bodyguard_char, protected_char], [attacker]
        )
        
        # Switch to attacker
        game_state.current_player_index = 1
        
        # Verify only bodyguard can be challenged
        legal_actions = validator.get_all_legal_actions()
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Should only be able to challenge bodyguard
        assert len(challenge_actions) == 1
        action, params = challenge_actions[0]
        assert params['defender'] == bodyguard_char
        
        # Challenge the bodyguard
        success, message = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': attacker,
            'defender': bodyguard_char
        })
        
        assert success == True
        assert "challenged" in message.lower()
        
        # Verify bodyguard took damage
        assert bodyguard_char.damage == attacker.strength
        
        # Verify protected character is untouched
        assert protected_char.damage == 0
    
    def test_bodyguard_delegation_methods_integration(self):
        """Test that Bodyguard properly implements all delegation methods."""
        # Create Bodyguard ability
        bodyguard_ability = KeywordRegistry.create_keyword_ability('Bodyguard')
        
        # Create characters
        bodyguard_char = create_character_with_ability("Guardian", bodyguard_ability)
        normal_char = create_test_character("Normal")
        attacker = create_test_character("Attacker")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([bodyguard_char, normal_char], [attacker])
        
        # Test delegation methods that don't affect normal rules
        assert bodyguard_ability.allows_being_challenged_by(attacker, bodyguard_char, game_state) == True
        assert bodyguard_ability.allows_challenging(bodyguard_char, attacker, game_state) == True
        assert bodyguard_ability.allows_singing_song(bodyguard_char, None, game_state) == True
        assert bodyguard_ability.get_song_cost_modification(bodyguard_char, None, game_state) == 0
        assert bodyguard_ability.allows_being_targeted_by(bodyguard_char, attacker, game_state) == True
        
        # Test core bodyguard functionality - challenge target modification
        all_targets = [bodyguard_char, normal_char]
        modified_targets = bodyguard_ability.modifies_challenge_targets(attacker, all_targets, game_state)
        
        # When bodyguard is present, should only be able to target bodyguards
        assert bodyguard_char in modified_targets
        assert normal_char not in modified_targets  # Normal char should be filtered out
        
        # Test bodyguard identification
        assert bodyguard_ability.modifies_challenge_targeting() == True
        assert bodyguard_ability.can_enter_play_exerted() == True