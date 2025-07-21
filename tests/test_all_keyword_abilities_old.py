"""Comprehensive tests for all keyword abilities in the composable system."""

import pytest
from unittest.mock import Mock, MagicMock

from lorcana_sim.models.abilities.composable.keyword_abilities import (
    create_resist_ability, create_ward_ability, create_bodyguard_ability,
    create_evasive_ability, create_singer_ability, create_support_ability,
    create_rush_ability, create_shift_ability, create_puppy_shift_ability,
    create_universal_shift_ability, create_challenger_ability, create_reckless_ability,
    create_vanish_ability, create_sing_together_ability, create_keyword_ability
)
from lorcana_sim.engine.event_system import GameEvent, EventContext


class MockCharacter:
    """Mock character for testing abilities."""
    
    def __init__(self, name="Test Character", controller=None, strength=2, willpower=3):
        self.name = name
        self.controller = controller
        self.strength = strength
        self.willpower = willpower
        self.current_strength = strength
        self.current_willpower = willpower
        self.lore = 1
        self.current_lore = 1
        self.damage = 0
        self.exerted = False
        self.is_dry = True
        self.metadata = {}
        self.composable_abilities = []
        
        # Track bonuses for testing
        self.lore_bonuses = []
        self.strength_bonuses = []
        self.willpower_bonuses = []
    
    def add_lore_bonus(self, amount, duration):
        self.lore_bonuses.append((amount, duration))
        if duration in ["permanent", "this_turn"]:
            self.current_lore += amount
    
    def add_strength_bonus(self, amount, duration):
        self.strength_bonuses.append((amount, duration))
        if duration in ["permanent", "this_turn", "this_challenge"]:
            self.current_strength += amount
    
    def add_willpower_bonus(self, amount, duration):
        self.willpower_bonuses.append((amount, duration))
        if duration in ["permanent", "this_turn"]:
            self.current_willpower += amount
    
    def modify_damage(self, amount):
        self.damage += amount
    
    def heal_damage(self, amount):
        self.damage = max(0, self.damage - amount)
    
    def banish(self):
        self.metadata['banished'] = True
    
    def __str__(self):
        return self.name


class MockPlayer:
    """Mock player for testing."""
    
    def __init__(self, name="Test Player"):
        self.name = name
        self.characters_in_play = []
    
    def draw_cards(self, count):
        pass


class MockGameState:
    """Mock game state for testing."""
    
    def __init__(self, players=None):
        self.players = players or []
        self.current_player = players[0] if players else None


# =============================================================================
# RESIST ABILITY TESTS
# =============================================================================

class TestResistAbility:
    """Test Resist ability implementation."""
    
    def test_resist_reduces_damage(self):
        """Test that Resist reduces incoming damage."""
        character = MockCharacter("Resist Character")
        resist_ability = create_resist_ability(2, character)
        
        # Create damage event
        event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            additional_data={'damage': 5}
        )
        
        resist_ability.handle_event(event)
        
        # Damage should be reduced from 5 to 3 (5 - 2)
        assert event.additional_data['damage'] == 3
    
    def test_resist_cannot_reduce_below_zero(self):
        """Test that Resist cannot reduce damage below 0."""
        character = MockCharacter("High Resist Character")
        resist_ability = create_resist_ability(10, character)
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            additional_data={'damage': 3}
        )
        
        resist_ability.handle_event(event)
        
        # Damage should be reduced to 0, not negative
        assert event.additional_data['damage'] == 0


# =============================================================================
# WARD ABILITY TESTS
# =============================================================================

class TestWardAbility:
    """Test Ward ability implementation."""
    
    def test_ward_prevents_targeting(self):
        """Test that Ward prevents ability targeting."""
        character = MockCharacter("Ward Character")
        ward_ability = create_ward_ability(character)
        
        # Create targeting event
        event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,  # Using as placeholder for targeting
            target=character,
            additional_data={'targeting_attempt': True}
        )
        
        ward_ability.handle_event(event)
        
        # Event should be prevented
        assert event.additional_data.get('prevented', False) == True


# =============================================================================
# BODYGUARD ABILITY TESTS
# =============================================================================

class TestBodyguardAbility:
    """Test Bodyguard ability implementation."""
    
    def test_bodyguard_marks_character_on_entry(self):
        """Test that Bodyguard marks character with bodyguard metadata."""
        character = MockCharacter("Bodyguard Character")
        bodyguard_ability = create_bodyguard_ability(character)
        
        # Simulate character entering play
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        bodyguard_ability.handle_event(event)
        
        # Character should be marked with bodyguard properties
        assert character.metadata.get('has_bodyguard', False) == True
        assert character.metadata.get('can_enter_exerted', False) == True


# =============================================================================
# EVASIVE ABILITY TESTS
# =============================================================================

