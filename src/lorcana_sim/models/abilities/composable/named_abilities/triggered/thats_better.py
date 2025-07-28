"""THAT'S BETTER - When you play this character, chosen character gains Challenger +2 this turn. (They get +2 ¤ while challenging.)"""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import TemporaryEffect, GrantProperty
from ...target_selectors import FRIENDLY_CHARACTER
from ...triggers import when_enters_play


@register_named_ability("THAT'S BETTER")
def create_thats_better(character: Any, ability_data: dict):
    """THAT'S BETTER - When you play this character, chosen character gains Challenger +2 this turn.
    
    Implementation: Uses new choice-based architectural pattern with TemporaryEffect.
    """
    # Create temporary effect that grants Challenger +2 until end of turn
    temporary_challenger = TemporaryEffect(
        wrapped_effect=GrantProperty('has_challenger_2', True),
        duration_type="until_end_of_turn",
        duration_value=1
    )
    
    return (ComposableAbility("THAT'S BETTER", character)
            .choice_effect(
                trigger_condition=when_enters_play(character),
                target_selector=FRIENDLY_CHARACTER,
                effect=temporary_challenger,
                name="THAT'S BETTER"
            ))