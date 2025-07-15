"""PHENOMENAL SHOWMAN - While this character is exerted, opposing characters can't ready at the start of their turn."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import ConditionalEffect
from ...target_selectors import ALL_ENEMIES
from ...triggers import when_turn_starts, when_character_exerts, when_character_readies, or_conditions


def _prevent_ready_condition(character: Any, context: dict) -> bool:
    """Check if this character is exerted to prevent opponents from readying."""
    return hasattr(character, 'exerted') and character.exerted


class PreventReadyEffect:
    """Effect that prevents opposing characters from readying."""
    
    def apply(self, target: Any, context: dict) -> Any:
        # This would need to be implemented in the game engine's ready step
        # For now, just mark that ready is prevented
        if hasattr(target, 'prevent_ready'):
            target.prevent_ready = True
        return target
    
    def __str__(self) -> str:
        return "prevent ready"


@register_named_ability("PHENOMENAL SHOWMAN")
def create_phenomenal_showman(character: Any, ability_data: dict):
    """PHENOMENAL SHOWMAN - While this character is exerted, opposing characters can't ready at the start of their turn.
    
    Implementation: Continuous effect that prevents opponent readying while this character is exerted.
    """
    return quick_ability(
        "PHENOMENAL SHOWMAN",
        character,
        or_conditions(
            when_turn_starts(),
            when_character_exerts(character),
            when_character_readies(character)
        ),
        ALL_ENEMIES,
        ConditionalEffect(
            condition=_prevent_ready_condition,
            effect=PreventReadyEffect()
        )
    )