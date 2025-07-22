"""PARTING GIFT - When this character is banished, you may draw a card."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import DRAW_CARD
from ...target_selectors import CONTROLLER
from ...triggers import when_banished
from ...conditional_effects import ActivationZone


@register_named_ability("PARTING GIFT")
def create_parting_gift(character: Any, ability_data: dict):
    """PARTING GIFT - When this character is banished, you may draw a card.
    
    Implementation: Uses new choice-based architectural pattern with optional choice.
    This ability must be active in both PLAY and DISCARD zones since the CHARACTER_BANISHED
    event fires after the character has already been moved to discard.
    """
    return (ComposableAbility("PARTING GIFT", character)
            .active_in_zones(ActivationZone.PLAY, ActivationZone.DISCARD)
            .choice_effect(
                trigger_condition=when_banished(character),
                target_selector=CONTROLLER,
                effect=DRAW_CARD,
                name="PARTING GIFT"
            ))