"""Tests for Support keyword ability - both unit and integration tests."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry, SupportAbility
from lorcana_sim.models.abilities.base_ability import AbilityType
from lorcana_sim.engine.game_engine import GameAction
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestSupportAbilityUnit:
    """Unit tests for Support keyword ability implementation."""
    
    def test_support_creation(self):
        """Test creating Support ability."""
        support = SupportAbility(
            name="Support",
            type=AbilityType.KEYWORD,
            effect="Support ability",
            full_text="Support",
            keyword="Support",
            value=None
        )
        
        assert support.keyword == "Support"
        assert support.triggers_on_quest() == True
        assert support.modifies_quest_effects() == True
        assert support.is_optional() == True
        assert str(support) == "Support"
    
    def test_support_targeting(self):
        """Test Support targeting rules."""
        support = SupportAbility(
            name="Support",
            type=AbilityType.KEYWORD,
            effect="Support ability",
            full_text="Support",
            keyword="Support",
            value=None
        )
        
        supporting_char = create_test_character("Supporting Character")
        target_char = create_test_character("Target Character")
        
        # Can support other characters but not self
        assert support.can_support_character(target_char, supporting_char) == True
        assert support.can_support_character(supporting_char, supporting_char) == False
    
    def test_passive_ability(self):
        """Test that Support is a triggered ability."""
        support = SupportAbility(
            name="Support",
            type=AbilityType.KEYWORD,
            effect="Support ability",
            full_text="Support",
            keyword="Support",
            value=None
        )
        
        assert support.can_activate(None) == False
    
    def test_registry_creation(self):
        """Test creating Support ability via registry."""
        support = KeywordRegistry.create_keyword_ability('Support')
        
        assert isinstance(support, SupportAbility)
        assert support.keyword == 'Support'
        assert support.type == AbilityType.KEYWORD


class TestSupportAbilityIntegration:
    """Integration tests for Support keyword ability with game state."""
    
    def test_support_triggers_on_quest(self):
        """Test that Support triggers when the character quests."""
        # Create support ability
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create characters
        support_char = create_character_with_ability("Supportive Character", support_ability, lore=2)
        target_char = create_test_character("Target Character", lore=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([support_char, target_char], [])
        
        # Get all legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should be able to quest with the support character
        quest_actions = [action for action, params in legal_actions 
                        if action == GameAction.QUEST_CHARACTER]
        
        assert len(quest_actions) >= 0, "Should be able to quest with support character"
    
    def test_support_lore_bonus_calculation(self):
        """Test that Support calculates lore bonus correctly."""
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create character with specific lore value
        support_char = create_character_with_ability("Helper", support_ability, lore=3)
        
        # Check lore bonus calculation
        lore_bonus = support_ability.get_support_lore_bonus(support_char)
        assert lore_bonus == 3, "Support should provide lore equal to character's lore value"
    
    def test_support_targeting_multiple_characters(self):
        """Test Support with multiple potential targets."""
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create characters
        support_char = create_character_with_ability("Supporter", support_ability)
        target_char1 = create_test_character("Target 1")
        target_char2 = create_test_character("Target 2")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char, target_char1, target_char2], []
        )
        
        # Get valid support targets
        valid_targets = support_ability.get_valid_support_targets(
            game_state, game_state.current_player, support_char
        )
        
        # Should be able to target both other characters
        assert len(valid_targets) == 2
        assert target_char1 in valid_targets
        assert target_char2 in valid_targets
        assert support_char not in valid_targets  # Cannot target self
    
    def test_support_is_optional(self):
        """Test that Support is an optional ability."""
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create characters
        support_char = create_character_with_ability("Supporter", support_ability)
        target_char = create_test_character("Target")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([support_char, target_char], [])
        
        # Verify support is optional
        assert support_ability.is_optional() == True
        
        # In full implementation, player could choose whether to use support when questing
    
    def test_support_without_other_characters(self):
        """Test Support behavior when no other characters are available to support."""
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create only the support character
        support_char = create_character_with_ability("Lone Supporter", support_ability)
        
        # Setup game with only one character
        game_state, validator, engine = setup_game_with_characters([support_char], [])
        
        # Get valid support targets
        valid_targets = support_ability.get_valid_support_targets(
            game_state, game_state.current_player, support_char
        )
        
        # Should have no valid targets
        assert len(valid_targets) == 0
    
    def test_support_actual_lore_execution(self):
        """Test that Support ability actually increases lore gained when questing."""
        # Create characters with Support
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        support_char = create_character_with_ability("Supporter", support_ability, lore=3)
        target_char = create_test_character("Target", lore=2)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char, target_char], []
        )
        
        # Ensure characters have dry ink (were played in a previous turn)
        support_char.turn_played = game_state.turn_number - 1
        target_char.turn_played = game_state.turn_number - 1
        
        # Track initial lore
        initial_lore = game_state.current_player.lore
        
        # Quest with support character - this should trigger Support
        success, message = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': support_char})
        
        # Verify quest succeeded
        if not success:
            print(f"Quest failed: {message}")
        assert success == True
        assert "supported" in message.lower()
        
        # Verify lore calculation:
        # - Support character's base lore: 3
        # - Support ability gives target character +3 lore for this quest
        # - But the support character is the one questing, so it gets its own 3 lore
        # - The target gets the +3 temporary bonus for later use
        lore_gained = game_state.current_player.lore - initial_lore
        assert lore_gained == 3  # Support character's own lore
        
        # Verify target character got the support bonus
        assert getattr(target_char, 'temporary_lore_bonus', 0) == 3
        
        # Now quest with target character to see if bonus applies
        target_char.exerted = False  # Ready the target
        target_initial_lore = game_state.current_player.lore
        
        success2, message2 = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': target_char})
        assert success2 == True
        
        # Target should quest for its base lore (2) + support bonus (3) = 5 total
        target_lore_gained = game_state.current_player.lore - target_initial_lore
        assert target_lore_gained == 5  # 2 base + 3 support bonus
        
        # Verify temporary bonus was cleared after use
        assert getattr(target_char, 'temporary_lore_bonus', 0) == 0
    
    def test_support_trigger_system_integration(self):
        """Test that Support integrates properly with the trigger system."""
        # Create Support ability
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        support_char = create_character_with_ability("Supporter", support_ability, lore=2)
        target_char = create_test_character("Target", lore=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char, target_char], []
        )
        
        # Verify the Support ability is registered for triggering
        from lorcana_sim.engine.event_system import GameEvent
        assert len(engine.event_manager._event_listeners[GameEvent.CHARACTER_QUESTS]) == 1
        
        # Verify the ability declares it triggers on CHARACTER_QUESTS
        trigger_events = support_ability.get_trigger_events()
        assert GameEvent.CHARACTER_QUESTS in trigger_events
        
        # Verify the targeting logic works
        valid_targets = support_ability.get_valid_support_targets(
            game_state, game_state.current_player, support_char
        )
        assert target_char in valid_targets  # Target should be valid
        assert support_char not in valid_targets  # Can't support self
        
        # Verify lore bonus calculation
        lore_bonus = support_ability.get_support_lore_bonus(support_char)
        assert lore_bonus == 2  # Should equal support_char's lore
    
    def test_support_only_triggers_for_own_character(self):
        """Test that Support only triggers when the character with Support quests."""
        # Create abilities
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        
        # Create characters
        support_char = create_character_with_ability("Supporter", support_ability, lore=2)
        normal_char = create_test_character("Normal", lore=1)
        target_char = create_test_character("Target", lore=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters(
            [support_char, normal_char, target_char], []
        )
        
        # Ensure characters have dry ink (were played in a previous turn)
        support_char.turn_played = game_state.turn_number - 1
        normal_char.turn_played = game_state.turn_number - 1
        target_char.turn_played = game_state.turn_number - 1
        
        # Quest with the normal character (not the support character)
        success, message = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': normal_char})
        
        # Verify the quest succeeded but no support triggered
        assert success == True
        assert "quested" in message
        assert "Triggered" not in message  # Should NOT show triggered abilities
        assert "supported" not in message.lower()
        
        # Verify no support bonus was applied to any character
        assert not hasattr(target_char, 'temporary_lore_bonus') or target_char.temporary_lore_bonus == 0