"""GRASPING TRUNK - Whenever this character quests, gain lore equal to the ◊ of chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GainLoreEffect
from ...target_selectors import ENEMY_CHARACTER
from ...triggers import when_quests


class GainLoreEqualToTargetLore:
    """Gain lore equal to target's lore value."""
    
    def apply(self, target: Any, context: dict) -> Any:
        lore_value = getattr(target, 'lore', 0)
        ability_owner = context.get('ability_owner')
        if ability_owner and hasattr(ability_owner, 'controller'):
            controller = ability_owner.controller
            if hasattr(controller, 'gain_lore'):
                controller.gain_lore(lore_value)
        return target
    
    def get_events(self, target: Any, context: dict, result: Any) -> list:
        return []
    
    def __str__(self) -> str:
        return "gain lore equal to target's lore"


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
        GainLoreEqualToTargetLore()
    )