"""MY ORDERS COME FROM JAFAR - When you play this character, if you have a character named Jafar in play, you may banish chosen item."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import BANISH_TARGET, ConditionalEffect
from ...target_selectors import TARGET_WITH_COST_CONSTRAINT
from ...triggers import when_enters_play


def _has_jafar_condition(character: Any, context: dict) -> bool:
    """Check if controller has a character named Jafar in play."""
    if not hasattr(character, 'controller') or not context.get('game_state'):
        return False
    
    game_state = context['game_state']
    controller = character.controller
    
    # Check for Jafar
    for player in game_state.players:
        if player == controller:
            for char in player.characters_in_play:
                if hasattr(char, 'name') and 'Jafar' in char.name:
                    return True
    
    return False


def _is_item_filter(target: Any) -> bool:
    """Filter for item cards."""
    return hasattr(target, 'card_type') and target.card_type == 'Item'


@register_named_ability("MY ORDERS COME FROM JAFAR")
def create_my_orders_come_from_jafar(character: Any, ability_data: dict):
    """MY ORDERS COME FROM JAFAR - When you play this character, if you have a character named Jafar in play, you may banish chosen item.
    
    Implementation: When this character enters play, if you have Jafar, banish an item.
    """
    return quick_ability(
        "MY ORDERS COME FROM JAFAR",
        character,
        when_enters_play(character),
        TARGET_WITH_COST_CONSTRAINT(
            cost_constraint=_is_item_filter,
            valid_types=['item']
        ),
        ConditionalEffect(
            condition=_has_jafar_condition,
            effect=BANISH_TARGET
        )
    )