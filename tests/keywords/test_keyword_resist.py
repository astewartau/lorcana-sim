"""Tests for Resist keyword ability - both unit and integration tests."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry, ResistAbility
from lorcana_sim.models.abilities.base_ability import AbilityType
from lorcana_sim.models.game.game_state import GameAction
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestResistAbilityUnit:
    """Unit tests for Resist keyword ability implementation."""
    
    def test_resist_creation(self):
        """Test creating Resist ability."""
        resist = ResistAbility(
            name="Resist",
            type=AbilityType.KEYWORD,
            effect="Resist ability",
            full_text="Resist +2",
            keyword="Resist",
            value=2
        )
        
        assert resist.keyword == "Resist"
        assert resist.value == 2
        assert resist.get_damage_reduction() == 2
        assert resist.modifies_damage_calculation() == True
        assert resist.is_passive_damage_modifier() == True
        assert resist.applies_to_all_damage_sources() == True
        assert str(resist) == "Resist +2"
    
    def test_damage_reduction(self):
        """Test damage reduction calculations."""
        resist_2 = ResistAbility(
            name="Resist",
            type=AbilityType.KEYWORD,
            effect="Resist ability",
            full_text="Resist +2",
            keyword="Resist",
            value=2
        )
        
        # Test various damage amounts
        assert resist_2.reduce_incoming_damage(5) == 3  # 5 - 2 = 3
        assert resist_2.reduce_incoming_damage(2) == 0  # 2 - 2 = 0 (minimum 0)
        assert resist_2.reduce_incoming_damage(1) == 0  # 1 - 2 = 0 (minimum 0)
        assert resist_2.reduce_incoming_damage(0) == 0  # 0 - 2 = 0 (minimum 0)
    
    def test_resist_different_values(self):
        """Test Resist with different reduction values."""
        resist_1 = ResistAbility(
            name="Resist",
            type=AbilityType.KEYWORD,
            effect="Resist ability",
            full_text="Resist +1",
            keyword="Resist",
            value=1
        )
        
        resist_3 = ResistAbility(
            name="Resist",
            type=AbilityType.KEYWORD,
            effect="Resist ability",
            full_text="Resist +3",
            keyword="Resist",
            value=3
        )
        
        # Test damage reduction with different values
        damage = 4
        assert resist_1.reduce_incoming_damage(damage) == 3  # 4 - 1 = 3
        assert resist_3.reduce_incoming_damage(damage) == 1  # 4 - 3 = 1
    
    def test_passive_ability(self):
        """Test that Resist is a passive ability."""
        resist = ResistAbility(
            name="Resist",
            type=AbilityType.KEYWORD,
            effect="Resist ability",
            full_text="Resist +1",
            keyword="Resist",
            value=1
        )
        
        assert resist.can_activate(None) == False
    
    def test_registry_creation(self):
        """Test creating Resist ability via registry."""
        resist = KeywordRegistry.create_keyword_ability('Resist', value=2)
        
        assert isinstance(resist, ResistAbility)
        assert resist.keyword == 'Resist'
        assert resist.value == 2
        assert resist.type == AbilityType.KEYWORD


class TestResistAbilityIntegration:
    """Integration tests for Resist keyword ability with game state."""
    
    def test_resist_reduces_challenge_damage(self):
        """Test that Resist reduces damage from challenges."""
        # Create resist ability
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        
        # Create characters
        resist_char = create_character_with_ability("Tough Character", resist_ability, willpower=4)
        attacker = create_test_character("Attacker", strength=5)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([resist_char], [attacker])
        
        # In full implementation, damage calculation would use resist
        damage_before_resist = attacker.strength  # 5
        damage_after_resist = resist_ability.reduce_incoming_damage(damage_before_resist)  # 3
        
        assert damage_after_resist == 3
        assert damage_after_resist < damage_before_resist
    
    def test_resist_applies_to_all_damage_sources(self):
        """Test that Resist applies to damage from all sources."""
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=1)
        
        # Create character with resist
        resist_char = create_character_with_ability("Protected Character", resist_ability)
        
        # Verify resist applies to all damage sources
        assert resist_ability.applies_to_all_damage_sources() == True
        
        # Test different damage amounts
        challenge_damage = 3
        ability_damage = 2
        
        assert resist_ability.reduce_incoming_damage(challenge_damage) == 2
        assert resist_ability.reduce_incoming_damage(ability_damage) == 1
    
    def test_resist_minimum_zero_damage(self):
        """Test that Resist cannot reduce damage below zero."""
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=3)
        
        # Create character
        resist_char = create_character_with_ability("Super Tough", resist_ability)
        
        # Test low damage amounts
        low_damage = 1
        reduced_damage = resist_ability.reduce_incoming_damage(low_damage)
        
        assert reduced_damage == 0  # Cannot go below 0
        assert reduced_damage >= 0
    
    def test_resist_vs_high_damage(self):
        """Test Resist against high damage amounts."""
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        
        # Test against various high damage amounts
        test_cases = [
            (10, 8),  # 10 - 2 = 8
            (7, 5),   # 7 - 2 = 5
            (3, 1),   # 3 - 2 = 1
            (2, 0),   # 2 - 2 = 0
        ]
        
        for incoming_damage, expected_result in test_cases:
            actual_result = resist_ability.reduce_incoming_damage(incoming_damage)
            assert actual_result == expected_result, f"Damage {incoming_damage} should reduce to {expected_result}, got {actual_result}"
    
    def test_resist_damage_modifier_properties(self):
        """Test Resist as a passive damage modifier."""
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=1)
        
        # Create character
        resist_char = create_character_with_ability("Damage Reducer", resist_ability)
        
        # Verify damage modifier properties
        assert resist_ability.is_passive_damage_modifier() == True
        assert resist_ability.modifies_damage_calculation() == True
        
        # Should not be activatable
        assert resist_ability.can_activate(None) == False
    
    def test_resist_actual_damage_reduction_execution(self):
        """Test that Resist actually reduces damage taken in challenges."""
        # Create Resist ability
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        
        # Create characters
        resist_char = create_character_with_ability("Tough Guy", resist_ability, willpower=5)
        attacker = create_test_character("Attacker", strength=4)  # Deals 4 damage
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [resist_char], [attacker]
        )
        
        # Switch to attacker
        game_state.current_player_index = 1
        
        # Execute challenge
        success, message = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': attacker,
            'defender': resist_char
        })
        
        # Verify challenge succeeded
        assert success == True
        
        # Verify damage was reduced: 4 base damage - 2 resist = 2 actual damage
        expected_damage = 4 - 2  # resist value
        assert resist_char.damage == expected_damage
        
        # Character should still be alive (5 willpower - 2 damage = 3 remaining)
        assert resist_char.is_alive == True
    
    def test_resist_prevents_lethal_damage(self):
        """Test that Resist can prevent lethal damage."""
        # Create Resist ability that prevents lethal damage
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=3)
        
        # Create characters where Resist saves from death
        resist_char = create_character_with_ability("Survivor", resist_ability, willpower=2)
        attacker = create_test_character("Weak Attacker", strength=3)  # Would deal exactly lethal
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [resist_char], [attacker]
        )
        
        # Switch to attacker
        game_state.current_player_index = 1
        
        # Execute challenge
        success, message = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': attacker,
            'defender': resist_char
        })
        
        # Verify challenge succeeded
        assert success == True
        
        # Verify damage was completely prevented: 3 base damage - 3 resist = 0 damage
        assert resist_char.damage == 0
        
        # Character should still be alive
        assert resist_char.is_alive == True
    
    def test_resist_with_overkill_damage(self):
        """Test Resist behavior with very high damage."""
        # Create Resist ability
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        
        # Create characters with overkill scenario
        resist_char = create_character_with_ability("Tank", resist_ability, willpower=3)
        strong_attacker = create_test_character("Dragon", strength=10)  # Massive overkill
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [resist_char], [strong_attacker]
        )
        
        # Switch to attacker
        game_state.current_player_index = 1
        
        # Execute challenge
        success, message = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': strong_attacker,
            'defender': resist_char
        })
        
        # Verify challenge succeeded
        assert success == True
        
        # Verify damage was reduced: 10 base damage - 2 resist = 8 damage
        expected_damage = 10 - 2
        assert resist_char.damage == expected_damage
        
        # Character should be dead (3 willpower < 8 damage)
        assert resist_char.is_alive == False
        assert "destroyed" in message
    
    def test_resist_damage_calculation_logic(self):
        """Test that Resist has the correct damage calculation logic."""
        # Create Resist ability
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        
        # Test damage reduction calculations
        assert resist_ability.get_damage_reduction() == 2
        assert resist_ability.reduce_incoming_damage(5) == 3  # 5 - 2 = 3
        assert resist_ability.reduce_incoming_damage(2) == 0  # 2 - 2 = 0 
        assert resist_ability.reduce_incoming_damage(1) == 0  # 1 - 2 = 0 (minimum)
        
        # Test that it identifies as damage modifier
        assert resist_ability.modifies_damage_calculation() == True
        assert resist_ability.is_passive_damage_modifier() == True
        assert resist_ability.applies_to_all_damage_sources() == True
    
    def test_resist_delegation_methods_integration(self):
        """Test that Resist properly implements all delegation methods."""
        # Create Resist ability
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=3)
        
        # Create character
        resist_char = create_character_with_ability("Resistant", resist_ability)
        attacker = create_test_character("Attacker")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([resist_char], [attacker])
        
        # Test all delegation methods work (don't affect other rules)
        assert resist_ability.allows_being_challenged_by(attacker, resist_char, game_state) == True
        assert resist_ability.allows_challenging(resist_char, attacker, game_state) == True
        assert resist_ability.modifies_challenge_targets(attacker, [resist_char], game_state) == [resist_char]
        assert resist_ability.allows_singing_song(resist_char, None, game_state) == True
        assert resist_ability.get_song_cost_modification(resist_char, None, game_state) == 0
        assert resist_ability.allows_being_targeted_by(resist_char, attacker, game_state) == True
        
        # Test core resist functionality
        assert resist_ability.get_damage_reduction() == 3
        assert resist_ability.reduce_incoming_damage(5) == 2  # 5 - 3 = 2
        assert resist_ability.reduce_incoming_damage(2) == 0  # 2 - 3 = 0 (minimum)
        assert resist_ability.modifies_damage_calculation() == True