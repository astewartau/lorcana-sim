"""Tests for the first 10 named abilities implementation."""

import pytest
from unittest.mock import Mock, MagicMock

from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.models.abilities.composable.named_abilities import NamedAbilityRegistry
from src.lorcana_sim.engine.event_system import GameEvent, EventContext
from src.lorcana_sim.models.game.player import Player


def create_test_character(name: str, cost: int, color: CardColor, rarity: Rarity, 
                         strength: int, willpower: int, lore: int, subtypes=None) -> CharacterCard:
    """Helper function to create test characters with all required fields."""
    return CharacterCard(
        id=1,
        name=name,
        version=name.split(" - ")[1] if " - " in name else "",
        full_name=name,
        cost=cost,
        color=color,
        inkwell=True,
        rarity=rarity,
        set_code="TEST",
        number=1,
        story="Test Story",
        strength=strength,
        willpower=willpower,
        lore=lore,
        subtypes=subtypes or []
    )


class TestStaticNamedAbilities:
    """Test static named abilities (ongoing effects)."""
    
    def test_voiceless_ability(self):
        """Test VOICELESS - This character can't ⟳ to sing songs."""
        character = create_test_character(
            "Ariel - On Human Legs", 4, CardColor.RUBY, Rarity.COMMON, 2, 4, 2
        )
        
        ability_data = {"name": "VOICELESS", "type": "static"}
        voiceless_ability = NamedAbilityRegistry.create_ability("VOICELESS", character, ability_data)
        
        assert voiceless_ability is not None
        assert voiceless_ability.name == "VOICELESS"
    
    def test_sinister_plot_ability(self):
        """Test SINISTER PLOT - This character gets +1 ◇ for each other Villain character you have in play."""
        character = create_test_character(
            "Hades - King of Olympus", 8, CardColor.AMETHYST, Rarity.LEGENDARY, 6, 7, 3, ["Storyborn", "Villain", "Deity"]
        )
        
        ability_data = {"name": "SINISTER PLOT", "type": "static"}
        sinister_plot_ability = NamedAbilityRegistry.create_ability("SINISTER PLOT", character, ability_data)
        
        assert sinister_plot_ability is not None
        assert sinister_plot_ability.name == "SINISTER PLOT"
    
    def test_loyal_ability(self):
        """Test LOYAL - If you have a character named Gaston in play, you pay 1 ⬢ less to play this character."""
        character = create_test_character(
            "LeFou - Bumbler", 2, CardColor.AMBER, Rarity.COMMON, 1, 2, 1
        )
        
        ability_data = {"name": "LOYAL", "type": "static"}
        loyal_ability = NamedAbilityRegistry.create_ability("LOYAL", character, ability_data)
        
        assert loyal_ability is not None
        assert loyal_ability.name == "LOYAL"


