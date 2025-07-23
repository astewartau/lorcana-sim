"""MY ORDERS COME FROM JAFAR - When you play this character, if you have a character named Jafar in play, you may banish chosen item."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility, quick_ability
from ...effects import BanishCharacter, ConditionalEffect
from ...target_selectors import TARGET_WITH_COST_CONSTRAINT, TargetWithCostConstraintSelector
from ...triggers import when_enters_play


class BanishItemEffect:
    """Effect that banishes an item card."""
    
    def apply(self, target: Any, context: dict) -> Any:
        """Banish target item by removing it from play to discard."""
        if not hasattr(target, 'controller') or not target.controller:
            return None
            
        controller = target.controller
        
        # Remove from items in play
        if target in controller.items_in_play:
            controller.items_in_play.remove(target)
            controller.discard_pile.append(target)
            return target
            
        return None


class JafarConditionalBanishItem(BanishItemEffect):
    """Conditional banish effect that only works if Jafar is in play."""
    
    def apply(self, target: Any, context: dict) -> Any:
        """Apply banish only if controller has Jafar in play."""
        # Get the ability source character
        if 'ability_owner' not in context:
            return None
            
        source_character = context['ability_owner']
        
        if not source_character or not hasattr(source_character, 'controller'):
            return None
            
        game_state = context.get('game_state')
        if not game_state:
            return None
            
        controller = source_character.controller
        
        # Check for Jafar
        has_jafar = False
        for player in game_state.players:
            if player == controller:
                for char in player.characters_in_play:
                    if hasattr(char, 'name') and 'Jafar' in char.name:
                        has_jafar = True
                        break
                break
                
        if not has_jafar:
            return None  # Ability does nothing if no Jafar
            
        # Apply the banish effect
        return super().apply(target, context)


def _is_item_filter(target: Any) -> bool:
    """Filter for item cards."""
    return hasattr(target, 'card_type') and target.card_type == 'Item'


@register_named_ability("MY ORDERS COME FROM JAFAR")
def create_my_orders_come_from_jafar(character: Any, ability_data: dict):
    """MY ORDERS COME FROM JAFAR - When you play this character, if you have a character named Jafar in play, you may banish chosen item.
    
    Implementation: When this character enters play, if you have Jafar, player chooses an item to banish.
    """
    return (ComposableAbility("MY ORDERS COME FROM JAFAR", character)
            .choice_effect(
                trigger_condition=when_enters_play(character),
                target_selector=TargetWithCostConstraintSelector(
                    cost_constraint=lambda target: _is_item_filter(target),
                    valid_types=['item'],
                    count=1  # Select 1 item from all available options
                ),
                effect=JafarConditionalBanishItem(),
                name="MY ORDERS COME FROM JAFAR"
            ))