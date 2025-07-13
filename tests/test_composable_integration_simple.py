"""Simple integration tests for composable keyword abilities without full game engine."""

import pytest
from unittest.mock import Mock

from lorcana_sim.engine.event_system import GameEvent, EventContext

# Import our composable keyword abilities
from lorcana_sim.models.abilities.composable.keyword_abilities import (
    create_resist_ability, create_ward_ability, create_bodyguard_ability,
    create_evasive_ability, create_singer_ability, create_support_ability, 
    create_rush_ability
)


class MockCharacter:
    """Simple mock character for testing."""
    
    def __init__(self, name: str, controller=None):
        self.name = name
        self.controller = controller
        self.exerted = False
        self.metadata = {}
        
        # Track bonuses for testing
        self.lore_bonuses = []
        self.strength_bonuses = []
        self.willpower_bonuses = []
    
    def add_lore_bonus(self, amount, duration):
        self.lore_bonuses.append((amount, duration))
    
    def add_strength_bonus(self, amount, duration):
        self.strength_bonuses.append((amount, duration))
    
    def add_willpower_bonus(self, amount, duration):
        self.willpower_bonuses.append((amount, duration))
    
    def __str__(self):
        return self.name


class MockPlayer:
    """Simple mock player."""
    
    def __init__(self, name: str):
        self.name = name
        self.characters_in_play = []


class MockGameState:
    """Simple mock game state."""
    
    def __init__(self, players):
        self.all_players = players
        self.current_player = players[0] if players else None


class TestResistAbilityIntegration:
    """Test Resist ability with direct ability calls."""
    
    def test_resist_reduces_damage_directly(self):
        """Test that Resist ability reduces damage when called directly."""
        character = MockCharacter("Resist Character")
        resist_ability = create_resist_ability(2, character)
        
        # Create damage event
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            additional_data={'damage': 5}
        )
        
        # Call the ability directly
        resist_ability.handle_event(damage_event)
        
        # Damage should be reduced from 5 to 3 (5 - 2 resist)
        assert damage_event.additional_data['damage'] == 3
    
    def test_resist_cannot_reduce_below_zero(self):
        """Test that Resist cannot reduce damage below 0."""
        character = MockCharacter("High Resist Character")
        resist_ability = create_resist_ability(10, character)
        
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            additional_data={'damage': 3}
        )
        
        resist_ability.handle_event(damage_event)
        
        # Damage should be reduced to 0, not negative
        assert damage_event.additional_data['damage'] == 0
    
    def test_multiple_resist_abilities_stack(self):
        """Test that multiple Resist abilities on the same character stack."""
        character = MockCharacter("Multi-Resist Character")
        resist1 = create_resist_ability(2, character)
        resist2 = create_resist_ability(1, character)
        
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            additional_data={'damage': 6}
        )
        
        # Apply both resist abilities
        resist1.handle_event(damage_event)
        resist2.handle_event(damage_event)
        
        # Damage should be reduced by both: 6 - 2 - 1 = 3
        assert damage_event.additional_data['damage'] == 3


class TestSupportAbilityIntegration:
    """Test Support ability with direct ability calls."""
    
    def test_support_gives_lore_bonus_on_quest(self):
        """Test that Support ability gives lore bonus when character quests."""
        support_char = MockCharacter("Support Character")
        target_char = MockCharacter("Target Character")
        
        # Set up friendly characters (same controller)
        controller = Mock()
        support_char.controller = target_char.controller = controller
        
        # Create game state with both characters
        player = MockPlayer("Player 1")
        player.characters_in_play = [support_char, target_char]
        game_state = MockGameState([player])
        
        support_ability = create_support_ability(2, support_char)
        
        # Create quest event - target character quests, support character provides bonus
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=target_char,  # The character who is questing
            game_state=game_state,
            additional_data={}
        )
        
        # Call the ability
        support_ability.handle_event(quest_event)
        
        # Target character should have received lore bonus
        assert len(target_char.lore_bonuses) == 1
        assert target_char.lore_bonuses[0] == (2, "this_turn")
    
    def test_support_only_affects_other_characters(self):
        """Test that Support doesn't target the character with the ability."""
        support_char = MockCharacter("Support Character")
        support_char.controller = Mock()
        
        # Only support character in play
        player = MockPlayer("Player 1")
        player.characters_in_play = [support_char]
        game_state = MockGameState([player])
        
        support_ability = create_support_ability(1, support_char)
        
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=support_char,
            game_state=game_state,
            additional_data={}
        )
        
        support_ability.handle_event(quest_event)
        
        # Support character shouldn't have received the bonus
        assert len(support_char.lore_bonuses) == 0


class TestRushAbilityIntegration:
    """Test Rush ability with direct ability calls."""
    
    def test_rush_grants_challenge_ability(self):
        """Test that Rush allows character to challenge immediately."""
        character = MockCharacter("Rush Character")
        rush_ability = create_rush_ability(character)
        
        # Create enters play event
        play_event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        rush_ability.handle_event(play_event)
        
        # Character should have the rush property
        assert character.metadata.get('can_challenge_with_wet_ink', False) == True


