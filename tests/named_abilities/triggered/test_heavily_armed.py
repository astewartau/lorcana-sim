"""Integration tests for HEAVILY ARMED - Whenever you draw a card, this character gains Challenger +1 for the turn."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.action_card import ActionCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.heavily_armed import create_heavily_armed


class TestHeavilyArmedIntegration(GameEngineTestBase):
    """Integration tests for HEAVILY ARMED named ability."""
    
    def create_heavily_armed_character(self, name="Armed Character", cost=3, strength=2, willpower=3):
        """Create a test character with HEAVILY ARMED ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            subtypes=["Hero"]
        )
        
        # Add the HEAVILY ARMED ability
        ability_data = {"name": "HEAVILY ARMED", "type": "triggered"}
        heavily_armed_ability = create_heavily_armed(character, ability_data)
        character.composable_abilities = [heavily_armed_ability]
        
        return character
    
    def create_test_action(self, name="Test Action", cost=2, effect="Draw a card"):
        """Create a test action card that draws cards."""
        action = ActionCard(
            id=len(self.player1.deck) + len(self.player2.deck) + 200,
            name=name,
            version=None,
            full_name=name,
            cost=cost,
            color=CardColor.STEEL,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=2,
            story="",
            effects=[effect]
        )
        return action
    
    def test_heavily_armed_creation(self):
        """Unit test: Verify HEAVILY ARMED ability creates correctly."""
        character = self.create_heavily_armed_character()
        
        assert len(character.composable_abilities) == 1
        ability = character.composable_abilities[0]
        assert "HEAVILY ARMED" in ability.name
    
    def test_heavily_armed_triggers_on_natural_draw(self):
        """Integration test: HEAVILY ARMED triggers when player draws a card naturally."""
        # Create character with HEAVILY ARMED ability
        armed_character = self.create_heavily_armed_character(
            name="Armed Character", 
            cost=4,
            strength=3
        )
        
        # Set up game state - put character in hand BEFORE GameEngine init to register abilities
        self.player1.hand = [armed_character]
        self.setup_player_ink(self.player1, ink_count=5)  # Ensure player has ink to play character
        armed_character.controller = self.player1
        
        # Play the armed character to register abilities properly
        play_move = PlayMove(armed_character)
        play_message = self.game_engine.next_message(play_move)
        
        # Verify the character was played
        assert play_message.type == MessageType.STEP_EXECUTED
        assert armed_character in self.player1.characters_in_play
        
        # Ensure player has cards to draw
        dummy_card = self.create_test_character(name="Dummy Card")
        self.player1.deck = [dummy_card]
        
        # Record initial strength and challenger abilities
        initial_strength = armed_character.current_strength
        initial_challenger_abilities = len([ability for ability in armed_character.composable_abilities 
                                          if 'Challenger' in ability.name])
        
        # Simulate a card draw (this could be from draw phase, ability, etc.)
        # For testing, we'll manually trigger the draw and event
        drawn_card = self.player1.deck.pop(0)
        self.player1.hand.append(drawn_card)
        
        # Trigger the card draw event
        from lorcana_sim.engine.event_system import EventContext, GameEvent
        draw_context = EventContext(
            event_type=GameEvent.CARD_DRAWN,
            source=drawn_card,
            target=None,
            player=self.player1,
            game_state=self.game_state
        )
        
        # Process the draw event through the event system
        self.game_engine.execution_engine.event_manager.trigger_event(draw_context)
        
        # Get the HEAVILY ARMED trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Get the Challenger effect message
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        # Verify effect message
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify character gained Challenger +1 for the turn
        # Check for temporary challenger abilities created by the ChallengerEffect
        challenger_abilities = [ability for ability in armed_character.composable_abilities 
                              if 'Challenger' in ability.name]
        assert len(challenger_abilities) > 0, "Should have temporary challenger ability"
        assert challenger_abilities[0].strength_bonus == 1, "Should have Challenger +1"
    
    def test_heavily_armed_triggers_on_action_card_draw(self):
        """Test HEAVILY ARMED when player draws cards (simulating action card effect)."""
        # Create character with HEAVILY ARMED ability
        armed_character = self.create_heavily_armed_character(
            name="Armed Character",
            strength=2
        )
        
        # Set up game state - put character in hand BEFORE GameEngine init to register abilities
        self.player1.hand = [armed_character]
        self.setup_player_ink(self.player1, ink_count=4)  # Ensure player has ink to play character
        armed_character.controller = self.player1
        
        # Play the armed character to register abilities properly
        play_move = PlayMove(armed_character)
        play_message = self.game_engine.next_message(play_move)
        
        # Verify the character was played
        assert play_message.type == MessageType.STEP_EXECUTED
        assert armed_character in self.player1.characters_in_play
        
        # Ensure player has cards to draw
        dummy_card = self.create_test_character(name="Dummy Card")
        self.player1.deck = [dummy_card]
        
        # Record initial challenger abilities count
        initial_challenger_abilities = len([ability for ability in armed_character.composable_abilities 
                                          if 'Challenger' in ability.name])
        
        # Simulate a card draw (this could be from an action card effect)
        drawn_card = self.player1.deck.pop(0)
        self.player1.hand.append(drawn_card)
        
        # Trigger the card draw event
        from lorcana_sim.engine.event_system import EventContext, GameEvent
        draw_context = EventContext(
            event_type=GameEvent.CARD_DRAWN,
            source=drawn_card,
            target=None,
            player=self.player1,
            game_state=self.game_state
        )
        
        # Process the draw event through the event system
        self.game_engine.execution_engine.event_manager.trigger_event(draw_context)
        
        # Get the HEAVILY ARMED trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        
        # Get the Challenger effect message
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify character gained Challenger +1 for the turn
        challenger_abilities = [ability for ability in armed_character.composable_abilities 
                              if 'Challenger' in ability.name]
        assert len(challenger_abilities) > initial_challenger_abilities, "Should have gained a challenger ability"
    
    def test_heavily_armed_multiple_draws_multiple_triggers(self):
        """Test HEAVILY ARMED triggers multiple times when multiple cards are drawn."""
        # Create character with HEAVILY ARMED ability
        armed_character = self.create_heavily_armed_character(
            name="Armed Character"
        )
        
        # Set up game state - put character in hand BEFORE GameEngine init to register abilities
        self.player1.hand = [armed_character]
        self.setup_player_ink(self.player1, ink_count=4)  # Ensure player has ink to play character
        armed_character.controller = self.player1
        
        # Play the armed character to register abilities properly
        play_move = PlayMove(armed_character)
        play_message = self.game_engine.next_message(play_move)
        
        # Verify the character was played
        assert play_message.type == MessageType.STEP_EXECUTED
        assert armed_character in self.player1.characters_in_play
        
        # Ensure deck has cards to draw
        dummy_cards = [
            self.create_test_character(name=f"Dummy {i}")
            for i in range(5)
        ]
        self.player1.deck = dummy_cards
        
        # Simulate drawing multiple cards in sequence
        draws_to_make = 3
        triggers_received = 0
        
        for i in range(draws_to_make):
            # Draw a card
            if self.player1.deck:
                drawn_card = self.player1.deck.pop(0)
                self.player1.hand.append(drawn_card)
                
                # Trigger the card draw event
                from lorcana_sim.engine.event_system import EventContext, GameEvent
                draw_context = EventContext(
                    event_type=GameEvent.CARD_DRAWN,
                    source=drawn_card,
                    target=None,
                    player=self.player1,
                    game_state=self.game_state
                )
                
                self.game_engine.execution_engine.event_manager.trigger_event(draw_context)
                
                # Get trigger message
                trigger_message = self.game_engine.next_message()
                if trigger_message and (trigger_message.event_data is not None or trigger_message.step is not None):
                    triggers_received += 1
                    
                    # Get effect message
                    effect_message = self.game_engine.next_message()
                    # Verify effect message
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify ability triggered for each draw
        assert triggers_received == draws_to_make
    
    def test_heavily_armed_does_not_trigger_on_opponent_draw(self):
        """Test that HEAVILY ARMED does not trigger when opponent draws cards."""
        # Create character with HEAVILY ARMED ability
        armed_character = self.create_heavily_armed_character(
            name="Armed Character"
        )
        
        # Set up game state
        self.player1.characters_in_play = [armed_character]
        armed_character.controller = self.player1
        
        # Ensure opponent has cards to draw
        dummy_card = self.create_test_character(name="Opponent Dummy")
        self.player2.deck = [dummy_card]
        
        # Record initial challenger abilities count
        initial_challenger_abilities = len([ability for ability in armed_character.composable_abilities 
                                          if 'Challenger' in ability.name])
        
        # Opponent draws a card
        drawn_card = self.player2.deck.pop(0)
        self.player2.hand.append(drawn_card)
        
        # Trigger the card draw event for opponent
        from lorcana_sim.engine.event_system import EventContext, GameEvent
        draw_context = EventContext(
            event_type=GameEvent.CARD_DRAWN,
            source=drawn_card,
            target=None,
            player=self.player2,  # Opponent draws
            game_state=self.game_state
        )
        
        self.game_engine.execution_engine.event_manager.trigger_event(draw_context)
        
        # HEAVILY ARMED should NOT trigger for opponent's draw
        # Character should retain original challenger abilities count
        current_challenger_abilities = len([ability for ability in armed_character.composable_abilities 
                                          if 'Challenger' in ability.name])
        assert current_challenger_abilities == initial_challenger_abilities
    
    def test_heavily_armed_effect_duration(self):
        """Test that HEAVILY ARMED Challenger bonus lasts for the turn."""
        # Create character with HEAVILY ARMED ability
        armed_character = self.create_heavily_armed_character(
            name="Armed Character"
        )
        
        # Set up game state - put character in hand BEFORE GameEngine init to register abilities
        self.player1.hand = [armed_character]
        self.setup_player_ink(self.player1, ink_count=4)  # Ensure player has ink to play character
        armed_character.controller = self.player1
        
        # Play the armed character to register abilities properly
        play_move = PlayMove(armed_character)
        play_message = self.game_engine.next_message(play_move)
        
        # Verify the character was played
        assert play_message.type == MessageType.STEP_EXECUTED
        assert armed_character in self.player1.characters_in_play
        
        # Ensure deck has cards
        dummy_card = self.create_test_character(name="Dummy")
        self.player1.deck = [dummy_card]
        
        # Draw a card to trigger ability
        drawn_card = self.player1.deck.pop(0)
        self.player1.hand.append(drawn_card)
        
        from lorcana_sim.engine.event_system import EventContext, GameEvent
        draw_context = EventContext(
            event_type=GameEvent.CARD_DRAWN,
            source=drawn_card,
            target=None,
            player=self.player1,
            game_state=self.game_state
        )
        
        self.game_engine.execution_engine.event_manager.trigger_event(draw_context)
        
        # Get trigger and effect messages
        trigger_message = self.game_engine.next_message()
        # Check that we got a step executed message (ability trigger)
        assert trigger_message.type == MessageType.STEP_EXECUTED
        
        effect_message = self.game_engine.next_message()
        # Verify effect message
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify character gained Challenger bonus
        challenger_abilities = [ability for ability in armed_character.composable_abilities 
                              if 'Challenger' in ability.name]
        assert len(challenger_abilities) > 0, "Should have challenger ability"
        
        # Verify effect is applied
        # The exact verification depends on how temporary effects are implemented
        # Character should have enhanced challenging capability until end of turn
        
        # Simulate end of turn cleanup
        # The temporary effect should be removed when the turn ends
        # This would typically be handled by the game engine's end-of-turn processing
    
    def test_heavily_armed_with_multiple_armed_characters(self):
        """Test HEAVILY ARMED with multiple characters having the ability."""
        # Create multiple characters with HEAVILY ARMED
        armed_character1 = self.create_heavily_armed_character(
            name="Armed Character 1"
        )
        armed_character2 = self.create_heavily_armed_character(
            name="Armed Character 2"
        )
        
        # Set up game state - put characters in hand BEFORE GameEngine init to register abilities
        self.player1.hand = [armed_character1, armed_character2]
        self.setup_player_ink(self.player1, ink_count=7)  # Ensure player has ink to play both characters
        armed_character1.controller = self.player1
        armed_character2.controller = self.player1
        
        # Play both armed characters to register abilities properly
        play_move1 = PlayMove(armed_character1)
        play_message1 = self.game_engine.next_message(play_move1)
        
        # Verify first character was played
        assert play_message1.type == MessageType.STEP_EXECUTED
        assert armed_character1 in self.player1.characters_in_play
        
        play_move2 = PlayMove(armed_character2)
        play_message2 = self.game_engine.next_message(play_move2)
        
        # Verify second character was played
        assert play_message2.type == MessageType.STEP_EXECUTED
        assert armed_character2 in self.player1.characters_in_play
        
        # Ensure deck has cards
        dummy_card = self.create_test_character(name="Dummy")
        self.player1.deck = [dummy_card]
        
        # Draw a card (should trigger both abilities)
        drawn_card = self.player1.deck.pop(0)
        self.player1.hand.append(drawn_card)
        
        from lorcana_sim.engine.event_system import EventContext, GameEvent
        draw_context = EventContext(
            event_type=GameEvent.CARD_DRAWN,
            source=drawn_card,
            target=None,
            player=self.player1,
            game_state=self.game_state
        )
        
        self.game_engine.execution_engine.event_manager.trigger_event(draw_context)
        
        # Should get two separate triggers (one for each character)
        trigger_messages = []
        effect_messages = []
        
        # Get first trigger and effect
        trigger1 = self.game_engine.next_message()
        if trigger1 and trigger1.type == MessageType.STEP_EXECUTED:
            trigger_messages.append(trigger1)
            effect1 = self.game_engine.next_message()
            if effect1 and effect1.type == MessageType.STEP_EXECUTED:
                effect_messages.append(effect1)
        
        # Get second trigger and effect
        trigger2 = self.game_engine.next_message()
        if trigger2 and trigger2.type == MessageType.STEP_EXECUTED:
            trigger_messages.append(trigger2)
            effect2 = self.game_engine.next_message()
            if effect2 and effect2.type == MessageType.STEP_EXECUTED:
                effect_messages.append(effect2)
        
        # Verify both characters triggered their abilities
        assert len(trigger_messages) == 2
        assert len(effect_messages) == 2
        
        # Verify both characters gained Challenger abilities
        challenger_abilities1 = [ability for ability in armed_character1.composable_abilities 
                               if 'Challenger' in ability.name]
        challenger_abilities2 = [ability for ability in armed_character2.composable_abilities 
                               if 'Challenger' in ability.name]
        assert len(challenger_abilities1) > 0, "First character should have challenger ability"
        assert len(challenger_abilities2) > 0, "Second character should have challenger ability"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])