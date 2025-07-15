"""GRASPING TRUNK - Whenever this character quests, gain lore equal to the ◊ of chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GAIN_LORE_EQUAL_TO_TARGET_LORE
from ...target_selectors import ENEMY_CHARACTER
from ...triggers import when_quests


@register_named_ability("GRASPING TRUNK")
def create_grasping_trunk(character: Any, ability_data: dict):
    """GRASPING TRUNK - Whenever this character quests, gain lore equal to the ◊ of chosen opposing character.
    
    Implementation: When this character quests, choose an opposing character and gain lore equal to their lore value.
    """
    return quick_ability(
        "GRASPING TRUNK",
        character,
        when_quests(character),
        ENEMY_CHARACTER,
        GAIN_LORE_EQUAL_TO_TARGET_LORE
    )