class TestTriggeredNamedAbilities:
    """Test triggered named abilities (event-driven effects)."""
    
    def test_musical_debut_ability(self):
        """Test MUSICAL DEBUT - When you play this character, look at the top 4 cards of your deck."""
        character = create_test_character(
            "Ariel - Spectacular Singer", 4, CardColor.RUBY, Rarity.SUPER_RARE, 2, 4, 2
        )
        
        ability_data = {"name": "MUSICAL DEBUT", "type": "triggered"}
        musical_debut_ability = NamedAbilityRegistry.create_ability("MUSICAL DEBUT", character, ability_data)
        
        assert musical_debut_ability is not None
        assert musical_debut_ability.name == "MUSICAL DEBUT"
    
    def test_and_two_for_tea_ability(self):
        """Test AND TWO FOR TEA! - When you play this character, you may remove up to 2 damage from each of your Musketeer characters."""
        character = create_test_character(
            "Goofy - Musketeer", 5, CardColor.AMBER, Rarity.RARE, 3, 4, 2, ["Dreamborn", "Musketeer"]
        )
        
        ability_data = {"name": "AND TWO FOR TEA!", "type": "triggered"}
        and_two_for_tea_ability = NamedAbilityRegistry.create_ability("AND TWO FOR TEA!", character, ability_data)
        
        assert and_two_for_tea_ability is not None
        assert and_two_for_tea_ability.name == "AND TWO FOR TEA!"
    
    def test_well_of_souls_ability(self):
        """Test WELL OF SOULS - When you play this character, return a character card from your discard to your hand."""
        character = create_test_character(
            "Hades - Lord of the Underworld", 7, CardColor.AMETHYST, Rarity.LEGENDARY, 5, 6, 2, ["Storyborn", "Villain", "Deity"]
        )
        
        ability_data = {"name": "WELL OF SOULS", "type": "triggered"}
        well_of_souls_ability = NamedAbilityRegistry.create_ability("WELL OF SOULS", character, ability_data)
        
        assert well_of_souls_ability is not None
        assert well_of_souls_ability.name == "WELL OF SOULS"
    
    def test_horse_kick_ability(self):
        """Test HORSE KICK - When you play this character, chosen character gets -2 ⚔ this turn."""
        character = create_test_character(
            "Maximus - Relentless Pursuer", 4, CardColor.AMBER, Rarity.UNCOMMON, 3, 4, 1, ["Storyborn", "Ally"]
        )
        
        ability_data = {"name": "HORSE KICK", "type": "triggered"}
        horse_kick_ability = NamedAbilityRegistry.create_ability("HORSE KICK", character, ability_data)
        
        assert horse_kick_ability is not None
        assert horse_kick_ability.name == "HORSE KICK"
    
    def test_we_can_fix_it_ability(self):
        """Test WE CAN FIX IT - Whenever this character quests, you may ready your other Princess characters."""
        character = create_test_character(
            "Moana - Of Motunui", 5, CardColor.AMBER, Rarity.LEGENDARY, 3, 5, 2, ["Storyborn", "Hero", "Princess"]
        )
        
        ability_data = {"name": "WE CAN FIX IT", "type": "triggered"}
        we_can_fix_it_ability = NamedAbilityRegistry.create_ability("WE CAN FIX IT", character, ability_data)
        
        assert we_can_fix_it_ability is not None
        assert we_can_fix_it_ability.name == "WE CAN FIX IT"
    
    def test_heroism_ability(self):
        """Test HEROISM - When this character challenges and is banished, you may banish the challenged character."""
        character = create_test_character(
            "Prince Phillip - Dragonslayer", 4, CardColor.STEEL, Rarity.LEGENDARY, 3, 3, 2, ["Storyborn", "Hero", "Prince"]
        )
        
        ability_data = {"name": "HEROISM", "type": "triggered"}
        heroism_ability = NamedAbilityRegistry.create_ability("HEROISM", character, ability_data)
        
        assert heroism_ability is not None
        assert heroism_ability.name == "HEROISM"


class TestActivatedNamedAbilities:
    """Test activated named abilities (cost-based effects)."""
    
    def test_a_wonderful_dream_ability(self):
        """Test A WONDERFUL DREAM - ⟲ — Remove up to 3 damage from chosen Princess character."""
        character = create_test_character(
            "Cinderella - Gentle and Kind", 4, CardColor.STEEL, Rarity.SUPER_RARE, 2, 5, 2, ["Storyborn", "Hero", "Princess"]
        )
        
        ability_data = {"name": "A WONDERFUL DREAM", "type": "activated"}
        a_wonderful_dream_ability = NamedAbilityRegistry.create_ability("A WONDERFUL DREAM", character, ability_data)
        
        assert a_wonderful_dream_ability is not None
        assert a_wonderful_dream_ability.name == "A WONDERFUL DREAM"


class TestNamedAbilityRegistry:
    """Test the named ability registry system."""
    
    def test_registry_functionality(self):
        """Test that the registry correctly identifies implemented abilities."""
        implemented_abilities = [
            "VOICELESS", "MUSICAL DEBUT", "A WONDERFUL DREAM", "AND TWO FOR TEA!",
            "SINISTER PLOT", "WELL OF SOULS", "LOYAL", "HORSE KICK", 
            "WE CAN FIX IT", "HEROISM"
        ]
        
        for ability_name in implemented_abilities:
            assert NamedAbilityRegistry.is_ability_implemented(ability_name), f"{ability_name} should be implemented"
        
        assert not NamedAbilityRegistry.is_ability_implemented("UNKNOWN_ABILITY")
    
    def test_registry_returns_none_for_unimplemented(self):
        """Test that registry returns None for unimplemented abilities."""
        character = create_test_character(
            "Test Character", 1, CardColor.AMBER, Rarity.COMMON, 1, 1, 1
        )
        
        ability_data = {"name": "UNKNOWN_ABILITY", "type": "static"}
        result = NamedAbilityRegistry.create_ability("UNKNOWN_ABILITY", character, ability_data)
        assert result is None
    
    def test_get_registered_abilities(self):
        """Test that we can get all registered abilities."""
        registered = NamedAbilityRegistry.get_registered_abilities()
        
        expected_abilities = [
            "VOICELESS", "MUSICAL DEBUT", "A WONDERFUL DREAM", "AND TWO FOR TEA!",
            "SINISTER PLOT", "WELL OF SOULS", "LOYAL", "HORSE KICK",
            "WE CAN FIX IT", "HEROISM"
        ]
        
        for ability_name in expected_abilities:
            assert ability_name in registered


if __name__ == "__main__":
    pytest.main([__file__])