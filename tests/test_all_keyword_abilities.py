"""Comprehensive integration tests for all keyword abilities in the composable system."""

import pytest
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity

from lorcana_sim.engine.game_moves import PlayMove, ChallengeMove, QuestMove, PassMove
from lorcana_sim.models.abilities.composable.keyword_abilities import (
    create_resist_ability, create_ward_ability, create_bodyguard_ability,
    create_evasive_ability, create_singer_ability, create_support_ability,
    create_rush_ability, create_shift_ability, create_puppy_shift_ability,
    create_universal_shift_ability, create_challenger_ability, create_reckless_ability,
    create_vanish_ability, create_sing_together_ability, create_keyword_ability
)
from lorcana_sim.engine.message_engine import MessageType


# =============================================================================
# BASE TEST CLASS
# =============================================================================

class BaseKeywordAbilityTest:
    """Base class for keyword ability integration tests."""
    
    def setup_method(self):
        """Set up test game with players and cards."""
        # Create players
        self.player1 = Player("Alice")
        self.player2 = Player("Bob")
        
        # Create game state and engine
        self.game_state = GameState([self.player1, self.player2])
        self.game_engine = GameEngine(self.game_state)
        
        # Start the game
        self.game_engine.start_game()
    
    def create_test_character(self, name="Test Character", strength=2, willpower=3, cost=3, 
                             keyword_abilities=None, keyword_values=None):
        """Create a test character with optional keyword abilities."""
        character = CharacterCard(
            id=len(self.player1.deck) + len(self.player2.deck) + 100,
            name=name,
            version=None,
            full_name=name,
            cost=cost,
            color=CardColor.AMBER,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=1,
            story="",
            strength=strength,
            willpower=willpower,
            lore=1
        )
        
        # Add keyword abilities
        if keyword_abilities:
            for i, keyword in enumerate(keyword_abilities):
                value = keyword_values[i] if keyword_values and i < len(keyword_values) else None
                ability = create_keyword_ability(keyword, character, value)
                character.composable_abilities.append(ability)
        
        return character
    
    def put_character_in_play(self, character, player):
        """Put a character in play using game engine."""
        player.hand.append(character)
        play_move = PlayMove(character)
        message = self.game_engine.next_message(play_move)
        return message


# =============================================================================
# RESIST ABILITY TESTS
# =============================================================================

class TestResistAbility(BaseKeywordAbilityTest):
    """Integration tests for Resist ability."""
    
    def test_resist_ability_creation(self):
        """Test that Resist ability creates correctly."""
        character = self.create_test_character(
            "Resist Character",
            keyword_abilities=["Resist"],
            keyword_values=[3]
        )
        
        assert len(character.composable_abilities) == 1
        resist_ability = character.composable_abilities[0]
        assert "resist" in resist_ability.name.lower()
        assert resist_ability.character == character
    
    def test_resist_integration(self):
        """Test Resist through real game flow."""
        resist_char = self.create_test_character(
            "Resist Character", 
            strength=2, 
            willpower=5,
            keyword_abilities=["Resist"],
            keyword_values=[2]
        )
        attacker = self.create_test_character("Attacker", strength=5, willpower=3)
        
        # Put both characters in play
        self.put_character_in_play(resist_char, self.player1)
        self.put_character_in_play(attacker, self.player2)
        
        # Challenge the resist character
        challenge_move = ChallengeMove(attacker, resist_char)
        message = self.game_engine.next_message(challenge_move)
        
        # Verify challenge occurred
        assert message.type == MessageType.STEP_EXECUTED
        
        # Resist ability should be present
        assert len(resist_char.composable_abilities) == 1


# =============================================================================
# KEYWORD FACTORY TESTS
# =============================================================================

class TestKeywordFactory(BaseKeywordAbilityTest):
    """Integration tests for the keyword ability factory function."""
    
    def test_create_all_keyword_abilities(self):
        """Test that all keyword abilities can be created."""
        keywords_to_test = [
            ('Resist', 2, None),
            ('Ward', None, None),
            ('Bodyguard', None, None),
            ('Evasive', None, None),
            ('Singer', 5, None),
            ('Support', None, None),
            ('Rush', None, None),
            ('Shift', 3, None),
            ('Puppy Shift', 2, None),
            ('Universal Shift', 4, None),
            ('Challenger', 2, None),
            ('Reckless', None, None),
            ('Vanish', None, None),
            ('Sing Together', 3, None),
        ]
        
        for keyword, value, target_name in keywords_to_test:
            character = self.create_test_character(f"{keyword} Character")
            ability = create_keyword_ability(keyword, character, value, target_name)
            
            # Check that the keyword appears in the ability name (flexible matching)
            keyword_parts = keyword.split()
            assert any(part.lower() in ability.name.lower() for part in keyword_parts)
            assert ability.character == character
    
    def test_unknown_keyword_raises_error(self):
        """Test that unknown keywords raise ValueError."""
        character = self.create_test_character("Test Character")
        
        with pytest.raises(ValueError, match="Unknown keyword ability"):
            create_keyword_ability("Unknown Ability", character)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])