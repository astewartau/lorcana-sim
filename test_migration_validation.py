#!/usr/bin/env python3
"""
Simple test to validate that the test infrastructure migration worked correctly.
This validates that the new helper classes and functions work as expected.
"""

import sys
import os
sys.path.insert(0, 'src')

def test_helper_imports():
    """Test that helper imports work correctly."""
    try:
        from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability, create_test_action_card, add_singer_ability
        print("✓ Helper imports work correctly")
        return True
    except Exception as e:
        print(f"✗ Helper imports failed: {e}")
        return False

def test_base_class_instantiation():
    """Test that BaseNamedAbilityTest can be instantiated."""
    try:
        from tests.helpers import BaseNamedAbilityTest
        test_instance = BaseNamedAbilityTest()
        test_instance.setup_method()
        print("✓ BaseNamedAbilityTest can be instantiated and setup")
        return True
    except Exception as e:
        print(f"✗ BaseNamedAbilityTest instantiation failed: {e}")
        return False

def test_create_test_character():
    """Test that create_test_character works correctly."""
    try:
        from tests.helpers import create_test_character
        from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
        
        char = create_test_character(
            name="Test Character - Version",
            cost=3,
            color=CardColor.AMBER,
            strength=2,
            willpower=3,
            lore=1,
            rarity=Rarity.COMMON
        )
        
        assert char.name == "Test Character"
        assert char.version == "Version"
        assert char.cost == 3
        assert char.strength == 2
        assert char.willpower == 3
        assert char.lore == 1
        print("✓ create_test_character works correctly")
        return True
    except Exception as e:
        print(f"✗ create_test_character failed: {e}")
        return False

def test_add_named_ability():
    """Test that add_named_ability works correctly."""
    try:
        from tests.helpers import BaseNamedAbilityTest, create_test_character, add_named_ability
        
        # Set up test environment
        test_instance = BaseNamedAbilityTest()
        test_instance.setup_method()
        
        # Create a test character
        char = create_test_character(name="Test Character - Version")
        
        # Add an ability
        ability = add_named_ability(char, "LOYAL", "static", test_instance.event_manager)
        
        assert char.composable_abilities is not None
        assert len(char.composable_abilities) == 1
        assert char.composable_abilities[0].name == "LOYAL"
        print("✓ add_named_ability works correctly")
        return True
    except Exception as e:
        print(f"✗ add_named_ability failed: {e}")
        return False

def test_migrated_test_class():
    """Test that a migrated test class can be instantiated."""
    try:
        # Remove pytest import temporarily for testing
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "test_loyal_integration", 
            "tests/named_abilities/static/test_loyal_integration.py"
        )
        # Read the file and remove pytest import
        with open("tests/named_abilities/static/test_loyal_integration.py", "r") as f:
            content = f.read()
        
        # Remove pytest import line
        lines = content.split('\n')
        filtered_lines = [line for line in lines if not line.strip().startswith('import pytest')]
        modified_content = '\n'.join(filtered_lines)
        
        # Execute the modified content
        exec(modified_content, globals())
        
        # Test the class
        test_instance = TestLoyalIntegration()
        test_instance.setup_method()
        
        # Test helper method
        loyal_char = test_instance.create_loyal_character()
        assert loyal_char.composable_abilities is not None
        assert len(loyal_char.composable_abilities) == 1
        assert loyal_char.composable_abilities[0].name == "LOYAL"
        
        print("✓ Migrated test class works correctly")
        return True
    except Exception as e:
        print(f"✗ Migrated test class failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Validating test infrastructure migration...")
    print("=" * 50)
    
    tests = [
        test_helper_imports,
        test_base_class_instantiation,
        test_create_test_character,
        test_add_named_ability,
        test_migrated_test_class
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All validation tests passed! Migration was successful.")
        return True
    else:
        print("✗ Some validation tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)