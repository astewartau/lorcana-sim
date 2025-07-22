"""Integration tests for MY ORDERS COME FROM JAFAR - When you play this character, if you have a character named Jafar in play, you may banish chosen item."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.item_card import ItemCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, ChoiceMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.my_orders_come_from_jafar import create_my_orders_come_from_jafar


class TestMyOrdersComeFromJafarIntegration(GameEngineTestBase):
    """Integration tests for MY ORDERS COME FROM JAFAR named ability."""
    
    def create_jafar_orders_character(self, name="Orders Character", cost=3, strength=2, willpower=3):
        """Create a test character with MY ORDERS COME FROM JAFAR ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            subtypes=["Ally"]
        )
        
        # Add the MY ORDERS COME FROM JAFAR ability
        ability_data = {"name": "MY ORDERS COME FROM JAFAR", "type": "triggered"}
        jafar_orders_ability = create_my_orders_come_from_jafar(character, ability_data)
        character.composable_abilities = [jafar_orders_ability]
        
        return character
    
    def create_jafar_character(self, name="Jafar", cost=4, strength=3, willpower=4):
        """Create a Jafar character."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower,
            subtypes=["Villain"]
        )
        return character
    
    def create_test_item(self, name="Test Item", cost=2):
        """Create a test item card."""
        item = ItemCard(
            id=len(self.player1.deck) + len(self.player2.deck) + 200,
            name=name,
            version=None,
            full_name=name,
            cost=cost,
            color=CardColor.AMETHYST,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=2,
            story=""
        )
        return item
    
    def test_jafar_orders_creation(self):
        """Unit test: Verify MY ORDERS COME FROM JAFAR ability creates correctly."""
        character = self.create_jafar_orders_character()
        
        assert len(character.composable_abilities) == 1
        ability = character.composable_abilities[0]
        assert "MY ORDERS COME FROM JAFAR" in ability.name
    
    def test_jafar_orders_triggers_with_jafar_in_play(self):
        """Integration test: Ability triggers when Jafar is in play and allows item banishment."""
        # Create Jafar character
        jafar_character = self.create_test_character(
            name="Jafar",
            cost=5,
            strength=4,
            willpower=4
        )
        
        # Create character with MY ORDERS COME FROM JAFAR ability
        orders_character = self.create_jafar_orders_character(
            name="Orders Character", 
            cost=3
        )
        
        # Create item cards to target
        enemy_item = self.create_test_item(name="Enemy Item", cost=2)
        friendly_item = self.create_test_item(name="Friendly Item", cost=1)
        
        # Set up game state - Jafar is already in play
        self.player1.characters_in_play = [jafar_character]
        self.player1.hand = [orders_character]
        self.player1.items_in_play = [friendly_item]
        self.player2.items_in_play = [enemy_item]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        jafar_character.controller = self.player1
        orders_character.controller = self.player1
        friendly_item.controller = self.player1
        enemy_item.controller = self.player2
        
        # Record initial item states
        assert enemy_item in self.player2.items_in_play
        assert friendly_item in self.player1.items_in_play
        
        # Play the orders character
        play_move = PlayMove(orders_character)
        message = self.game_engine.next_message(play_move)
        
        # Verify the character was played
        assert message.type == MessageType.STEP_EXECUTED
        # Verify character was played
        assert message.type == MessageType.STEP_EXECUTED
        assert orders_character in self.player1.characters_in_play
        
        # Get the ability trigger message
        trigger_message = self.game_engine.next_message()
        assert trigger_message.type == MessageType.STEP_EXECUTED
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Should get a choice message for which item to banish
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        # Verify choice message
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        # Choose to banish the enemy item
        selected_option = choice_message.choice.options[0].id  # Assume enemy item is first choice
        banish_choice = ChoiceMove(choice_id=choice_message.choice.choice_id, option=selected_option)
        choice_result = self.game_engine.next_message(banish_choice)
        
        # Get the banish effect message
        effect_message = self.game_engine.next_message()
        assert effect_message.type == MessageType.STEP_EXECUTED
        # Verify effect message
        assert effect_message.type == MessageType.STEP_EXECUTED
        
        # Verify the chosen item was banished
        # The exact verification depends on implementation - item should be removed from play
        assert enemy_item not in self.player2.items_in_play
        # Friendly item should remain unchanged
        assert friendly_item in self.player1.items_in_play
    
    def test_jafar_orders_does_not_trigger_without_jafar(self):
        """Test that ability does not trigger when no Jafar is in play."""
        # Create character with MY ORDERS COME FROM JAFAR ability
        orders_character = self.create_jafar_orders_character(
            name="Orders Character"
        )
        
        # Create item to potentially target
        enemy_item = self.create_test_item(name="Enemy Item")
        
        # Set up game state WITHOUT Jafar in play
        self.player1.hand = [orders_character]
        self.player1.characters_in_play = []  # No Jafar
        self.player2.items_in_play = [enemy_item]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        orders_character.controller = self.player1
        enemy_item.controller = self.player2
        
        # Record initial item state
        assert enemy_item in self.player2.items_in_play
        
        # Play the orders character
        play_move = PlayMove(orders_character)
        message = self.game_engine.next_message(play_move)
        
        # Verify character was played
        assert orders_character in self.player1.characters_in_play
        
        # Get trigger message
        trigger_message = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Should NOT get a choice message since Jafar requirement is not met
        # The ability should fizzle or indicate no valid effect
        # Enemy item should remain in play
        assert enemy_item in self.player2.items_in_play
    
    def test_jafar_orders_with_no_items_in_play(self):
        """Test ability when Jafar is present but no items are in play."""
        # Create Jafar character
        jafar_character = self.create_test_character(name="Jafar")
        
        # Create character with ability
        orders_character = self.create_jafar_orders_character(
            name="Orders Character"
        )
        
        # Set up game state with Jafar but no items
        self.player1.characters_in_play = [jafar_character]
        self.player1.hand = [orders_character]
        self.player1.items_in_play = []
        self.player2.items_in_play = []
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        jafar_character.controller = self.player1
        orders_character.controller = self.player1
        
        # Play the orders character
        play_move = PlayMove(orders_character)
        message = self.game_engine.next_message(play_move)
        
        # Get trigger message
        trigger_message = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Should either get a message indicating no valid targets,
        # or the ability should have no effect since no items exist
    
    def test_jafar_orders_player_chooses_not_to_banish(self):
        """Test ability when player chooses not to banish an item."""
        # Create Jafar and orders characters
        jafar_character = self.create_test_character(name="Jafar")
        orders_character = self.create_jafar_orders_character(
            name="Orders Character"
        )
        
        # Create item to potentially banish
        enemy_item = self.create_test_item(name="Enemy Item")
        
        # Set up game state
        self.player1.characters_in_play = [jafar_character]
        self.player1.hand = [orders_character]
        self.player2.items_in_play = [enemy_item]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        jafar_character.controller = self.player1
        orders_character.controller = self.player1
        enemy_item.controller = self.player2
        
        # Play the orders character
        play_move = PlayMove(orders_character)
        message = self.game_engine.next_message(play_move)
        
        # Get trigger and choice messages
        trigger_message = self.game_engine.next_message()
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        # Choose NOT to banish (assuming there's a "decline" option)
        # Find the "No" option - it's usually the last one
        decline_option = choice_message.choice.options[-1].id  # Or whatever represents "no"
        decline_choice = ChoiceMove(choice_id=choice_message.choice.choice_id, option=decline_option)
        choice_result = self.game_engine.next_message(decline_choice)
        
        # Item should remain in play
        assert enemy_item in self.player2.items_in_play
    
    def test_jafar_orders_with_multiple_jafars(self):
        """Test ability when multiple Jafar characters are in play."""
        # Create multiple Jafar characters
        jafar1 = self.create_test_character(name="Jafar", cost=4)
        jafar2 = self.create_test_character(name="Jafar", cost=6)
        
        # Create character with ability
        orders_character = self.create_jafar_orders_character(
            name="Orders Character"
        )
        
        # Create item to banish
        enemy_item = self.create_test_item(name="Enemy Item")
        
        # Set up game state
        self.player1.characters_in_play = [jafar1, jafar2]
        self.player1.hand = [orders_character]
        self.player2.items_in_play = [enemy_item]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        jafar1.controller = self.player1
        jafar2.controller = self.player1
        orders_character.controller = self.player1
        enemy_item.controller = self.player2
        
        # Play the orders character
        play_move = PlayMove(orders_character)
        message = self.game_engine.next_message(play_move)
        
        # Get trigger message
        trigger_message = self.game_engine.next_message()
        # Check that message has event data about the ability trigger
        assert trigger_message.event_data is not None or trigger_message.step is not None
        
        # Should still be able to banish item since at least one Jafar is present
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        selected_option = choice_message.choice.options[0].id
        banish_choice = ChoiceMove(choice_id=choice_message.choice.choice_id, option=selected_option)
        choice_result = self.game_engine.next_message(banish_choice)
        
        effect_message = self.game_engine.next_message()
        # Verify effect message
        assert effect_message.type == MessageType.STEP_EXECUTED
    
    def test_jafar_orders_with_mixed_item_ownership(self):
        """Test ability with both friendly and enemy items in play."""
        # Create Jafar and orders characters
        jafar_character = self.create_test_character(name="Jafar")
        orders_character = self.create_jafar_orders_character(
            name="Orders Character"
        )
        
        # Create items owned by both players
        friendly_item1 = self.create_test_item(name="Friendly Item 1")
        friendly_item2 = self.create_test_item(name="Friendly Item 2")
        enemy_item1 = self.create_test_item(name="Enemy Item 1")
        enemy_item2 = self.create_test_item(name="Enemy Item 2")
        
        # Set up game state
        self.player1.characters_in_play = [jafar_character]
        self.player1.hand = [orders_character]
        self.player1.items_in_play = [friendly_item1, friendly_item2]
        self.player2.items_in_play = [enemy_item1, enemy_item2]
        self.setup_player_ink(self.player1, ink_count=5)
        
        # Set controllers
        jafar_character.controller = self.player1
        orders_character.controller = self.player1
        friendly_item1.controller = self.player1
        friendly_item2.controller = self.player1
        enemy_item1.controller = self.player2
        enemy_item2.controller = self.player2
        
        # Play the orders character
        play_move = PlayMove(orders_character)
        message = self.game_engine.next_message(play_move)
        
        # Get trigger and choice messages
        trigger_message = self.game_engine.next_message()
        choice_message = self.game_engine.next_message()
        assert choice_message.type == MessageType.CHOICE_REQUIRED
        
        # Choose to banish one of the enemy items
        selected_option = choice_message.choice.options[2].id  # Assuming enemy items come after friendly
        banish_choice = ChoiceMove(choice_id=choice_message.choice.choice_id, option=selected_option)
        choice_result = self.game_engine.next_message(banish_choice)
        
        effect_message = self.game_engine.next_message()
        
        # Verify only the chosen item was banished
        # Exact verification depends on which item was chosen
        total_items_remaining = len(self.player1.items_in_play) + len(self.player2.items_in_play)
        assert total_items_remaining == 3  # Started with 4, banished 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])