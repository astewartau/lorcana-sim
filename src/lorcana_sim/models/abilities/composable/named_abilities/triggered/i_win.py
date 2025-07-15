"""I WIN - When this character is banished, if you have more cards in your hand than each opponent, you may return this card to your hand."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import RETURN_SELF_TO_HAND
from ...target_selectors import SELF
from ...triggers import when_banished


def _has_most_cards_condition(character: Any, context: dict) -> bool:
    """Check if controller has more cards in hand than each opponent."""
    if not hasattr(character, 'controller') or not context.get('game_state'):
        return False
    
    game_state = context['game_state']
    controller = character.controller
    controller_hand_size = len(controller.hand) if hasattr(controller, 'hand') else 0
    
    # Check that controller has more cards than each opponent
    for player in game_state.players:
        if player != controller:  # Opponent
            opponent_hand_size = len(player.hand) if hasattr(player, 'hand') else 0
            if controller_hand_size <= opponent_hand_size:
                return False
    
    return True


@register_named_ability("I WIN")
def create_i_win(character: Any, ability_data: dict):
    """I WIN - When this character is banished, if you have more cards in your hand than each opponent, you may return this card to your hand.
    
    Implementation: When this character is banished, check hand sizes and optionally return to hand.
    """
    return quick_ability(
        "I WIN",
        character,
        when_banished(character),
        SELF,
        RETURN_SELF_TO_HAND(condition_func=_has_most_cards_condition)
    )