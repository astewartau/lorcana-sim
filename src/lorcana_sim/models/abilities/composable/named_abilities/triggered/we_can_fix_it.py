"""WE CAN FIX IT - Whenever this character quests, you may ready your other Princess characters. 
They can't quest for the rest of this turn."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import ReadyCharactersEffect
from ...target_selectors import CharacterSelector, friendly_filter, subtype_filter, and_filters
from ...triggers import when_quests


@register_named_ability("WE CAN FIX IT")
def create_we_can_fix_it(character: Any, ability_data: dict):
    """WE CAN FIX IT - Whenever this character quests, you may ready your other Princess characters.
    They can't quest for the rest of this turn.
    
    Implementation: When this character quests, ready other friendly Princess characters.
    """
    def not_this_character_filter(target_char, context):
        return target_char != character
    
    return quick_ability(
        "WE CAN FIX IT",
        character,
        when_quests(character),
        CharacterSelector(
            and_filters(
                friendly_filter,
                subtype_filter("Princess"),
                not_this_character_filter
            )
        ),
        ReadyCharactersEffect()
    )