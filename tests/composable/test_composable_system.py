"""Comprehensive tests for the composable ability system."""

import pytest
from unittest.mock import Mock, MagicMock

from lorcana_sim.models.abilities.composable import *
from lorcana_sim.models.abilities.composable.keyword_abilities import *
from lorcana_sim.engine.event_system import GameEvent, EventContext


class MockCharacter:
    """Mock character for testing."""
    
    def __init__(self, name="Test Character", controller=None):
        self.name = name
        self.controller = controller
        self.lore = 0
        self.strength = 0
        self.willpower = 0
        self.damage = 0
        self.exerted = False
        self.abilities = []
        self.metadata = {}
        
        # Track bonuses for testing
        self.lore_bonuses = []
        self.strength_bonuses = []
        self.willpower_bonuses = []
    
    def add_lore_bonus(self, amount, duration):
        self.lore_bonuses.append((amount, duration))
        if duration == "permanent":
            self.lore += amount
    
    def add_strength_bonus(self, amount, duration):
        self.strength_bonuses.append((amount, duration))
        if duration == "permanent":
            self.strength += amount
    
    def add_willpower_bonus(self, amount, duration):
        self.willpower_bonuses.append((amount, duration))
        if duration == "permanent":
            self.willpower += amount
    
    def modify_damage(self, amount):
        self.damage += amount
    
    def heal_damage(self, amount):
        self.damage = max(0, self.damage - amount)
    
    def __str__(self):
        return self.name


class MockGameState:
    """Mock game state for testing."""
    
    def __init__(self, players=None):
        self.all_players = players or []
        self.current_player = players[0] if players else None
        self.opponent = players[1] if len(players) > 1 else None


class MockPlayer:
    """Mock player for testing."""
    
    def __init__(self, characters=None):
        self.characters_in_play = characters or []
        
    def draw_cards(self, count):
        pass


# =============================================================================
# EFFECT SYSTEM TESTS
# =============================================================================

class TestEffectSystem:
    """Test the core effect system."""
    
    def test_stat_modification(self):
        """Test basic stat modification."""
        character = MockCharacter()
        effect = StatModification("lore", 2, "this_turn")
        
        effect.apply(character, {})
        
        assert character.lore_bonuses == [(2, "this_turn")]
    
    def test_effect_addition(self):
        """Test combining effects with +"""
        character = MockCharacter()
        effect1 = StatModification("lore", 2, "this_turn")
        effect2 = StatModification("strength", 1, "permanent")
        
        combined = effect1 + effect2
        combined.apply(character, {})
        
        assert character.lore_bonuses == [(2, "this_turn")]
        assert character.strength_bonuses == [(1, "permanent")]
    
    def test_effect_multiplication(self):
        """Test repeating effects with *"""
        character = MockCharacter()
        effect = StatModification("lore", 1, "permanent")
        
        repeated = effect * 3
        repeated.apply(character, {})
        
        assert character.lore == 3
    
    def test_effect_choice(self):
        """Test choice effects with |"""
        character = MockCharacter()
        effect1 = StatModification("lore", 2, "permanent")
        effect2 = StatModification("strength", 3, "permanent")
        
        choice = effect1 | effect2
        choice.apply(character, {})
        
        # Should apply first effect (for now)
        assert character.lore == 2
        assert character.strength == 0
    
    def test_conditional_effect(self):
        """Test conditional effects."""
        character = MockCharacter()
        character.cost = 5
        
        condition = lambda target, ctx: getattr(target, 'cost', 0) >= 5
        effect = ConditionalEffect(
            condition=condition,
            effect=StatModification("lore", 3, "permanent"),
            else_effect=StatModification("lore", 1, "permanent")
        )
        
        effect.apply(character, {})
        assert character.lore == 3
        
        # Test else branch
        low_cost_char = MockCharacter()
        low_cost_char.cost = 2
        effect.apply(low_cost_char, {})
        assert low_cost_char.lore == 1


# =============================================================================
# TARGET SELECTOR TESTS
# =============================================================================

