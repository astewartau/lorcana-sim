"""Tests for Singer keyword ability - both unit and integration tests."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry, SingerAbility
from lorcana_sim.models.abilities.base_ability import AbilityType
from lorcana_sim.engine.game_engine import GameAction
from tests.helpers import (
    create_test_character, create_test_song, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestSingerAbilityUnit:
    """Unit tests for Singer keyword ability implementation."""
    
    def test_singer_creation(self):
        """Test creating Singer ability."""
        singer = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer 5",
            keyword="Singer",
            value=5
        )
        
        assert singer.keyword == "Singer"
        assert singer.value == 5
        assert singer.get_effective_sing_cost() == 5
        assert str(singer) == "Singer 5"
    
    def test_singer_without_value(self):
        """Test Singer ability without value."""
        singer = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer",
            keyword="Singer",
            value=None
        )
        
        assert singer.get_effective_sing_cost() == 0
        assert str(singer) == "Singer"
    
    def test_can_sing_song(self):
        """Test if Singer can sing specific songs."""
        singer_5 = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer 5",
            keyword="Singer",
            value=5
        )
        
        song_cost_3 = create_test_song(cost=4, singer_cost=3)
        song_cost_5 = create_test_song(cost=6, singer_cost=5)
        song_cost_7 = create_test_song(cost=8, singer_cost=7)
        
        # Singer 5 can sing songs requiring cost 5 or less
        assert singer_5.can_sing_song(song_cost_3) == True
        assert singer_5.can_sing_song(song_cost_5) == True
        assert singer_5.can_sing_song(song_cost_7) == False
    
    def test_get_cost_reduction(self):
        """Test cost reduction calculation."""
        singer_5 = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer 5",
            keyword="Singer",
            value=5
        )
        
        song = create_test_song(cost=6, singer_cost=5)
        
        # When singer can sing the song, reduction equals the song's full cost
        reduction = singer_5.get_cost_reduction(song)
        assert reduction == 6  # Full cost of the song
    
    def test_passive_ability(self):
        """Test that Singer is a passive ability."""
        singer = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer 5",
            keyword="Singer",
            value=5
        )
        
        # Singer should not be activatable
        assert singer.can_activate(None) == False
    
    def test_registry_creation(self):
        """Test creating Singer ability via registry."""
        singer = KeywordRegistry.create_keyword_ability('Singer', value=4)
        
        assert isinstance(singer, SingerAbility)
        assert singer.keyword == 'Singer'
        assert singer.value == 4
        assert singer.type == AbilityType.KEYWORD


class TestSingerAbilityIntegration:
    """Integration tests for Singer keyword ability with game state."""
    
    def test_singer_enables_song_singing(self):
        """Test that Singer enables song singing as a legal move."""
        # Create singer ability
        singer_ability = KeywordRegistry.create_keyword_ability('Singer', value=5)
        
        # Create characters
        singer_char = create_character_with_ability("Ariel", singer_ability)
        normal_char = create_test_character("Mickey Mouse")
        
        # Create song
        song = create_test_song(cost=6, singer_cost=5, name="Part of Your World")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([singer_char], [normal_char])
        
        # Add song to hand
        game_state.current_player.hand.append(song)
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should be able to sing the song
        sing_actions = [action for action, params in legal_actions 
                       if action == GameAction.SING_SONG]
        
        assert len(sing_actions) > 0, "Singer should enable song singing"
    
    def test_singer_value_restriction(self):
        """Test that Singer value restricts which songs can be sung."""
        # Create singer abilities with different values
        singer_3_ability = KeywordRegistry.create_keyword_ability('Singer', value=3)
        singer_7_ability = KeywordRegistry.create_keyword_ability('Singer', value=7)
        
        # Create characters
        singer_3_char = create_character_with_ability("Cinderella", singer_3_ability)
        singer_7_char = create_character_with_ability("Sebastian", singer_7_ability)
        
        # Create songs with different requirements
        easy_song = create_test_song(cost=4, singer_cost=3, name="A Dream is a Wish")
        hard_song = create_test_song(cost=8, singer_cost=6, name="Under the Sea")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [singer_3_char, singer_7_char], []
        )
        
        # Add songs to hand
        game_state.current_player.hand.extend([easy_song, hard_song])
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        sing_actions = [action for action, params in legal_actions 
                       if action == GameAction.SING_SONG]
        
        # Both singers should be able to sing the easy song
        # Only the higher-cost singer should be able to sing the hard song
        assert len(sing_actions) > 0, "Should have some sing actions available"
        
        # In a full implementation, we'd check specific singer-song combinations
        # For now, we verify that the action is available
    
    def test_exerted_singer_cannot_sing(self):
        """Test that exerted singers cannot sing songs."""
        # Create singer ability
        singer_ability = KeywordRegistry.create_keyword_ability('Singer', value=5)
        
        # Create character
        singer_char = create_character_with_ability("Ariel", singer_ability)
        singer_char.exerted = True  # Exert the singer
        
        # Create song
        song = create_test_song(cost=6, singer_cost=5, name="Part of Your World")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([singer_char], [])
        
        # Add song to hand
        game_state.current_player.hand.append(song)
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should NOT be able to sing the song with exerted singer
        sing_actions = [action for action, params in legal_actions 
                       if action == GameAction.SING_SONG]
        
        assert len(sing_actions) == 0, "Exerted singer should not be able to sing"
    
    def test_singer_actual_song_execution(self):
        """Test that Singer ability actually allows songs to be sung."""
        # Create singer ability
        singer_ability = KeywordRegistry.create_keyword_ability('Singer', value=5)
        
        # Create characters
        singer_char = create_character_with_ability("Ariel", singer_ability)
        
        # Create song that requires Singer 5
        song = create_test_song(cost=6, singer_cost=5, name="Part of Your World")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([singer_char], [])
        
        # Add song to hand and give enough ink
        game_state.current_player.hand.append(song)
        for i in range(10):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Try to sing the song
        success, message = engine.execute_action(GameAction.SING_SONG, {
            'song': song,
            'singer': singer_char
        })
        
        # Verify song was sung successfully
        assert success == True
        assert "sang" in message.lower()
        assert singer_char.exerted == True  # Singer should be exerted
        assert song not in game_state.current_player.hand  # Song should be removed from hand
        assert song in game_state.current_player.discard_pile  # Song should be in discard
    
    def test_singer_cost_delegation_methods(self):
        """Test that Singer properly implements delegation methods for cost modification."""
        # Create singer ability
        singer_ability = KeywordRegistry.create_keyword_ability('Singer', value=4)
        
        # Create characters and song
        singer_char = create_character_with_ability("Singer", singer_ability)
        song = create_test_song(cost=5, singer_cost=4)
        
        # Setup game state
        game_state, validator, engine = setup_game_with_characters([singer_char], [])
        
        # Test delegation methods
        can_sing = singer_ability.allows_singing_song(singer_char, song, game_state)
        assert can_sing == True
        
        cost_modification = singer_ability.get_song_cost_modification(singer_char, song, game_state)
        assert cost_modification == -5  # Should reduce cost to 0 (full song cost reduction)
        
        # Test with song that can't be sung
        expensive_song = create_test_song(cost=8, singer_cost=6)  # Requires Singer 6
        
        can_sing_expensive = singer_ability.allows_singing_song(singer_char, expensive_song, game_state)
        assert can_sing_expensive == False
        
        no_cost_mod = singer_ability.get_song_cost_modification(singer_char, expensive_song, game_state)
        assert no_cost_mod == 0  # No modification if can't sing
    
    def test_singer_delegation_methods_integration(self):
        """Test that Singer properly implements all delegation methods."""
        # Create Singer ability
        singer_ability = KeywordRegistry.create_keyword_ability('Singer', value=4)
        
        # Create characters
        singer_char = create_character_with_ability("Vocalist", singer_ability)
        normal_char = create_test_character("Normal")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([singer_char], [normal_char])
        
        # Test delegation methods that don't affect normal rules
        assert singer_ability.allows_being_challenged_by(normal_char, singer_char, game_state) == True
        assert singer_ability.allows_challenging(singer_char, normal_char, game_state) == True
        assert singer_ability.modifies_challenge_targets(singer_char, [normal_char], game_state) == [normal_char]
        assert singer_ability.allows_being_targeted_by(singer_char, normal_char, game_state) == True
        
        # Test song-specific delegation methods
        valid_song = create_test_song(cost=5, singer_cost=4)  # Singer can sing this
        invalid_song = create_test_song(cost=7, singer_cost=6)  # Singer cannot sing this
        
        # Valid song tests
        assert singer_ability.allows_singing_song(singer_char, valid_song, game_state) == True
        cost_reduction = singer_ability.get_song_cost_modification(singer_char, valid_song, game_state)
        assert cost_reduction == -5  # Full cost reduction for valid song
        
        # Invalid song tests
        assert singer_ability.allows_singing_song(singer_char, invalid_song, game_state) == False
        no_reduction = singer_ability.get_song_cost_modification(singer_char, invalid_song, game_state)
        assert no_reduction == 0  # No reduction for invalid song
        
        # Test core Singer functionality
        assert singer_ability.get_effective_sing_cost() == 4
        assert singer_ability.can_sing_song(valid_song) == True
        assert singer_ability.can_sing_song(invalid_song) == False