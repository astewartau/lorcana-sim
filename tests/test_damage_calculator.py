"""Tests for the damage calculation system."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry
from lorcana_sim.engine.damage_calculator import DamageCalculator, DamageType
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters
)


class TestDamageCalculator:
    """Test the damage calculation system."""
    
    def test_basic_damage_calculation(self):
        """Test basic damage calculation without abilities."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create characters
        attacker = create_test_character("Attacker", strength=3)
        target = create_test_character("Target", willpower=5)
        
        # Calculate damage
        final_damage = calculator.calculate_damage(
            attacker, target, 4, DamageType.CHALLENGE
        )
        
        # No abilities, so damage should be unchanged
        assert final_damage == 4
    
    def test_resist_damage_reduction(self):
        """Test damage reduction with Resist ability."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create characters
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        attacker = create_test_character("Attacker", strength=5)
        target = create_character_with_ability("Tank", resist_ability, willpower=8)
        
        # Calculate damage
        final_damage = calculator.calculate_damage(
            attacker, target, 5, DamageType.CHALLENGE
        )
        
        # Should be reduced: 5 - 2 = 3
        assert final_damage == 3
    
    def test_resist_prevents_all_damage(self):
        """Test Resist preventing all damage."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create characters
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=5)
        attacker = create_test_character("Weak Attacker", strength=3)
        target = create_character_with_ability("Heavy Tank", resist_ability, willpower=10)
        
        # Calculate damage
        final_damage = calculator.calculate_damage(
            attacker, target, 3, DamageType.CHALLENGE
        )
        
        # Should be completely prevented: 3 - 5 = 0 (minimum)
        assert final_damage == 0
    
    def test_damage_preview(self):
        """Test damage preview functionality."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create characters
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        attacker = create_test_character("Attacker", strength=5)
        target = create_character_with_ability("Tank", resist_ability, willpower=8)
        
        # Preview damage
        preview = calculator.preview_damage(
            attacker, target, 5, DamageType.CHALLENGE
        )
        
        # Check preview structure
        assert preview['base_damage'] == 5
        assert preview['final_damage'] == 3  # 5 - 2 resist
        assert len(preview['modifiers']) == 1
        assert preview['modifiers'][0]['type'] == 'damage_reduction'
        assert preview['modifiers'][0]['change'] == 2
        assert preview['prevented'] == False
    
    def test_damage_preview_prevention(self):
        """Test damage preview when damage is completely prevented."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create characters
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=4)
        attacker = create_test_character("Weak Attacker", strength=2)
        target = create_character_with_ability("Super Tank", resist_ability)
        
        # Preview damage
        preview = calculator.preview_damage(
            attacker, target, 2, DamageType.CHALLENGE
        )
        
        # Check prevention
        assert preview['base_damage'] == 2
        assert preview['final_damage'] == 0
        assert preview['prevented'] == True
        assert len(preview['modifiers']) == 1
        assert preview['modifiers'][0]['change'] == 2  # All damage prevented
    
    def test_multiple_resist_abilities(self):
        """Test multiple Resist abilities on the same character."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create character with multiple resist abilities
        resist_ability1 = KeywordRegistry.create_keyword_ability('Resist', value=2)
        resist_ability2 = KeywordRegistry.create_keyword_ability('Resist', value=1)
        
        attacker = create_test_character("Attacker", strength=8)
        target = create_character_with_ability("Ultra Tank", resist_ability1)
        target.abilities.append(resist_ability2)  # Add second resist
        
        # Calculate damage
        final_damage = calculator.calculate_damage(
            attacker, target, 8, DamageType.CHALLENGE
        )
        
        # Should apply both reductions: 8 - 2 - 1 = 5
        assert final_damage == 5
    
    def test_zero_damage_input(self):
        """Test calculator behavior with zero damage."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create characters
        attacker = create_test_character("Attacker")
        target = create_test_character("Target")
        
        # Calculate zero damage
        final_damage = calculator.calculate_damage(
            attacker, target, 0, DamageType.CHALLENGE
        )
        
        assert final_damage == 0
    
    def test_negative_damage_input(self):
        """Test calculator behavior with negative damage."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create characters
        attacker = create_test_character("Attacker")
        target = create_test_character("Target")
        
        # Calculate negative damage
        final_damage = calculator.calculate_damage(
            attacker, target, -5, DamageType.CHALLENGE
        )
        
        # Should be clamped to 0
        assert final_damage == 0
    
    def test_damage_types(self):
        """Test that different damage types work correctly."""
        # Setup game and calculator
        game_state, validator, engine = setup_game_with_characters([], [])
        calculator = DamageCalculator(game_state)
        
        # Create characters
        resist_ability = KeywordRegistry.create_keyword_ability('Resist', value=2)
        target = create_character_with_ability("Tank", resist_ability)
        
        # Test different damage types
        challenge_damage = calculator.calculate_damage(None, target, 5, DamageType.CHALLENGE)
        ability_damage = calculator.calculate_damage(None, target, 5, DamageType.ABILITY)
        direct_damage = calculator.calculate_damage(None, target, 5, DamageType.DIRECT)
        
        # All should be reduced by Resist (since it applies to all damage types by default)
        assert challenge_damage == 3
        assert ability_damage == 3
        assert direct_damage == 3