class TestTargetSelectors:
    """Test the target selection system."""
    
    def test_character_selector(self):
        """Test basic character selection."""
        char1 = MockCharacter("Char1")
        char2 = MockCharacter("Char2") 
        player = MockPlayer([char1, char2])
        game_state = MockGameState([player])
        
        selector = CharacterSelector(lambda c, ctx: c.name == "Char1")
        targets = selector.select({'game_state': game_state})
        
        assert len(targets) == 1
        assert targets[0] == char1
    
    def test_selector_intersection(self):
        """Test selector intersection with &"""
        char1 = MockCharacter("Char1")
        char1.exerted = False
        char1.damage = 1
        
        char2 = MockCharacter("Char2")
        char2.exerted = True
        char2.damage = 1
        
        player = MockPlayer([char1, char2])
        game_state = MockGameState([player])
        context = {'game_state': game_state}
        
        ready_selector = CharacterSelector(ready_filter, count=99)
        damaged_selector = CharacterSelector(damaged_filter, count=99)
        
        combined = ready_selector & damaged_selector
        targets = combined.select(context)
        
        # Should only get char1 (ready AND damaged)
        assert len(targets) == 1
        assert targets[0] == char1
    
    def test_selector_difference(self):
        """Test selector difference with -"""
        char1 = MockCharacter("Char1")
        char1.exerted = False
        
        char2 = MockCharacter("Char2")
        char2.exerted = True
        
        player = MockPlayer([char1, char2])
        game_state = MockGameState([player])
        context = {'game_state': game_state}
        
        all_selector = CharacterSelector(lambda c, ctx: True, count=99)
        exerted_selector = CharacterSelector(exerted_filter, count=99)
        
        ready_only = all_selector - exerted_selector
        targets = ready_only.select(context)
        
        # Should only get char1 (all characters minus exerted ones)
        assert len(targets) == 1
        assert targets[0] == char1


# =============================================================================
# COMPOSABLE ABILITY TESTS
# =============================================================================

class TestComposableAbilities:
    """Test complete composable abilities."""
    
    def test_simple_support_ability(self):
        """Test creating a Support-like ability."""
        character = MockCharacter("Support Character")
        target_char = MockCharacter("Target Character")
        target_char.controller = character.controller = Mock()
        
        support = quick_ability(
            name="Support 2",
            character=character,
            trigger_condition=when_quests(character),
            target_selector=OTHER_FRIENDLY,
            effect=StatModification("lore", 2, "this_turn")
        )
        
        # Create event context
        player = MockPlayer([character, target_char])
        game_state = MockGameState([player])
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=character,
            game_state=game_state,
            additional_data={}
        )
        
        # Execute
        support.handle_event(event)
        
        # Verify
        assert len(target_char.lore_bonuses) == 1
        assert target_char.lore_bonuses[0] == (2, "this_turn")
    
    def test_fluent_interface(self):
        """Test the fluent interface for building abilities."""
        character = MockCharacter("Test Character")
        
        test_ability = (ability("Multi Ability")
                  .for_character(character)
                  .when(when_quests(character))
                  .target(SELF)
                  .apply(LORE_PLUS_1)
                  .when(when_enters_play(character))
                  .target(OTHER_FRIENDLY)
                  .apply(STRENGTH_PLUS_2)
                  .build())
        
        assert test_ability.name == "Multi Ability"
        assert test_ability.character == character
        assert len(test_ability.listeners) == 2
    
    def test_multiple_effects_same_trigger(self):
        """Test ability with multiple effects on same trigger."""
        character = MockCharacter("Rally Character")
        target_char = MockCharacter("Target Character")
        target_char.controller = character.controller = Mock()
        
        rally = quick_ability(
            name="Rally",
            character=character,
            trigger_condition=when_enters_play(character),
            target_selector=OTHER_FRIENDLY,
            effect=LORE_PLUS_1 + STRENGTH_PLUS_2
        )
        
        # Mock target to track both bonuses
        target_char.strength_bonuses = []
        target_char.add_strength_bonus = lambda amount, duration: target_char.strength_bonuses.append((amount, duration))
        
        # Setup and execute
        player = MockPlayer([character, target_char])
        game_state = MockGameState([player])
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            game_state=game_state,
            additional_data={}
        )
        
        rally.handle_event(event)
        
        # Verify both effects applied
        assert target_char.lore_bonuses == [(1, "this_turn")]
        assert target_char.strength_bonuses == [(2, "this_turn")]


# =============================================================================
# KEYWORD ABILITY TESTS
# =============================================================================

