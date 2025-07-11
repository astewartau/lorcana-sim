"""Tests for Shift keyword ability - both unit and integration tests."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry, ShiftAbility
from lorcana_sim.models.abilities.base_ability import AbilityType
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestShiftAbilityUnit:
    """Unit tests for Shift keyword ability implementation."""
    
    def test_shift_creation(self):
        """Test creating Shift ability."""
        shift = ShiftAbility(
            name="Shift",
            type=AbilityType.KEYWORD,
            effect="Shift ability",
            full_text="Shift 6",
            keyword="Shift",
            value=6
        )
        
        assert shift.keyword == "Shift"
        assert shift.value == 6
        assert shift.get_shift_cost() == 6
        assert shift.provides_alternative_play_cost() == True
        assert str(shift) == "Shift 6"
    
    def test_shift_alternative_cost(self):
        """Test Shift alternative cost mechanics."""
        shift = ShiftAbility(
            name="Shift",
            type=AbilityType.KEYWORD,
            effect="Shift ability",
            full_text="Shift 4",
            keyword="Shift",
            value=4
        )
        
        assert shift.get_alternative_cost() == 4
        assert shift.requires_target_for_play() == True
    
    def test_passive_ability(self):
        """Test that Shift is a passive ability."""
        shift = ShiftAbility(
            name="Shift",
            type=AbilityType.KEYWORD,
            effect="Shift ability",
            full_text="Shift 6",
            keyword="Shift",
            value=6
        )
        
        assert shift.can_activate(None) == False
    
    def test_registry_creation(self):
        """Test creating Shift ability via registry."""
        shift = KeywordRegistry.create_keyword_ability('Shift', value=5)
        
        assert isinstance(shift, ShiftAbility)
        assert shift.keyword == 'Shift'
        assert shift.value == 5
        assert shift.type == AbilityType.KEYWORD


class TestShiftAbilityIntegration:
    """Integration tests for Shift keyword ability with game state."""
    
    def test_shift_provides_alternative_play_option(self):
        """Test that Shift provides an alternative way to play characters."""
        # Create shift ability
        shift_ability = KeywordRegistry.create_keyword_ability('Shift', value=4)
        
        # Create characters - one to shift onto, one with shift
        base_char = create_test_character("Hades - Basic", cost=6)
        shift_char = create_character_with_ability("Hades - King of Olympus", shift_ability, cost=8)
        
        # Setup game with base character in play
        game_state, validator, engine = setup_game_with_characters([base_char], [])
        
        # Add shift character to hand
        game_state.current_player.hand.append(shift_char)
        
        # In a full implementation, we'd check for shift play options
        # For now, verify the ability has the right properties
        assert shift_ability.provides_alternative_play_cost() == True
        assert shift_ability.get_alternative_cost() == 4
    
    def test_shift_targeting_requirements(self):
        """Test that Shift requires a valid target to shift onto."""
        shift_ability = KeywordRegistry.create_keyword_ability('Shift', value=5)
        
        # Create characters
        wrong_name_char = create_test_character("Mickey Mouse")  # Different name
        shift_char = create_character_with_ability("Stitch - Rock Star", shift_ability)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([wrong_name_char], [])
        
        # Add shift character to hand
        game_state.current_player.hand.append(shift_char)
        
        # Verify shift requires targeting
        assert shift_ability.requires_target_for_play() == True
    
    def test_shift_cost_efficiency(self):
        """Test that Shift can provide cost savings."""
        shift_ability = KeywordRegistry.create_keyword_ability('Shift', value=3)
        
        # Create expensive character with cheap shift cost
        shift_char = create_character_with_ability("Expensive Character", shift_ability, cost=7)
        
        # Verify cost savings potential
        normal_cost = shift_char.cost  # 7
        shift_cost = shift_ability.get_shift_cost()  # 3
        
        assert shift_cost < normal_cost, "Shift should provide cost savings"
        assert shift_cost == 3
    
    def test_shift_without_valid_targets(self):
        """Test Shift behavior when no valid targets exist."""
        shift_ability = KeywordRegistry.create_keyword_ability('Shift', value=4)
        
        # Create shift character
        shift_char = create_character_with_ability("Hades - King", shift_ability)
        
        # Setup game with no characters in play (no shift targets)
        game_state, validator, engine = setup_game_with_characters([], [])
        
        # Add shift character to hand
        game_state.current_player.hand.append(shift_char)
        
        # Would need to play normally (no shift targets available)
        # In full implementation, move validator would check for valid shift targets
        assert shift_ability.requires_target_for_play() == True
    
    def test_shift_delegation_methods_integration(self):
        """Test that Shift properly implements all delegation methods."""
        # Create Shift ability
        shift_ability = KeywordRegistry.create_keyword_ability('Shift', value=4)
        
        # Create characters
        shift_char = create_character_with_ability("Shifter", shift_ability)
        normal_char = create_test_character("Normal")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([shift_char], [normal_char])
        
        # Test delegation methods (Shift shouldn't affect normal rules during play)
        assert shift_ability.allows_being_challenged_by(normal_char, shift_char, game_state) == True
        assert shift_ability.allows_challenging(shift_char, normal_char, game_state) == True
        assert shift_ability.modifies_challenge_targets(shift_char, [normal_char], game_state) == [normal_char]
        assert shift_ability.allows_singing_song(shift_char, None, game_state) == True
        assert shift_ability.get_song_cost_modification(shift_char, None, game_state) == 0
        assert shift_ability.allows_being_targeted_by(shift_char, normal_char, game_state) == True
        
        # Test core Shift functionality
        assert shift_ability.provides_alternative_play_cost() == True
        assert shift_ability.get_alternative_cost() == 4
        assert shift_ability.get_shift_cost() == 4
        assert shift_ability.requires_target_for_play() == True
    
    def test_shift_play_mechanics_framework(self):
        """Test Shift play mechanics within the framework."""
        shift_ability = KeywordRegistry.create_keyword_ability('Shift', value=3)
        
        # Create characters
        base_char = create_test_character("Base Version", cost=5)
        shift_char = create_character_with_ability("Advanced Version", shift_ability, cost=7)
        
        # Setup game with base character in play
        game_state, validator, engine = setup_game_with_characters([base_char], [])
        
        # Add shift character to hand
        game_state.current_player.hand.append(shift_char)
        
        # Verify shift mechanics
        assert shift_ability.get_shift_cost() == 3  # Cheaper than normal cost of 7
        assert shift_ability.provides_alternative_play_cost() == True
        
        # In full implementation, this would enable playing for 3 ink instead of 7
        # by targeting the base character
    
    def test_shift_character_replacement_concept(self):
        """Test the concept of character replacement with Shift."""
        shift_ability = KeywordRegistry.create_keyword_ability('Shift', value=2)
        
        # Create characters representing different versions
        old_version = create_test_character("Character - Basic", willpower=3)
        new_version = create_character_with_ability("Character - Upgraded", shift_ability, willpower=5)
        
        # Setup game with old version in play
        game_state, validator, engine = setup_game_with_characters([old_version], [])
        
        # Add new version to hand
        game_state.current_player.hand.append(new_version)
        
        # Verify shift properties
        assert shift_ability.get_shift_cost() == 2
        assert shift_ability.requires_target_for_play() == True
        assert shift_ability.provides_alternative_play_cost() == True
        
        # In full implementation:
        # - Could play new_version for 2 ink by targeting old_version
        # - Old version would be moved to discard pile
        # - New version would inherit any counters/effects from old version