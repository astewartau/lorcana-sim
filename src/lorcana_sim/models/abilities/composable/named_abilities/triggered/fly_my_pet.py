"""FLY, MY PET! - When this character is banished, you may draw a card."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import DRAW_CARD
from ...target_selectors import CONTROLLER
from ...triggers import when_banished
from ...conditional_effects import ActivationZone


@register_named_ability("FLY, MY PET!")
def create_fly_my_pet(character: Any, ability_data: dict):
    """FLY, MY PET! - When this character is banished, you may draw a card.
    
    Implementation: Uses quick_ability with may_effect for proper optional choice.
    This ability must be active in both PLAY and DISCARD zones since the CHARACTER_BANISHED
    event fires after the character has already been moved to discard.
    """
    from lorcana_sim.engine.choice_system import may_effect
    
    ability = quick_ability(
        "FLY, MY PET!", 
        character,
        when_banished(character),
        CONTROLLER,
        may_effect("Draw a card?", DRAW_CARD, "FLY, MY PET!")
    )
    
    # Set activation zones to include DISCARD since CHARACTER_BANISHED fires after move
    ability.active_in_zones(ActivationZone.PLAY, ActivationZone.DISCARD)
    
    return ability