"""Integration tests for both keyword and named abilities working together."""

import pytest
from src.lorcana_sim.models.cards.card_factory import CardFactory
from src.lorcana_sim.models.abilities.composable.named_abilities import NamedAbilityRegistry


class TestAbilityIntegration:
    """Test that keyword and named abilities work together."""
    
    def test_card_with_both_keyword_and_named_abilities(self):
        """Test a card that has both keyword abilities and named abilities."""
        card_data = {
            'id': 1,
            'name': 'Test Hero',
            'version': 'Mighty Warrior',
            'fullName': 'Test Hero - Mighty Warrior',
            'cost': 5,
            'color': 'Steel',
            'inkwell': True,
            'rarity': 'Legendary',
            'setCode': 'TEST',
            'number': 1,
            'story': 'Test Story',
            'type': 'Character',
            'strength': 4,
            'willpower': 6,
            'lore': 3,
            'subtypes': ['Hero', 'Princess'],
            'keywordAbilities': ['Rush', 'Challenger'],
            'abilities': [
                {
                    'type': 'keyword',
                    'keyword': 'Rush',
                    'fullText': 'Rush (This character can challenge the turn they\'re played.)'
                },
                {
                    'type': 'keyword', 
                    'keyword': 'Challenger',
                    'keywordValue': '+2',
                    'keywordValueNumber': 2,
                    'fullText': 'Challenger +2 (While challenging, this character gets +2 ⚔.)'
                },
                {
                    'name': 'A WONDERFUL DREAM',
                    'type': 'activated',
                    'effect': 'Remove up to 3 damage from chosen Princess character.',
                    'fullText': 'A WONDERFUL DREAM ⟲ — Remove up to 3 damage from chosen Princess character.'
                }
            ]
        }
        
        # Create the card
        card = CardFactory.from_json(card_data)
        
        # Verify the card was created
        assert card.name == 'Test Hero'
        assert card.strength == 4
        assert card.willpower == 6
        assert card.lore == 3
        assert 'Hero' in card.subtypes
        assert 'Princess' in card.subtypes
        
        # Verify abilities were created
        assert len(card.composable_abilities) >= 1  # At least the named ability
        
        # Check if named ability was created
        named_abilities = [ability for ability in card.composable_abilities if ability.name == 'A WONDERFUL DREAM']
        assert len(named_abilities) == 1, "Should have created A WONDERFUL DREAM ability"
        
        # Verify ability names
        ability_names = [ability.name for ability in card.composable_abilities]
        print(f"Card has abilities: {ability_names}")
        
        # Should have at least the named ability
        assert 'A WONDERFUL DREAM' in ability_names
    
    def test_unimplemented_named_ability_is_skipped(self):
        """Test that unimplemented named abilities are skipped gracefully."""
        card_data = {
            'id': 2,
            'name': 'Future Character',
            'version': 'Not Yet Implemented',
            'fullName': 'Future Character - Not Yet Implemented',
            'cost': 3,
            'color': 'Amber',
            'inkwell': True,
            'rarity': 'Common',
            'setCode': 'TEST',
            'number': 2,
            'story': 'Test Story',
            'type': 'Character',
            'strength': 2,
            'willpower': 3,
            'lore': 1,
            'abilities': [
                {
                    'name': 'FUTURE_ABILITY_NOT_IMPLEMENTED',
                    'type': 'static',
                    'effect': 'This ability is not implemented yet.',
                    'fullText': 'FUTURE_ABILITY_NOT_IMPLEMENTED This ability is not implemented yet.'
                },
                {
                    'name': 'VOICELESS',
                    'type': 'static',
                    'effect': 'This character can\'t ⟳ to sing songs.',
                    'fullText': 'VOICELESS This character can\'t ⟳ to sing songs.'
                }
            ]
        }
        
        # Create the card - should not crash
        card = CardFactory.from_json(card_data)
        
        # Verify the card was created
        assert card.name == 'Future Character'
        
        # Should have the implemented ability but not the unimplemented one
        ability_names = [ability.name for ability in card.composable_abilities]
        assert 'VOICELESS' in ability_names
        assert 'FUTURE_ABILITY_NOT_IMPLEMENTED' not in ability_names


if __name__ == "__main__":
    pytest.main([__file__])