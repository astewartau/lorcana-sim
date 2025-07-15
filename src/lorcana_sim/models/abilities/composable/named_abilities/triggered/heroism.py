"""HEROISM - When this character challenges and is banished, you may banish the challenged character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import BANISH_TARGET
from ...target_selectors import EVENT_TARGET
from ...triggers import when_banished_in_challenge


@register_named_ability("HEROISM")
def create_heroism(character: Any, ability_data: dict):
    """HEROISM - When this character challenges and is banished, you may banish the challenged character.
    
    Implementation: When this character is banished in a challenge, banish the target.
    """
    return quick_ability(
        "HEROISM",
        character,
        when_banished_in_challenge(character),
        EVENT_TARGET,  # The character that was challenged
        BANISH_TARGET
    )