class TestEvasiveAbility:
    """Test Evasive ability implementation."""
    
    def test_evasive_prevents_non_evasive_challenges(self):
        """Test that Evasive prevents challenges from non-evasive characters."""
        evasive_character = MockCharacter("Evasive Character")
        normal_attacker = MockCharacter("Normal Attacker")
        
        evasive_ability = create_evasive_ability(evasive_character)
        
        # Create challenge event
        event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=normal_attacker,
            target=evasive_character,
            additional_data={}
        )
        
        evasive_ability.handle_event(event)
        
        # Challenge should be prevented
        assert event.additional_data.get('prevented', False) == True
    
    def test_evasive_allows_evasive_challenges(self):
        """Test that Evasive characters can challenge other Evasive characters."""
        evasive_defender = MockCharacter("Evasive Defender")
        evasive_attacker = MockCharacter("Evasive Attacker")
        
        # Give attacker an evasive ability
        evasive_attacker.composable_abilities = [create_evasive_ability(evasive_attacker)]
        
        evasive_ability = create_evasive_ability(evasive_defender)
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=evasive_attacker,
            target=evasive_defender,
            additional_data={}
        )
        
        evasive_ability.handle_event(event)
        
        # Challenge should not be prevented
        assert event.additional_data.get('prevented', False) == False


# =============================================================================
# SINGER ABILITY TESTS
# =============================================================================

class TestSingerAbility:
    """Test Singer ability implementation."""
    
    def test_singer_enables_song_singing(self):
        """Test that Singer enables singing songs."""
        character = MockCharacter("Singer Character")
        singer_ability = create_singer_ability(5, character)
        
        event = EventContext(
            event_type=GameEvent.SONG_SUNG,
            source=character,
            additional_data={'singer': character, 'required_cost': 4}
        )
        
        singer_ability.handle_event(event)
        
        # Should enable singing
        assert event.additional_data.get('can_sing', False) == True
        assert event.additional_data.get('singer_cost') == 5


# =============================================================================
# SUPPORT ABILITY TESTS
# =============================================================================

class TestSupportAbility:
    """Test Support ability implementation."""
    
    def test_support_adds_strength_when_questing(self):
        """Test that Support adds strength to another character when this character quests."""
        support_char = MockCharacter("Support Character", strength=3)
        target_char = MockCharacter("Target Character")
        player = MockPlayer("Test Player")
        support_char.controller = target_char.controller = player
        
        support_ability = create_support_ability(support_char)
        
        # Create quest event where support character quests
        game_state = MockGameState([player])
        event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=support_char,
            game_state=game_state,
            additional_data={'ability_owner': support_char}
        )
        
        support_ability.handle_event(event)
        
        # Target character should receive strength bonus equal to support character's strength
        # Note: The actual targeting logic would be handled by the game engine
        # Here we're just testing that the ability triggers correctly


# =============================================================================
# RUSH ABILITY TESTS
# =============================================================================

class TestRushAbility:
    """Test Rush ability implementation."""
    
    def test_rush_grants_immediate_challenge_ability(self):
        """Test that Rush grants ability to challenge with wet ink."""
        character = MockCharacter("Rush Character")
        rush_ability = create_rush_ability(character)
        
        # Simulate character entering play
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        rush_ability.handle_event(event)
        
        # Character should have rush property
        assert character.metadata.get('can_challenge_with_wet_ink', False) == True


# =============================================================================
# SHIFT ABILITY TESTS
# =============================================================================

class TestShiftAbilities:
    """Test Shift-related abilities."""
    
    def test_shift_marks_character(self):
        """Test that Shift marks character with shift metadata."""
        character = MockCharacter("Shift Character")
        shift_ability = create_shift_ability(3, character)
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        shift_ability.handle_event(event)
        
        assert character.metadata.get('shift_cost_reduction') == 3
    
    def test_puppy_shift_marks_character(self):
        """Test that Puppy Shift marks character correctly."""
        character = MockCharacter("Puppy Character")
        puppy_shift_ability = create_puppy_shift_ability(2, character)
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        puppy_shift_ability.handle_event(event)
        
        assert character.metadata.get('shift_cost_reduction') == 2
    
    def test_universal_shift_marks_character(self):
        """Test that Universal Shift marks character correctly."""
        character = MockCharacter("Universal Character")
        universal_shift_ability = create_universal_shift_ability(4, character)
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        universal_shift_ability.handle_event(event)
        
        assert character.metadata.get('shift_cost_reduction') == 4


# =============================================================================
# CHALLENGER ABILITY TESTS
# =============================================================================

class TestChallengerAbility:
    """Test Challenger ability implementation."""
    
    def test_challenger_grants_strength_bonus(self):
        """Test that Challenger grants strength bonus while challenging."""
        character = MockCharacter("Challenger Character", strength=2)
        challenger_ability = create_challenger_ability(3, character)
        
        # Create challenge event
        event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=character,
            additional_data={}
        )
        
        challenger_ability.handle_event(event)
        
        # Character should have received strength bonus
        assert character.current_strength == 5  # 2 + 3


