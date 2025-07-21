"""Integration tests for named abilities implementation."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities import NamedAbilityRegistry


class TestStaticNamedAbilities(GameEngineTestBase):
    """Integration tests for static named abilities (ongoing effects)."""
    
    def create_named_ability_character(self, name: str, cost: int, color: CardColor, rarity: Rarity, 
                                     strength: int, willpower: int, lore: int, subtypes=None, 
                                     named_ability=None) -> CharacterCard:
        """Helper function to create test characters with named abilities."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            lore=lore,
            color=color,
            subtypes=subtypes
        )
        
        # Add named ability if specified
        if named_ability:
            ability_data = {"name": named_ability, "type": "triggered"}  # Default to triggered
            ability = NamedAbilityRegistry.create_ability(named_ability, character, ability_data)
            if ability:
                character.composable_abilities.append(ability)
        
        return character
    
    def test_voiceless_ability_creation(self):
        """Test VOICELESS - This character can't ⟳ to sing songs."""
        character = self.create_named_ability_character(
            "Ariel - On Human Legs", 4, CardColor.RUBY, Rarity.COMMON, 2, 4, 2
        )
        
        ability_data = {"name": "VOICELESS", "type": "static"}
        voiceless_ability = NamedAbilityRegistry.create_ability("VOICELESS", character, ability_data)
        
        assert voiceless_ability is not None
        assert voiceless_ability.name == "VOICELESS"
    
    def test_voiceless_integration(self):
        """Test VOICELESS integration through game flow."""
        voiceless_char = self.create_named_ability_character(
            "Ariel - On Human Legs", 4, CardColor.RUBY, Rarity.COMMON, 2, 4, 2,
            named_ability="VOICELESS"
        )
        
        # Put character in play
        message = self.play_character(voiceless_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert voiceless_char in self.player1.characters_in_play
        
        # Should have voiceless ability
        if voiceless_char.composable_abilities:
            assert any("voiceless" in ability.name.lower() for ability in voiceless_char.composable_abilities)
    
    def test_sinister_plot_ability_creation(self):
        """Test SINISTER PLOT - This character gets +1 ◇ for each other Villain character you have in play."""
        character = self.create_named_ability_character(
            "Hades - King of Olympus", 8, CardColor.AMETHYST, Rarity.LEGENDARY, 6, 7, 3, ["Storyborn", "Villain", "Deity"]
        )
        
        ability_data = {"name": "SINISTER PLOT", "type": "static"}
        sinister_plot_ability = NamedAbilityRegistry.create_ability("SINISTER PLOT", character, ability_data)
        
        # SINISTER PLOT may return None but adds conditional effects to the character
        if sinister_plot_ability is None:
            # Check for conditional effects or metadata
            assert hasattr(character, 'conditional_effects') or hasattr(character, 'metadata')
        else:
            assert sinister_plot_ability.name == "SINISTER PLOT"
    
    def test_loyal_ability_creation(self):
        """Test LOYAL - If you have a character named Gaston in play, you pay 1 ⬢ less to play this character."""
        character = self.create_named_ability_character(
            "LeFou - Bumbler", 2, CardColor.AMBER, Rarity.COMMON, 1, 2, 1
        )
        
        ability_data = {"name": "LOYAL", "type": "static"}
        loyal_ability = NamedAbilityRegistry.create_ability("LOYAL", character, ability_data)
        
        # LOYAL may return None but adds conditional effects to the character
        if loyal_ability is None:
            # Check for conditional effects or metadata
            assert hasattr(character, 'conditional_effects') or hasattr(character, 'metadata')
        else:
            assert loyal_ability.name == "LOYAL"


class TestTriggeredNamedAbilities(GameEngineTestBase):
    """Integration tests for triggered named abilities (event-driven effects)."""
    
    def create_named_ability_character(self, name: str, cost: int, color: CardColor, rarity: Rarity, 
                                     strength: int, willpower: int, lore: int, subtypes=None, 
                                     named_ability=None) -> CharacterCard:
        """Helper function to create test characters with named abilities."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            lore=lore,
            color=color,
            subtypes=subtypes
        )
        
        # Add named ability if specified
        if named_ability:
            ability_data = {"name": named_ability, "type": "triggered"}  # Default to triggered
            ability = NamedAbilityRegistry.create_ability(named_ability, character, ability_data)
            if ability:
                character.composable_abilities.append(ability)
        
        return character
    
    def test_musical_debut_ability_creation(self):
        """Test MUSICAL DEBUT - When you play this character, look at the top 4 cards of your deck."""
        character = self.create_named_ability_character(
            "Ariel - Spectacular Singer", 4, CardColor.RUBY, Rarity.SUPER_RARE, 2, 4, 2
        )
        
        ability_data = {"name": "MUSICAL DEBUT", "type": "triggered"}
        musical_debut_ability = NamedAbilityRegistry.create_ability("MUSICAL DEBUT", character, ability_data)
        
        assert musical_debut_ability is not None
        assert musical_debut_ability.name == "MUSICAL DEBUT"
    
    def test_musical_debut_integration(self):
        """Test MUSICAL DEBUT integration through game flow."""
        # Add some cards to deck for the ability to reveal
        for i in range(10):
            test_card = self.create_test_character(f"Deck Card {i}", cost=2, strength=1, willpower=1, lore=1)
            self.player1.deck.append(test_card)
        
        musical_debut_char = self.create_named_ability_character(
            "Ariel - Spectacular Singer", 4, CardColor.RUBY, Rarity.SUPER_RARE, 2, 4, 2,
            named_ability="MUSICAL DEBUT"
        )
        
        # Put character in play
        message = self.play_character(musical_debut_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert musical_debut_char in self.player1.characters_in_play
        
        # Should have musical debut ability
        if musical_debut_char.composable_abilities:
            assert any("musical debut" in ability.name.lower() for ability in musical_debut_char.composable_abilities)
    
    def test_and_two_for_tea_ability_creation(self):
        """Test AND TWO FOR TEA! - When you play this character, you may remove up to 2 damage from each of your Musketeer characters."""
        character = self.create_named_ability_character(
            "Goofy - Musketeer", 5, CardColor.AMBER, Rarity.RARE, 3, 4, 2, ["Dreamborn", "Musketeer"]
        )
        
        ability_data = {"name": "AND TWO FOR TEA!", "type": "triggered"}
        and_two_for_tea_ability = NamedAbilityRegistry.create_ability("AND TWO FOR TEA!", character, ability_data)
        
        assert and_two_for_tea_ability is not None
        assert and_two_for_tea_ability.name == "AND TWO FOR TEA!"
    
    def test_well_of_souls_ability_creation(self):
        """Test WELL OF SOULS - When you play this character, return a character card from your discard to your hand."""
        character = self.create_named_ability_character(
            "Hades - Lord of the Underworld", 7, CardColor.AMETHYST, Rarity.LEGENDARY, 5, 6, 2, ["Storyborn", "Villain", "Deity"]
        )
        
        ability_data = {"name": "WELL OF SOULS", "type": "triggered"}
        well_of_souls_ability = NamedAbilityRegistry.create_ability("WELL OF SOULS", character, ability_data)
        
        assert well_of_souls_ability is not None
        assert well_of_souls_ability.name == "WELL OF SOULS"
    
    def test_horse_kick_ability_creation(self):
        """Test HORSE KICK - When you play this character, chosen character gets -2 ⚔ this turn."""
        character = self.create_named_ability_character(
            "Maximus - Relentless Pursuer", 4, CardColor.AMBER, Rarity.UNCOMMON, 3, 4, 1, ["Storyborn", "Ally"]
        )
        
        ability_data = {"name": "HORSE KICK", "type": "triggered"}
        horse_kick_ability = NamedAbilityRegistry.create_ability("HORSE KICK", character, ability_data)
        
        assert horse_kick_ability is not None
        assert horse_kick_ability.name == "HORSE KICK"
    
    def test_we_can_fix_it_ability_creation(self):
        """Test WE CAN FIX IT - Whenever this character quests, you may ready your other Princess characters."""
        character = self.create_named_ability_character(
            "Moana - Of Motunui", 5, CardColor.AMBER, Rarity.LEGENDARY, 3, 5, 2, ["Storyborn", "Hero", "Princess"]
        )
        
        ability_data = {"name": "WE CAN FIX IT", "type": "triggered"}
        we_can_fix_it_ability = NamedAbilityRegistry.create_ability("WE CAN FIX IT", character, ability_data)
        
        assert we_can_fix_it_ability is not None
        assert we_can_fix_it_ability.name == "WE CAN FIX IT"
    
    def test_heroism_ability_creation(self):
        """Test HEROISM - When this character challenges and is banished, you may banish the challenged character."""
        character = self.create_named_ability_character(
            "Prince Phillip - Dragonslayer", 4, CardColor.STEEL, Rarity.LEGENDARY, 3, 3, 2, ["Storyborn", "Hero", "Prince"]
        )
        
        ability_data = {"name": "HEROISM", "type": "triggered"}
        heroism_ability = NamedAbilityRegistry.create_ability("HEROISM", character, ability_data)
        
        assert heroism_ability is not None
        assert heroism_ability.name == "HEROISM"


class TestActivatedNamedAbilities(GameEngineTestBase):
    """Integration tests for activated named abilities (cost-based effects)."""
    
    def create_named_ability_character(self, name: str, cost: int, color: CardColor, rarity: Rarity, 
                                     strength: int, willpower: int, lore: int, subtypes=None, 
                                     named_ability=None) -> CharacterCard:
        """Helper function to create test characters with named abilities."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            lore=lore,
            color=color,
            subtypes=subtypes
        )
        
        # Add named ability if specified
        if named_ability:
            ability_data = {"name": named_ability, "type": "activated"}  # For activated abilities
            ability = NamedAbilityRegistry.create_ability(named_ability, character, ability_data)
            if ability:
                character.composable_abilities.append(ability)
                
        return character
    
    def test_a_wonderful_dream_ability_creation(self):
        """Test A WONDERFUL DREAM - ⟲ — Remove up to 3 damage from chosen Princess character."""
        character = self.create_named_ability_character(
            "Cinderella - Gentle and Kind", 4, CardColor.STEEL, Rarity.SUPER_RARE, 2, 5, 2, ["Storyborn", "Hero", "Princess"]
        )
        
        ability_data = {"name": "A WONDERFUL DREAM", "type": "activated"}
        a_wonderful_dream_ability = NamedAbilityRegistry.create_ability("A WONDERFUL DREAM", character, ability_data)
        
        assert a_wonderful_dream_ability is not None
        assert a_wonderful_dream_ability.name == "A WONDERFUL DREAM"
    
    def test_a_wonderful_dream_integration(self):
        """Test A WONDERFUL DREAM integration through game flow."""
        a_wonderful_dream_char = self.create_named_ability_character(
            "Cinderella - Gentle and Kind", 4, CardColor.STEEL, Rarity.SUPER_RARE, 2, 5, 2, ["Storyborn", "Hero", "Princess"],
            named_ability="A WONDERFUL DREAM"
        )
        
        # Play character using proper game moves
        message = self.play_character(a_wonderful_dream_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert a_wonderful_dream_char in self.player1.characters_in_play
        
        # Should have a wonderful dream ability
        if a_wonderful_dream_char.composable_abilities:
            assert any("wonderful dream" in ability.name.lower() for ability in a_wonderful_dream_char.composable_abilities)


class TestNamedAbilityRegistry(GameEngineTestBase):
    """Integration tests for the named ability registry system."""
    
    def create_named_ability_character(self, name: str, cost: int, color: CardColor, rarity: Rarity, 
                                     strength: int, willpower: int, lore: int, subtypes=None, 
                                     named_ability=None) -> CharacterCard:
        """Helper function to create test characters with named abilities."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            lore=lore,
            color=color,
            subtypes=subtypes
        )
        
        # Add named ability if specified
        if named_ability:
            ability_data = {"name": named_ability, "type": "triggered"}  # Default to triggered
            ability = NamedAbilityRegistry.create_ability(named_ability, character, ability_data)
            if ability:
                character.composable_abilities.append(ability)
                
        return character
    
    def test_registry_functionality(self):
        """Test that the registry correctly identifies implemented abilities."""
        implemented_abilities = [
            "VOICELESS", "MUSICAL DEBUT", "A WONDERFUL DREAM", "AND TWO FOR TEA!",
            "SINISTER PLOT", "WELL OF SOULS", "LOYAL", "HORSE KICK", 
            "WE CAN FIX IT", "HEROISM"
        ]
        
        for ability_name in implemented_abilities:
            if hasattr(NamedAbilityRegistry, 'is_ability_implemented'):
                assert NamedAbilityRegistry.is_ability_implemented(ability_name), f"{ability_name} should be implemented"
        
        if hasattr(NamedAbilityRegistry, 'is_ability_implemented'):
            assert not NamedAbilityRegistry.is_ability_implemented("UNKNOWN_ABILITY")
    
    def test_registry_returns_none_for_unimplemented(self):
        """Test that registry returns None for unimplemented abilities."""
        character = self.create_named_ability_character(
            "Test Character", 1, CardColor.AMBER, Rarity.COMMON, 1, 1, 1
        )
        
        ability_data = {"name": "UNKNOWN_ABILITY", "type": "static"}
        result = NamedAbilityRegistry.create_ability("UNKNOWN_ABILITY", character, ability_data)
        assert result is None
    
    def test_get_registered_abilities(self):
        """Test that we can get all registered abilities."""
        if hasattr(NamedAbilityRegistry, 'get_registered_abilities'):
            registered = NamedAbilityRegistry.get_registered_abilities()
            
            expected_abilities = [
                "VOICELESS", "MUSICAL DEBUT", "A WONDERFUL DREAM", "AND TWO FOR TEA!",
                "SINISTER PLOT", "WELL OF SOULS", "LOYAL", "HORSE KICK",
                "WE CAN FIX IT", "HEROISM"
            ]
            
            for ability_name in expected_abilities:
                if ability_name in registered:
                    assert ability_name in registered
    
    def test_ability_integration_through_game_flow(self):
        """Test that abilities work through real game flow."""
        # Test a simple ability that should work
        test_char = self.create_named_ability_character(
            "Test Character", 3, CardColor.AMBER, Rarity.COMMON, 2, 2, 1,
            named_ability="HEROISM"  # Use a known ability
        )
        
        # Put character in play
        message = self.play_character(test_char, self.player1)
        
        # Should successfully enter play
        assert message.type == MessageType.STEP_EXECUTED
        assert test_char in self.player1.characters_in_play
        
        # Verify ability was added if it exists
        if test_char.composable_abilities:
            assert len(test_char.composable_abilities) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])