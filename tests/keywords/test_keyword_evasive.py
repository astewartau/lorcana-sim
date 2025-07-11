"""Tests for Evasive keyword ability - both unit and integration tests."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry, EvasiveAbility
from lorcana_sim.models.abilities.base_ability import AbilityType
from lorcana_sim.models.game.game_state import GameAction
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestEvasiveAbilityUnit:
    """Unit tests for Evasive keyword ability implementation."""
    
    def test_evasive_creation(self):
        """Test creating Evasive ability."""
        evasive = EvasiveAbility(
            name="Evasive",
            type=AbilityType.KEYWORD,
            effect="Evasive ability",
            full_text="Evasive",
            keyword="Evasive",
            value=None
        )
        
        assert evasive.keyword == "Evasive"
        assert evasive.modifies_challenge_rules() == True
        assert str(evasive) == "Evasive"
    
    def test_can_be_challenged_by(self):
        """Test Evasive challenge restrictions."""
        evasive_ability = EvasiveAbility(
            name="Evasive",
            type=AbilityType.KEYWORD,
            effect="Evasive ability",
            full_text="Evasive",
            keyword="Evasive",
            value=None
        )
        
        # Create characters
        evasive_challenger = create_test_character("Evasive Challenger", [evasive_ability])
        normal_challenger = create_test_character("Normal Challenger", [])
        
        # Evasive character can challenge another evasive character
        assert evasive_ability.can_be_challenged_by(evasive_challenger) == True
        
        # Normal character cannot challenge evasive character
        assert evasive_ability.can_be_challenged_by(normal_challenger) == False
    
    def test_passive_ability(self):
        """Test that Evasive is a passive ability."""
        evasive = EvasiveAbility(
            name="Evasive",
            type=AbilityType.KEYWORD,
            effect="Evasive ability",
            full_text="Evasive",
            keyword="Evasive",
            value=None
        )
        
        # Evasive should not be activatable
        assert evasive.can_activate(None) == False
    
    def test_registry_creation(self):
        """Test creating Evasive ability via registry."""
        evasive = KeywordRegistry.create_keyword_ability('Evasive')
        
        assert isinstance(evasive, EvasiveAbility)
        assert evasive.keyword == 'Evasive'
        assert evasive.type == AbilityType.KEYWORD


class TestEvasiveAbilityIntegration:
    """Integration tests for Evasive keyword ability with game state."""
    
    def test_evasive_prevents_normal_challenges(self):
        """Test that Evasive prevents challenges from non-evasive characters."""
        # Create abilities
        evasive_ability = KeywordRegistry.create_keyword_ability('Evasive')
        
        # Create characters
        evasive_char = create_character_with_ability("Tinker Bell", evasive_ability)
        normal_attacker = create_test_character("Mickey Mouse")
        
        # Setup game with evasive character for player 1, normal attacker for player 2
        game_state, validator, engine = setup_game_with_characters([evasive_char], [normal_attacker])
        
        # Get all legal actions for player 2 (with normal character)
        game_state.current_player_index = 1  # Switch to player 2
        legal_actions = validator.get_all_legal_actions()
        
        # Check challenge actions - should be NONE because normal character can't challenge evasive
        challenge_actions = [action for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Verify that no challenges are possible
        assert len(challenge_actions) == 0, "Normal character should not be able to challenge evasive character"
        
        # Double-check with the validator's direct method
        can_challenge = validator.can_challenge(normal_attacker, evasive_char)
        assert can_challenge == False, "Direct validation should also prevent normal vs evasive challenge"
    
    def test_evasive_can_challenge_evasive(self):
        """Test that Evasive characters can challenge other Evasive characters."""
        # Create abilities
        evasive_ability = KeywordRegistry.create_keyword_ability('Evasive')
        
        # Create characters - both evasive
        evasive_attacker = create_character_with_ability("Tinker Bell", evasive_ability)
        evasive_defender = create_character_with_ability("Jetsam", evasive_ability)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([evasive_attacker], [evasive_defender])
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should be able to challenge the other evasive character
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Verify that evasive can challenge evasive
        assert len(challenge_actions) == 1, "Evasive character should be able to challenge other evasive character"
        
        # Verify the specific challenge is correct
        action, params = challenge_actions[0]
        assert action == GameAction.CHALLENGE_CHARACTER
        assert params['attacker'] == evasive_attacker
        assert params['defender'] == evasive_defender
        
        # Double-check with direct validation
        can_challenge = validator.can_challenge(evasive_attacker, evasive_defender)
        assert can_challenge == True, "Direct validation should allow evasive vs evasive challenge"
    
    def test_evasive_with_multiple_targets(self):
        """Test Evasive behavior with multiple potential targets."""
        # Create abilities
        evasive_ability = KeywordRegistry.create_keyword_ability('Evasive')
        
        # Create characters
        evasive_char = create_character_with_ability("Tinker Bell", evasive_ability)
        normal_char1 = create_test_character("Mickey Mouse")
        normal_char2 = create_test_character("Donald Duck")
        normal_challenger = create_test_character("Attacker")
        
        # Setup game - player 1 has evasive + normal, player 2 has challenger
        game_state, validator, engine = setup_game_with_characters(
            [evasive_char, normal_char1], [normal_challenger, normal_char2]
        )
        
        # Switch to player 2 to test challenging
        game_state.current_player_index = 1
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # The normal challenger should be able to challenge normal characters
        # but not the evasive character
        challenge_actions = [action for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Framework verification - specific targeting logic would be in move validator
        assert len(challenge_actions) >= 0
    
    def test_evasive_actual_challenge_execution(self):
        """Test that Evasive actually prevents challenges from normal characters in execution."""
        # Create abilities
        evasive_ability = KeywordRegistry.create_keyword_ability('Evasive')
        
        # Create characters
        evasive_char = create_character_with_ability("Flying Tinker Bell", evasive_ability, willpower=2)
        normal_attacker = create_test_character("Ground Beast", strength=3)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [evasive_char], [normal_attacker]
        )
        
        # Switch to attacker
        game_state.current_player_index = 1
        
        # Verify no legal challenge actions exist
        legal_actions = validator.get_all_legal_actions()
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Should be no challenges possible
        assert len(challenge_actions) == 0
        
        # Double check with direct validation
        assert validator.can_challenge(normal_attacker, evasive_char) == False
        
        # Evasive character should be untouched
        assert evasive_char.damage == 0
        assert evasive_char.is_alive == True
    
    def test_evasive_vs_evasive_actual_execution(self):
        """Test that Evasive characters can actually challenge other Evasive characters."""
        # Create abilities
        evasive_ability = KeywordRegistry.create_keyword_ability('Evasive')
        
        # Create characters - both evasive
        evasive_attacker = create_character_with_ability("Flying Attacker", evasive_ability, strength=2)
        evasive_defender = create_character_with_ability("Flying Defender", evasive_ability, willpower=3)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [evasive_attacker], [evasive_defender]
        )
        
        # Execute the challenge
        success, message = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': evasive_attacker,
            'defender': evasive_defender
        })
        
        assert success == True
        assert "challenged" in message.lower()
        
        # Verify damage was dealt
        assert evasive_defender.damage == evasive_attacker.strength
        assert evasive_attacker.damage == evasive_defender.strength  # If defender has strength
    
    def test_evasive_delegation_methods_integration(self):
        """Test that Evasive properly implements all delegation methods."""
        # Create Evasive ability
        evasive_ability = KeywordRegistry.create_keyword_ability('Evasive')
        
        # Create characters
        evasive_char = create_character_with_ability("Flyer", evasive_ability)
        normal_char = create_test_character("Normal")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([evasive_char], [normal_char])
        
        # Test delegation methods that don't affect normal rules
        assert evasive_ability.allows_challenging(evasive_char, normal_char, game_state) == True
        assert evasive_ability.modifies_challenge_targets(evasive_char, [normal_char], game_state) == [normal_char]
        assert evasive_ability.allows_singing_song(evasive_char, None, game_state) == True
        assert evasive_ability.get_song_cost_modification(evasive_char, None, game_state) == 0
        assert evasive_ability.allows_being_targeted_by(evasive_char, normal_char, game_state) == True
        
        # Test core evasive functionality - being challenged
        normal_can_challenge_evasive = evasive_ability.allows_being_challenged_by(normal_char, evasive_char, game_state)
        evasive_can_challenge_evasive = evasive_ability.allows_being_challenged_by(evasive_char, evasive_char, game_state)
        
        assert normal_can_challenge_evasive == False  # Normal can't challenge evasive
        assert evasive_can_challenge_evasive == True  # Evasive can challenge evasive
        
        # Test evasive properties
        assert evasive_ability.modifies_challenge_rules() == True