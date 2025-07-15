"""EXTRACT OF AMETHYST - Return chosen character, item, or location with cost 3 or less to their player's hand."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import RETURN_TO_HAND
from ...target_selectors import TARGET_WITH_COST_CONSTRAINT
from ...triggers import on_activation


def _cost_3_or_less_filter(target: Any) -> bool:
    """Filter for targets with cost 3 or less."""
    return hasattr(target, 'cost') and target.cost <= 3


@register_named_ability("EXTRACT OF AMETHYST")
def create_extract_of_amethyst(character: Any, ability_data: dict):
    """EXTRACT OF AMETHYST - Return chosen character, item, or location with cost 3 or less to their player's hand.
    
    Implementation: Activated ability to return a target with cost 3 or less to hand.
    """
    return quick_ability(
        "EXTRACT OF AMETHYST",
        character,
        on_activation(),
        TARGET_WITH_COST_CONSTRAINT(
            cost_constraint=_cost_3_or_less_filter,
            valid_types=['character', 'item', 'location']
        ),
        RETURN_TO_HAND
    )