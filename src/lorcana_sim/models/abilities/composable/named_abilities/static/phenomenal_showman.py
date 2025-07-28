"""PHENOMENAL SHOWMAN - While this character is exerted, opposing characters can't ready at the start of their turn."""

from typing import Any, Dict
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import StatefulConditionalEffect, PreventReadying, NoEffect
from ...target_selectors import ALL_ENEMIES
from ...triggers import when_character_exerts, when_character_readies, when_enters_play, or_conditions


def _is_phenomenal_showman_exerted(character):
    """Create a condition function for a specific Phenomenal Showman character."""
    def condition(target: Any, context: Dict[str, Any]) -> bool:
        """Check if the Phenomenal Showman character is exerted."""
        return hasattr(character, 'exerted') and character.exerted
    return condition


@register_named_ability("PHENOMENAL SHOWMAN")
def create_phenomenal_showman(character: Any, ability_data: dict):
    """PHENOMENAL SHOWMAN - While this character is exerted, opposing characters can't ready at the start of their turn.
    
    Implementation: Stateful conditional effect that prevents opponent readying while this character is exerted.
    """
    
    # Create conditional effect that applies to each opponent character individually
    conditional_effect = StatefulConditionalEffect(
        condition=_is_phenomenal_showman_exerted(character),
        true_effect=PreventReadying(),  # Grant prevention when exerted
        false_effect=NoEffect(),        # Remove prevention when not exerted (handled automatically)
        state_key=f'phenomenal_showman_{id(character)}'
    )
    
    # Evaluate the condition when:
    # 1. This character becomes exerted/readied
    # 2. When this character enters play
    # 3. At the start of any turn (for cleanup/verification)
    evaluation_trigger = or_conditions(
        when_character_exerts(character),
        when_character_readies(character),
        when_enters_play(character)
    )
    
    return quick_ability(
        "PHENOMENAL SHOWMAN",
        character,
        evaluation_trigger,
        ALL_ENEMIES,  # Apply to all opponent characters
        conditional_effect
    )