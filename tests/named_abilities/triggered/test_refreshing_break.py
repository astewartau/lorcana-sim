"""Tests for REFRESHING BREAK ability."""

import pytest
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.refreshing_break import create_refreshing_break


class TestRefreshingBreak:
    """Test REFRESHING BREAK ability implementation."""
    
    def test_refreshing_break_ability_creation(self):
        """Test that REFRESHING BREAK ability can be created."""
        
        # Create a mock character
        class MockCharacter:
            def __init__(self):
                self.name = 'Test Character'
                self.damage = 2
        
        character = MockCharacter()
        
        # Create the ability
        ability = create_refreshing_break(character, {})
        
        # Verify basic properties
        assert ability.name == "REFRESHING BREAK"
        assert len(ability.listeners) > 0
        assert hasattr(ability.listeners[0].effect, 'apply')
    
    def test_gain_lore_per_damage_effect(self):
        """Test that the effect gains lore per damage correctly."""
        from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.refreshing_break import GainLorePerDamageEffect
        
        # Create mock objects
        class MockCharacter:
            def __init__(self, damage=3):
                self.damage = damage
        
        class MockPlayer:
            def __init__(self):
                self.lore = 5
            
            def gain_lore(self, amount):
                self.lore += amount
        
        # Test setup
        character = MockCharacter(damage=3)
        player = MockPlayer()
        effect = GainLorePerDamageEffect()
        
        # Create context with event data
        context = {
            'event_context': {
                'source': character  # The readied character
            }
        }
        
        # Apply the effect
        initial_lore = player.lore
        result = effect.apply(player, context)
        
        # Verify lore was gained equal to damage
        assert player.lore == initial_lore + character.damage
        assert result == player
    
    def test_gain_lore_per_damage_no_damage(self):
        """Test that no lore is gained when character has no damage."""
        from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.refreshing_break import GainLorePerDamageEffect
        
        # Create mock objects
        class MockCharacter:
            def __init__(self, damage=0):
                self.damage = damage
        
        class MockPlayer:
            def __init__(self):
                self.lore = 5
            
            def gain_lore(self, amount):
                self.lore += amount
        
        # Test setup
        character = MockCharacter(damage=0)
        player = MockPlayer()
        effect = GainLorePerDamageEffect()
        
        # Create context with event data
        context = {
            'event_context': {
                'source': character  # The readied character
            }
        }
        
        # Apply the effect
        initial_lore = player.lore
        result = effect.apply(player, context)
        
        # Verify no lore was gained
        assert player.lore == initial_lore
        assert result == player
    
    def test_gain_lore_per_damage_fallback_to_ability_owner(self):
        """Test that effect falls back to ability_owner when event_context source is missing."""
        from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.refreshing_break import GainLorePerDamageEffect
        
        # Create mock objects
        class MockCharacter:
            def __init__(self, damage=2):
                self.damage = damage
        
        class MockPlayer:
            def __init__(self):
                self.lore = 5
            
            def gain_lore(self, amount):
                self.lore += amount
        
        # Test setup
        character = MockCharacter(damage=2)
        player = MockPlayer()
        effect = GainLorePerDamageEffect()
        
        # Create context without event_context source, but with ability_owner
        context = {
            'ability_owner': character
        }
        
        # Apply the effect
        initial_lore = player.lore
        result = effect.apply(player, context)
        
        # Verify lore was gained equal to damage
        assert player.lore == initial_lore + character.damage
        assert result == player
    
    def test_gain_lore_per_damage_effect_string_representation(self):
        """Test string representation of the effect."""
        from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.refreshing_break import GainLorePerDamageEffect
        
        effect = GainLorePerDamageEffect()
        assert str(effect) == "gain 1 lore per damage"