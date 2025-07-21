"""THAT'S BETTER - When you play this character, chosen character gains Challenger +2 this turn. (They get +2 ¤ while challenging.)"""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import ChallengerEffect
from ...target_selectors import FRIENDLY_CHARACTER
from ...triggers import when_enters_play


@register_named_ability("THAT'S BETTER")
def create_thats_better(character: Any, ability_data: dict):
    """THAT'S BETTER - When you play this character, chosen character gains Challenger +2 this turn.
    
    Implementation: Uses new choice-based architectural pattern with ChoiceGenerationEffect.
    """
    return (ComposableAbility("THAT'S BETTER", character)
            .choice_effect(
                trigger_condition=when_enters_play(character),
                target_selector=FRIENDLY_CHARACTER,
                effect=ChallengerEffect(2),
                name="THAT'S BETTER"
            ))