"""A WONDERFUL DREAM - ⟲ — Remove up to 3 damage from chosen Princess character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import REMOVE_DAMAGE_3
from ...target_selectors import CharacterSelector, subtype_filter
from ...triggers import when_ability_activated


@register_named_ability("A WONDERFUL DREAM")
def create_a_wonderful_dream(character: Any, ability_data: dict):
    """A WONDERFUL DREAM - ⟲ — Remove up to 3 damage from chosen Princess character.
    
    Implementation: Uses new choice-based architectural pattern with Princess character selection.
    """
    # Create selector for Princess characters
    princess_selector = CharacterSelector(subtype_filter("Princess"))
    
    return (ComposableAbility("A WONDERFUL DREAM", character)
            .choice_effect(
                trigger_condition=when_ability_activated(character, "A WONDERFUL DREAM"),
                target_selector=princess_selector,
                effect=REMOVE_DAMAGE_3,
                name="A WONDERFUL DREAM"
            ))