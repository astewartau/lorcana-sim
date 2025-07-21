"""AND TWO FOR TEA! - When you play this character, you may remove up to 2 damage from each of your Musketeer characters."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import REMOVE_DAMAGE_2
from ...target_selectors import CharacterSelector, friendly_filter, subtype_filter, and_filters
from ...triggers import when_enters_play


@register_named_ability("AND TWO FOR TEA!")
def create_and_two_for_tea(character: Any, ability_data: dict):
    """AND TWO FOR TEA! - When you play this character, you may remove up to 2 damage from each of your Musketeer characters.
    
    Implementation: When this character enters play, target all friendly Musketeer characters and remove damage.
    """
    # Use choice-based pattern like CRYSTALLIZE for proper triggering
    return (ComposableAbility("AND TWO FOR TEA!", character)
            .choice_effect(
                trigger_condition=when_enters_play(character),
                target_selector=CharacterSelector(
                    and_filters(
                        friendly_filter,
                        subtype_filter("Musketeer")
                    ),
                    count=999  # Target ALL Musketeer characters
                ),
                effect=REMOVE_DAMAGE_2,
                name="AND TWO FOR TEA!"
            ))