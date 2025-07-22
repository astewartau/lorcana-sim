"""GRASPING TRUNK - Whenever this character quests, gain lore equal to the ◊ of chosen opposing character."""

from typing import Any, Dict, List
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import GainLoreEffect
from ...target_selectors import ENEMY_CHARACTER
from ...triggers import when_quests


class GainLoreEqualToTargetLore(GainLoreEffect):
    """Gain lore equal to target's lore value - extends standard GainLoreEffect."""
    
    def __init__(self):
        # Initialize with 0, will be set dynamically in apply()
        super().__init__(0)
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply the effect - gain lore equal to target's lore value."""
        # Get the target's lore value dynamically
        lore_value = getattr(target, 'lore', 0)
        
        # Update our amount to the dynamic value
        self.amount = lore_value
        
        # The target is the selected character, but we need to gain lore for the ability owner
        # Check if there's an ability_owner in context
        if 'ability_owner' in context:
            ability_owner = context['ability_owner']
            if hasattr(ability_owner, 'controller'):
                lore_gainer = ability_owner.controller
                return super().apply(lore_gainer, context)
        
        # Fallback to original logic
        return super().apply(target, context)


@register_named_ability("GRASPING TRUNK")
def create_grasping_trunk(character: Any, ability_data: dict):
    """GRASPING TRUNK - Whenever this character quests, gain lore equal to the ◊ of chosen opposing character.
    
    Implementation: Uses new choice-based architectural pattern with enemy character selection.
    """
    return (ComposableAbility("GRASPING TRUNK", character)
            .choice_effect(
                trigger_condition=when_quests(character),
                target_selector=ENEMY_CHARACTER,
                effect=GainLoreEqualToTargetLore(),
                name="GRASPING TRUNK"
            ))