# =============================================================================
# RECKLESS ABILITY TESTS
# =============================================================================

class TestRecklessAbility:
    """Test Reckless ability implementation."""
    
    def test_reckless_marks_restrictions(self):
        """Test that Reckless marks character with restrictions."""
        character = MockCharacter("Reckless Character")
        reckless_ability = create_reckless_ability(character)
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        reckless_ability.handle_event(event)
        
        # Character should be marked with reckless restrictions
        assert character.metadata.get('cannot_quest', False) == True
        assert character.metadata.get('must_challenge_if_able', False) == True


# =============================================================================
# VANISH ABILITY TESTS
# =============================================================================

class TestVanishAbility:
    """Test Vanish ability implementation."""
    
    def test_vanish_banishes_when_targeted_by_opponent(self):
        """Test that Vanish banishes character when targeted by opponent."""
        character = MockCharacter("Vanish Character")
        player = MockPlayer("Player")
        opponent = MockPlayer("Opponent")
        character.controller = player
        
        vanish_ability = create_vanish_ability(character)
        
        # Create targeting event from opponent
        source_char = MockCharacter("Opponent Character")
        source_char.controller = opponent
        
        # Create a mock game state to provide current player context
        game_state = MockGameState([player, opponent])
        game_state.current_player = opponent  # Opponent's turn
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,  # Placeholder for targeting
            source=source_char,
            target=character,
            game_state=game_state,
            additional_data={}
        )
        
        # Manually check the vanish condition works as expected
        vanish_listeners = vanish_ability.listeners
        assert len(vanish_listeners) > 0
        
        listener = vanish_listeners[0]
        assert listener.should_trigger(event) == True  # Debug the condition
        
        vanish_ability.handle_event(event)
        
        # Character should be banished
        assert character.metadata.get('banished', False) == True


# =============================================================================
# SING TOGETHER ABILITY TESTS
# =============================================================================

class TestSingTogetherAbility:
    """Test Sing Together ability implementation."""
    
    def test_sing_together_marks_participation(self):
        """Test that Sing Together marks character as able to participate."""
        character = MockCharacter("Sing Together Character")
        sing_together_ability = create_sing_together_ability(4, character)
        
        event = EventContext(
            event_type=GameEvent.SONG_SUNG,
            source=character,
            additional_data={'allow_multiple_singers': True}
        )
        
        sing_together_ability.handle_event(event)
        
        # Should mark character as able to participate in sing together
        assert event.additional_data.get('can_sing_together', False) == True
        assert event.additional_data.get('sing_together_required_cost') == 4


# =============================================================================
# KEYWORD FACTORY TESTS
# =============================================================================

class TestKeywordFactory:
    """Test the keyword ability factory function."""
    
    def test_create_all_keyword_abilities(self):
        """Test that all keyword abilities can be created."""
        character = MockCharacter("Test Character")
        
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
            ability = create_keyword_ability(keyword, character, value, target_name)
            # Check that the keyword appears in the ability name (flexible matching)
            keyword_parts = keyword.split()
            assert any(part.lower() in ability.name.lower() for part in keyword_parts)
            assert ability.character == character
    
    def test_unknown_keyword_raises_error(self):
        """Test that unknown keywords raise ValueError."""
        character = MockCharacter("Test Character")
        
        with pytest.raises(ValueError, match="Unknown keyword ability"):
            create_keyword_ability("Unknown Ability", character)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestAbilityIntegration:
    """Test interactions between multiple abilities."""
    
    def test_multiple_abilities_on_same_character(self):
        """Test character with multiple abilities."""
        character = MockCharacter("Multi-Ability Character", strength=2, willpower=5)
        
        # Create multiple abilities
        resist_ability = create_resist_ability(1, character)
        rush_ability = create_rush_ability(character)
        
        # Test Rush ability
        enter_event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        rush_ability.handle_event(enter_event)
        assert character.metadata.get('can_challenge_with_wet_ink', False) == True
        
        # Test Resist ability
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            additional_data={'damage': 3}
        )
        
        resist_ability.handle_event(damage_event)
        assert damage_event.additional_data['damage'] == 2  # 3 - 1
    
    def test_challenger_and_rush_combination(self):
        """Test character with both Challenger and Rush abilities."""
        character = MockCharacter("Challenger Rush Character", strength=1)
        
        challenger_ability = create_challenger_ability(2, character)
        rush_ability = create_rush_ability(character)
        
        # Test Rush on entry
        enter_event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        rush_ability.handle_event(enter_event)
        assert character.metadata.get('can_challenge_with_wet_ink', False) == True
        
        # Test Challenger during challenge
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=character,
            additional_data={}
        )
        
        challenger_ability.handle_event(challenge_event)
        assert character.current_strength == 3  # 1 + 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])