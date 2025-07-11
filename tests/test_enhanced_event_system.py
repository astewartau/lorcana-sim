"""Tests for the enhanced event system with all new events."""

import pytest
from lorcana_sim.engine.event_system import GameEvent, EventContext
from lorcana_sim.models.game.game_state import GameAction
from tests.helpers import (
    create_test_character, create_character_with_ability, create_test_song,
    setup_game_with_characters
)


class TestEnhancedEventSystem:
    """Test all the new events added to the event system."""
    
    def test_ink_played_event_triggered(self):
        """Test that INK_PLAYED event is triggered when playing ink."""
        char = create_test_character("Test Character", cost=2)
        ink_card = create_test_character("Ink Card", cost=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([], [])
        
        # Add cards to hand and set phase
        game_state.current_player.hand.extend([char, ink_card])
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.SET
        
        # Track events by creating a simple listener
        events_triggered = []
        original_trigger = engine.event_manager.trigger_event
        
        def track_events(event_context):
            events_triggered.append(event_context.event_type)
            return original_trigger(event_context)
        
        engine.event_manager.trigger_event = track_events
        
        # Play ink
        success, message = engine.execute_action(GameAction.PLAY_INK, {'card': ink_card})
        
        assert success == True
        assert GameEvent.INK_PLAYED in events_triggered
    
    def test_action_played_vs_song_sung_distinction(self):
        """Test that ACTION_PLAYED and SONG_SUNG are properly distinguished."""
        from lorcana_sim.abilities.keywords import KeywordRegistry
        from lorcana_sim.models.cards.action_card import ActionCard
        
        # Create singer and song
        singer_ability = KeywordRegistry.create_keyword_ability('Singer', value=4)
        singer = create_character_with_ability("Singer", singer_ability)
        song = create_test_song(cost=5, singer_cost=4, name="Test Song")
        
        # Also create a normal action (non-song)
        from lorcana_sim.models.abilities.base_ability import Ability, AbilityType
        from lorcana_sim.models.cards.base_card import CardColor, Rarity
        
        normal_ability = Ability(
            name="Normal Effect",
            type=AbilityType.STATIC,
            effect="Draw a card.",
            full_text="Draw a card."
        )
        
        normal_action = ActionCard(
            id=1, name="Normal Action", version="Test", full_name="Normal Action - Test",
            cost=3, color=CardColor.AMBER, inkwell=True, rarity=Rarity.COMMON, set_code="TEST",
            number=1, story="Test", abilities=[normal_ability]
        )
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([singer], [])
        
        # Ensure characters have dry ink
        singer.turn_played = game_state.turn_number - 1
        
        # Add cards to hand and give ink
        game_state.current_player.hand.extend([song, normal_action])
        for i in range(10):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        
        # Track events
        events_triggered = []
        original_trigger = engine.event_manager.trigger_event
        
        def track_events(event_context):
            events_triggered.append(event_context.event_type)
            return original_trigger(event_context)
        
        engine.event_manager.trigger_event = track_events
        
        # Test 1: Play normal action (should trigger ACTION_PLAYED only)
        events_triggered.clear()
        success, message = engine.execute_action(GameAction.PLAY_ACTION, {'card': normal_action})
        
        assert success == True
        assert GameEvent.ACTION_PLAYED in events_triggered
        assert GameEvent.SONG_PLAYED not in events_triggered
        assert GameEvent.SONG_SUNG not in events_triggered
        
        # Test 2: Play song normally (should trigger ACTION_PLAYED and SONG_PLAYED)
        events_triggered.clear()
        success, message = engine.execute_action(GameAction.PLAY_ACTION, {'card': song})
        
        assert success == True
        assert GameEvent.ACTION_PLAYED in events_triggered
        assert GameEvent.SONG_PLAYED in events_triggered
        assert GameEvent.SONG_SUNG not in events_triggered
        
        # Test 3: Sing song with Singer (should trigger SONG_SUNG only)
        game_state.current_player.hand.append(song)  # Add song back to hand
        events_triggered.clear()
        success, message = engine.execute_action(GameAction.SING_SONG, {
            'song': song, 'singer': singer
        })
        
        assert success == True
        assert GameEvent.SONG_SUNG in events_triggered
        assert GameEvent.ACTION_PLAYED not in events_triggered
        assert GameEvent.SONG_PLAYED not in events_triggered
    
    def test_turn_and_phase_events(self):
        """Test that turn and phase events are triggered correctly."""
        char1 = create_test_character("Character 1")
        char2 = create_test_character("Character 2")
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([char1], [char2])
        
        # Set to main phase
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        
        # Track events
        events_triggered = []
        original_trigger = engine.event_manager.trigger_event
        
        def track_events(event_context):
            events_triggered.append((event_context.event_type, getattr(event_context, 'additional_data', {})))
            return original_trigger(event_context)
        
        engine.event_manager.trigger_event = track_events
        
        # Pass turn (should trigger multiple events)
        success, message = engine.execute_action(GameAction.PASS_TURN, {})
        
        assert success == True
        
        # Check that the right events were triggered in order
        event_types = [event[0] for event in events_triggered]
        
        assert GameEvent.PHASE_ENDS in event_types  # End main phase
        assert GameEvent.TURN_ENDS in event_types   # End turn
        assert GameEvent.TURN_BEGINS in event_types # Begin new turn
        assert GameEvent.READY_STEP in event_types  # Ready step for new turn
    
    def test_character_enters_and_leaves_play_events(self):
        """Test CHARACTER_ENTERS_PLAY and CHARACTER_LEAVES_PLAY events."""
        char = create_test_character("Test Character", cost=2, willpower=1)
        attacker = create_test_character("Attacker", strength=3)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([], [attacker])
        
        # Add character to hand and give ink
        game_state.current_player.hand.append(char)
        for i in range(5):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        
        # Track events
        events_triggered = []
        original_trigger = engine.event_manager.trigger_event
        
        def track_events(event_context):
            events_triggered.append(event_context.event_type)
            return original_trigger(event_context)
        
        engine.event_manager.trigger_event = track_events
        
        # Test 1: Play character (should trigger enters play events)
        events_triggered.clear()
        success, message = engine.execute_action(GameAction.PLAY_CHARACTER, {'card': char})
        
        assert success == True
        assert GameEvent.CHARACTER_ENTERS_PLAY in events_triggered
        assert GameEvent.CHARACTER_PLAYED in events_triggered
        
        # Test 2: Banish character (should trigger leaves play events)
        # Switch to opponent and challenge to banish
        game_state.current_player_index = 1
        attacker.turn_played = game_state.turn_number - 1  # Make attacker able to challenge
        
        events_triggered.clear()
        success, message = engine.execute_action(GameAction.CHALLENGE_CHARACTER, {
            'attacker': attacker, 'defender': char
        })
        
        assert success == True
        assert GameEvent.CHARACTER_LEAVES_PLAY in events_triggered
        assert GameEvent.CHARACTER_BANISHED in events_triggered
    
    def test_lore_gained_event(self):
        """Test that LORE_GAINED event is triggered when questing."""
        char = create_test_character("Quester", lore=3)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([char], [])
        
        # Make character able to quest
        char.turn_played = game_state.turn_number - 1
        
        # Set to main phase
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        
        # Track events
        events_triggered = []
        lore_amounts = []
        original_trigger = engine.event_manager.trigger_event
        
        def track_events(event_context):
            events_triggered.append(event_context.event_type)
            if event_context.event_type == GameEvent.LORE_GAINED:
                lore_amounts.append(event_context.additional_data.get('lore_amount', 0))
            return original_trigger(event_context)
        
        engine.event_manager.trigger_event = track_events
        
        # Quest with character
        initial_lore = game_state.current_player.lore
        success, message = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': char})
        
        assert success == True
        assert GameEvent.CHARACTER_QUESTS in events_triggered
        assert GameEvent.LORE_GAINED in events_triggered
        assert len(lore_amounts) == 1
        assert lore_amounts[0] == 3  # Character's lore value
        assert game_state.current_player.lore == initial_lore + 3
    
    def test_item_played_event(self):
        """Test that ITEM_PLAYED event is triggered when playing items."""
        from lorcana_sim.models.cards.item_card import ItemCard
        
        item = ItemCard(
            id=1, name="Test Item", version="Test", full_name="Test Item - Test",
            cost=2, color="Amber", inkwell=True, rarity="Common", set_code="TEST",
            number=1, story="Test", abilities=[]
        )
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([], [])
        
        # Add item to hand and give ink
        game_state.current_player.hand.append(item)
        for i in range(5):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        
        # Track events
        events_triggered = []
        original_trigger = engine.event_manager.trigger_event
        
        def track_events(event_context):
            events_triggered.append(event_context.event_type)
            return original_trigger(event_context)
        
        engine.event_manager.trigger_event = track_events
        
        # Play item
        success, message = engine.execute_action(GameAction.PLAY_ITEM, {'card': item})
        
        assert success == True
        assert GameEvent.ITEM_PLAYED in events_triggered
    
    def test_multiple_events_in_single_action(self):
        """Test that complex actions trigger multiple events correctly."""
        from lorcana_sim.abilities.keywords import KeywordRegistry
        
        # Create character with Support to test event interaction
        support_ability = KeywordRegistry.create_keyword_ability('Support')
        support_char = create_character_with_ability("Supporter", support_ability, lore=2)
        quest_char = create_test_character("Quester", lore=1)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([support_char, quest_char], [])
        
        # Make characters able to quest
        support_char.turn_played = game_state.turn_number - 1
        quest_char.turn_played = game_state.turn_number - 1
        
        # Set to main phase
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        
        # Track events
        events_triggered = []
        original_trigger = engine.event_manager.trigger_event
        
        def track_events(event_context):
            events_triggered.append(event_context.event_type)
            return original_trigger(event_context)
        
        engine.event_manager.trigger_event = track_events
        
        # Quest with support character (should trigger multiple events)
        success, message = engine.execute_action(GameAction.QUEST_CHARACTER, {'character': support_char})
        
        assert success == True
        assert GameEvent.CHARACTER_QUESTS in events_triggered
        assert GameEvent.LORE_GAINED in events_triggered
        # Support ability should have modified the quest, causing additional events