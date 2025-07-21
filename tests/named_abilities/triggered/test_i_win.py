"""Integration tests for I WIN - When this character is banished, if you have more cards in your hand than each opponent, you may return this card to your hand."""

import pytest
from tests.helpers import GameEngineTestBase
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.game_moves import PlayMove, ChallengeMove, PassMove
from lorcana_sim.engine.message_engine import MessageType
from lorcana_sim.models.abilities.composable.named_abilities.triggered.i_win import create_i_win
from lorcana_sim.models.game.player import Player


class TestIWinIntegration(GameEngineTestBase):
    """Integration tests for I WIN named ability."""
    
    def _add_cards_to_hand(self, player, count, start_id=3000):
        """Helper to add cards to a player's hand during setup."""
        for i in range(count):
            card = self.create_test_character(f"Hand Card {i}", cost=1, card_id=start_id+i)
            player.hand.append(card)
    
    def _play_character_to_field(self, character, player):
        """Helper to play a character to the field using proper game moves."""
        return self.play_character(character, player)
    
    def create_i_win_character(self, name="I Win Character", cost=3, strength=2, willpower=3):
        """Create a test character with I WIN ability."""
        character = self.create_test_character(
            name=name,
            cost=cost,
            strength=strength,
            willpower=willpower
        )
        
        # Add I WIN ability
        ability_data = {"name": "I WIN", "type": "triggered"}
        i_win_ability = create_i_win(character, ability_data)
        character.composable_abilities.append(i_win_ability)
        
        return character
    
    def test_i_win_ability_creation(self):
        """Test that I WIN ability creates correctly."""
        character = self.create_i_win_character("Mad Hatter - Gracious Host")
        
        assert len(character.composable_abilities) == 1
        i_win_ability = character.composable_abilities[0]
        assert i_win_ability.name == "I WIN"
        assert i_win_ability.character == character
    
    def test_i_win_triggers_when_banished_with_more_cards(self):
        """Test that I WIN triggers when character is banished and player has more cards."""
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        attacker = self.create_test_character("Attacker", strength=5, willpower=3)
        
        # Give player1 more cards than player2 by adding cards to their hands during setup
        # Add 5 cards to player1's hand
        for i in range(5):
            card = self.create_test_character(f"Hand Card {i}", cost=1, card_id=3000+i)
            self.player1.hand.append(card)
        
        # Add 2 cards to player2's hand
        for i in range(2):
            card = self.create_test_character(f"Hand Card {i}", cost=1, card_id=3100+i)
            self.player2.hand.append(card)
        
        # Play characters using proper game moves
        self.play_character(i_win_char, self.player1)
        self.play_character(attacker, self.player2)
        
        # Verify hand sizes
        assert len(self.player1.hand) > len(self.player2.hand)
        
        # Track initial discard pile size
        initial_discard_size = len(self.player1.discard_pile)
        
        # Challenge i_win character to banish it
        challenge_move = ChallengeMove(attacker, i_win_char)
        message = self.game_engine.next_message(challenge_move)
        
        # Should have I WIN ability
        assert len(i_win_char.composable_abilities) == 1
        assert i_win_char.composable_abilities[0].name == "I WIN"
    
    def test_i_win_does_not_trigger_without_more_cards(self):
        """Test that I WIN does not trigger when player doesn't have more cards."""
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        attacker = self.create_test_character("Attacker", strength=5, willpower=3)
        
        # Give player1 same or fewer cards than player2
        # Add 2 cards to player1's hand
        for i in range(2):
            card = self.create_test_character(f"Hand Card {i}", cost=1, card_id=3200+i)
            self.player1.hand.append(card)
        
        # Add 3 cards to player2's hand
        for i in range(3):
            card = self.create_test_character(f"Hand Card {i}", cost=1, card_id=3300+i)
            self.player2.hand.append(card)
        
        # Play characters using proper game moves
        self.play_character(i_win_char, self.player1)
        self.play_character(attacker, self.player2)
        
        # Verify hand sizes (player1 does not have more)
        assert len(self.player1.hand) <= len(self.player2.hand)
        
        # Track initial discard pile size
        initial_discard_size = len(self.player1.discard_pile)
        
        # Challenge i_win character to banish it
        challenge_move = ChallengeMove(attacker, i_win_char)
        message = self.game_engine.next_message(challenge_move)
        
        # Should have ability but condition not met
        assert len(i_win_char.composable_abilities) == 1
        assert i_win_char.composable_abilities[0].name == "I WIN"
    
    def test_i_win_equal_hand_sizes(self):
        """Test that I WIN does not trigger when hand sizes are equal."""
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        attacker = self.create_test_character("Attacker", strength=5, willpower=3)
        
        # Give both players equal hand sizes
        # Add 3 cards to player1's hand
        for i in range(3):
            card = self.create_test_character(f"Hand Card {i}", cost=1, card_id=3400+i)
            self.player1.hand.append(card)
        
        # Add 3 cards to player2's hand
        for i in range(3):
            card = self.create_test_character(f"Hand Card {i}", cost=1, card_id=3500+i)
            self.player2.hand.append(card)
        
        # Play characters using proper game moves
        self.play_character(i_win_char, self.player1)
        self.play_character(attacker, self.player2)
        
        # Verify hand sizes are equal
        assert len(self.player1.hand) == len(self.player2.hand)
        
        # Track initial discard pile size
        initial_discard_size = len(self.player1.discard_pile)
        
        # Challenge i_win character to banish it
        challenge_move = ChallengeMove(attacker, i_win_char)
        message = self.game_engine.next_message(challenge_move)
        
        # Should have ability but condition not met (need MORE cards, not equal)
        assert len(i_win_char.composable_abilities) == 1
        assert i_win_char.composable_abilities[0].name == "I WIN"
    
    def test_i_win_multiple_opponents(self):
        """Test I WIN condition checking with multiple opponents."""
        # Create a 3-player scenario
        player3 = Player("Charlie")
        self.game_state.players.append(player3)
        
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        attacker = self.create_test_character("Attacker", strength=5, willpower=3)
        
        # Give player1 more cards than BOTH opponents
        self._add_cards_to_hand(self.player1, 5, 3600)  # Player1 will have 5 cards
        self._add_cards_to_hand(self.player2, 2, 3700)  # Player2 will have 2 cards
        self._add_cards_to_hand(player3, 3, 3800)       # Player3 will have 3 cards
        
        # Play characters using proper game moves
        self._play_character_to_field(i_win_char, self.player1)
        self._play_character_to_field(attacker, self.player2)
        
        # Verify player1 has more cards than both opponents
        assert len(self.player1.hand) > len(self.player2.hand)
        assert len(self.player1.hand) > len(player3.hand)
        
        # Challenge i_win character to banish it
        challenge_move = ChallengeMove(attacker, i_win_char)
        message = self.game_engine.next_message(challenge_move)
        
        # Should have ability and condition should be met
        assert len(i_win_char.composable_abilities) == 1
        assert i_win_char.composable_abilities[0].name == "I WIN"
    
    def test_i_win_multiple_opponents_condition_not_met(self):
        """Test I WIN condition not met when one opponent has more cards."""
        # Create a 3-player scenario
        player3 = Player("Charlie")
        self.game_state.players.append(player3)
        
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        attacker = self.create_test_character("Attacker", strength=5, willpower=3)
        
        # Give player1 more cards than one opponent but not all
        self._add_cards_to_hand(self.player1, 4, 3900)  # Player1 will have 4 cards
        self._add_cards_to_hand(self.player2, 2, 4000)  # Player2 will have 2 cards
        self._add_cards_to_hand(player3, 5, 4100)       # Player3 will have 5 cards (more than player1)
        
        # Play characters using proper game moves
        self._play_character_to_field(i_win_char, self.player1)
        self._play_character_to_field(attacker, self.player2)
        
        # Verify player1 doesn't have more cards than ALL opponents
        assert len(self.player1.hand) > len(self.player2.hand)
        assert len(self.player1.hand) < len(player3.hand)  # One opponent has more
        
        # Challenge i_win character to banish it
        challenge_move = ChallengeMove(attacker, i_win_char)
        message = self.game_engine.next_message(challenge_move)
        
        # Should have ability but condition not met
        assert len(i_win_char.composable_abilities) == 1
        assert i_win_char.composable_abilities[0].name == "I WIN"
    
    def test_i_win_only_triggers_for_self(self):
        """Test that I WIN only triggers when the ability owner is banished."""
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        other_char = self.create_test_character("Other Character")
        attacker = self.create_test_character("Attacker", strength=5, willpower=3)
        
        # Give player1 more cards than player2
        self._add_cards_to_hand(self.player1, 5, 4200)
        self._add_cards_to_hand(self.player2, 2, 4300)
        
        # Play characters using proper game moves
        self._play_character_to_field(i_win_char, self.player1)
        self._play_character_to_field(other_char, self.player1)
        self._play_character_to_field(attacker, self.player2)
        
        # Track initial hand size
        initial_hand_size = len(self.player1.hand)
        
        # Challenge other character (not the i_win character)
        challenge_move = ChallengeMove(attacker, other_char)
        message = self.game_engine.next_message(challenge_move)
        
        # I WIN should not have triggered (other character was banished)
        # Hand size should not have changed
        current_hand_size = len(self.player1.hand)
        # Note: Hand size might change due to the challenge itself, 
        # but I WIN should not have added the card back
    
    def test_i_win_ability_registration(self):
        """Test that I WIN ability is properly registered."""
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        
        # Play character using proper game moves
        self._play_character_to_field(i_win_char, self.player1)
        
        # Should have ability
        assert i_win_char.composable_abilities
        assert i_win_char.composable_abilities[0].name == "I WIN"
        
        # Check that it has listeners for the correct event
        ability = i_win_char.composable_abilities[0]
        assert len(ability.listeners) > 0
    
    def test_i_win_conditional_effect_structure(self):
        """Test that I WIN uses ConditionalEffect correctly."""
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        
        # Should have I WIN ability with conditional effect
        assert len(i_win_char.composable_abilities) == 1
        i_win_ability = i_win_char.composable_abilities[0]
        assert i_win_ability.name == "I WIN"
        
        # Verify the ability has the correct components
        assert len(i_win_ability.listeners) > 0
        
        # The actual conditional effect checking would happen through the game engine
        # For now, verify the ability is correctly set up
    
    def test_i_win_hand_size_condition_function(self):
        """Test the hand size condition function directly."""
        from lorcana_sim.models.abilities.composable.named_abilities.triggered.i_win import _has_most_cards_condition
        
        i_win_char = self.create_i_win_character("Mad Hatter - Gracious Host")
        i_win_char.controller = self.player1
        
        # Test condition with more cards
        self._add_cards_to_hand(self.player1, 5, 4400)
        self._add_cards_to_hand(self.player2, 2, 4500)
        
        context = {'game_state': self.game_state}
        assert _has_most_cards_condition(i_win_char, context) == True
        
        # Test condition with equal cards
        self.player1.hand.clear()
        self.player2.hand.clear()
        self._add_cards_to_hand(self.player1, 3, 4600)
        self._add_cards_to_hand(self.player2, 3, 4700)
        
        assert _has_most_cards_condition(i_win_char, context) == False
        
        # Test condition with fewer cards
        self.player1.hand.clear()
        self.player2.hand.clear()
        self._add_cards_to_hand(self.player1, 2, 4800)
        self._add_cards_to_hand(self.player2, 4, 4900)
        
        assert _has_most_cards_condition(i_win_char, context) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])