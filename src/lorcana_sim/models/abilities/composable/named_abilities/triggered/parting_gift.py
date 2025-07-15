"""PARTING GIFT - When this character is banished, you may draw a card."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import DRAW_CARD
from ...target_selectors import CONTROLLER
from ...triggers import when_banished
from ......engine.choice_system import may_effect


@register_named_ability("PARTING GIFT")
def create_parting_gift(character: Any, ability_data: dict):
    """PARTING GIFT - When this character is banished, you may draw a card.
    
    Implementation: Uses new choice system to give player option to draw a card when banished.
    """
    # Create the choice effect: may draw a card when banished
    choice_effect = may_effect(
        prompt="Draw a card?",
        effect=DRAW_CARD,
        ability_name="PARTING GIFT"
    )
    
    return quick_ability(
        "PARTING GIFT",
        character,
        when_banished(character),
        CONTROLLER,
        choice_effect
    )