class TestWardAbilityIntegration:
    """Test Ward ability with direct ability calls."""
    
    def test_ward_prevents_targeting(self):
        """Test that Ward prevents ability targeting."""
        character = MockCharacter("Ward Character")
        ward_ability = create_ward_ability(character)
        
        # Create targeting event
        targeting_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,  # Using as placeholder
            target=character,
            additional_data={'targeting_attempt': True}
        )
        
        ward_ability.handle_event(targeting_event)
        
        # Event should be prevented
        assert targeting_event.additional_data.get('prevented', False) == True


class TestEvasiveAbilityIntegration:
    """Test Evasive ability with direct ability calls."""
    
    def test_evasive_prevents_normal_challenges(self):
        """Test that Evasive prevents challenges from non-evasive characters."""
        evasive_char = MockCharacter("Evasive Character")
        evasive_ability = create_evasive_ability(evasive_char)
        
        normal_attacker = MockCharacter("Normal Attacker")
        
        # Create challenge event
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=normal_attacker,
            target=evasive_char,
            additional_data={}
        )
        
        evasive_ability.handle_event(challenge_event)
        
        # Challenge should be prevented
        assert challenge_event.additional_data.get('prevented', False) == True
    
    def test_evasive_allows_evasive_challenges(self):
        """Test that Evasive characters can challenge other Evasive characters."""
        evasive_defender = MockCharacter("Evasive Defender")
        evasive_ability = create_evasive_ability(evasive_defender)
        
        # Create attacker with Evasive ability (mock properly)
        evasive_attacker = MockCharacter("Evasive Attacker")
        mock_evasive_ability = Mock()
        mock_evasive_ability.name = "Evasive"
        evasive_attacker.composable_abilities = [mock_evasive_ability]
        
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=evasive_attacker,
            target=evasive_defender,
            additional_data={}
        )
        
        evasive_ability.handle_event(challenge_event)
        
        # Challenge should not be prevented (both have Evasive)
        assert challenge_event.additional_data.get('prevented', False) == False


class TestSingerAbilityIntegration:
    """Test Singer ability with direct ability calls."""
    
    def test_singer_enables_song_singing(self):
        """Test that Singer ability enables singing songs."""
        character = MockCharacter("Singer Character")
        singer_ability = create_singer_ability(5, character)
        
        # Create song event
        sing_event = EventContext(
            event_type=GameEvent.SONG_SUNG,
            source=character,
            additional_data={'singer': character, 'required_cost': 4}
        )
        
        singer_ability.handle_event(sing_event)
        
        # Should enable singing
        assert sing_event.additional_data.get('can_sing', False) == True
        assert sing_event.additional_data.get('singer_cost') == 5


class TestBodyguardAbilityIntegration:
    """Test Bodyguard ability with direct ability calls."""
    
    def test_bodyguard_redirects_challenges(self):
        """Test that Bodyguard redirects challenges."""
        bodyguard = MockCharacter("Bodyguard")
        bodyguard.exerted = False  # Ready bodyguard
        bodyguard_ability = create_bodyguard_ability(bodyguard)
        
        protected_char = MockCharacter("Protected Character")
        attacker = MockCharacter("Attacker")
        
        # Set up controllers (bodyguard and protected are friendly, attacker is enemy)
        friendly_controller = Mock()
        enemy_controller = Mock()
        bodyguard.controller = protected_char.controller = friendly_controller
        attacker.controller = enemy_controller
        
        # Create challenge event against protected character
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=attacker,
            target=protected_char,
            additional_data={}
        )
        
        bodyguard_ability.handle_event(challenge_event)
        
        # Challenge should be retargeted
        assert challenge_event.additional_data.get('retargeted', False) == True


class TestMultipleAbilityInteractions:
    """Test interactions between multiple abilities."""
    
    def test_character_with_resist_and_support(self):
        """Test character with both Resist and Support working together."""
        multi_char = MockCharacter("Multi-Ability Character")
        friendly_char = MockCharacter("Friendly Character")
        
        controller = Mock()
        multi_char.controller = friendly_char.controller = controller
        
        player = MockPlayer("Player 1")
        player.characters_in_play = [multi_char, friendly_char]
        game_state = MockGameState([player])
        
        # Create both abilities
        resist_ability = create_resist_ability(1, multi_char)
        support_ability = create_support_ability(2, multi_char)
        
        # Test Support triggers on quest - friendly_char quests and gets bonus from multi_char
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=friendly_char,  # The character who is questing
            game_state=game_state,
            additional_data={}
        )
        
        support_ability.handle_event(quest_event)
        assert len(friendly_char.lore_bonuses) == 1
        assert friendly_char.lore_bonuses[0] == (2, "this_turn")
        
        # Test Resist reduces damage
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=multi_char,
            additional_data={'damage': 4}
        )
        
        resist_ability.handle_event(damage_event)
        assert damage_event.additional_data['damage'] == 3  # 4 - 1 resist


if __name__ == "__main__":
    pytest.main([__file__, "-v"])