class TestKeywordAbilities:
    """Test all composable keyword abilities."""
    
    def test_resist_ability(self):
        """Test Resist ability."""
        character = MockCharacter("Resist Character")
        resist = create_resist_ability(2, character)
        
        # Create damage event
        event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            additional_data={'damage': 5}
        )
        
        resist.handle_event(event)
        
        # Damage should be reduced
        assert event.additional_data['damage'] == 3  # 5 - 2
    
    def test_ward_ability(self):
        """Test Ward ability."""
        character = MockCharacter("Ward Character")
        ward = create_ward_ability(character)
        
        # Create targeting event - Ward needs a specific targeting attempt event
        # Since we don't have a specific targeting event type, simulate it
        # by using an event that has targeting_attempt in additional_data
        event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,  # Placeholder for targeting
            target=character,
            additional_data={'targeting_attempt': True}
        )
        
        ward.handle_event(event)
        
        # Should be prevented
        assert event.additional_data.get('prevented', False)
    
    def test_support_ability(self):
        """Test Support ability."""
        character = MockCharacter("Support Character")
        target_char = MockCharacter("Target Character")
        target_char.controller = character.controller = Mock()
        
        support = create_support_ability(3, character)
        
        player = MockPlayer([character, target_char])
        game_state = MockGameState([player])
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=target_char,  # target_char quests, gets bonus from character (support)
            game_state=game_state,
            additional_data={}
        )
        
        support.handle_event(event)
        
        assert target_char.lore_bonuses == [(3, "this_turn")]
    
    def test_singer_ability(self):
        """Test Singer ability."""
        character = MockCharacter("Singer Character")
        singer = create_singer_ability(5, character)
        
        event = EventContext(
            event_type=GameEvent.SONG_SUNG,
            source=character,
            additional_data={'singer': character, 'required_cost': 4}
        )
        
        singer.handle_event(event)
        
        assert event.additional_data['can_sing'] == True
        assert event.additional_data['singer_cost'] == 5
    
    def test_rush_ability(self):
        """Test Rush ability."""
        character = MockCharacter("Rush Character")
        rush = create_rush_ability(character)
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        rush.handle_event(event)
        
        assert character.metadata['can_challenge_with_wet_ink'] == True
    
    def test_keyword_registry_compatibility(self):
        """Test that we can create all keyword abilities."""
        character = MockCharacter("Test Character")
        
        keywords = ['Resist', 'Ward', 'Bodyguard', 'Evasive', 'Singer', 'Support', 'Rush']
        
        for keyword in keywords:
            ability = create_keyword_ability(keyword, character, 2)
            assert ability.name.startswith(keyword)
            assert ability.character == character


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Test integration between different parts of the system."""
    
    def test_complex_ability_interaction(self):
        """Test complex interactions between multiple abilities."""
        resist_char = MockCharacter("Resist Character")
        resist_ability = create_resist_ability(2, resist_char)
        
        support_char = MockCharacter("Support Character") 
        support_char.controller = resist_char.controller = Mock()
        support_ability = create_support_ability(1, support_char)
        
        # Resist character quests, should get lore bonus from support character
        player = MockPlayer([resist_char, support_char])
        game_state = MockGameState([player])
        
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=resist_char,  # resist_char quests, gets bonus from support_char
            game_state=game_state,
            additional_data={}
        )
        
        support_ability.handle_event(quest_event)
        
        # Then resist character takes damage, should be reduced
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=resist_char,
            additional_data={'damage': 5}
        )
        
        resist_ability.handle_event(damage_event)
        
        # Verify both effects
        assert resist_char.lore_bonuses == [(1, "this_turn")]
        assert damage_event.additional_data['damage'] == 3
    
    def test_priority_ordering(self):
        """Test that effects execute in priority order."""
        character = MockCharacter("Test Character")
        
        ability = ComposableAbility("Priority Test", character)
        
        # Add effects with different priorities
        ability.add_trigger(
            when_enters_play(character),
            SELF,
            StatModification("lore", 1, "permanent"),
            priority=1,
            name="Low Priority"
        )
        
        ability.add_trigger(
            when_enters_play(character),
            SELF,
            StatModification("lore", 2, "permanent"), 
            priority=10,
            name="High Priority"
        )
        
        event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            additional_data={}
        )
        
        ability.handle_event(event)
        
        # High priority should execute first, so final lore should be 3
        assert character.lore == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])