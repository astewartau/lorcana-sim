"""A WONDERFUL DREAM - ⟲ — Remove up to 3 damage from chosen Princess character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import REMOVE_DAMAGE_3
from ...target_selectors import CONTROLLER
from ...triggers import when_ability_activated
from ......engine.choice_system import choose_character_effect


@register_named_ability("A WONDERFUL DREAM")
def create_a_wonderful_dream(character: Any, ability_data: dict):
    """A WONDERFUL DREAM - ⟲ — Remove up to 3 damage from chosen Princess character.
    
    Implementation: Uses new choice system to let player choose which Princess character to heal.
    """
    # Create the choice effect: choose a Princess character to remove damage from
    choice_effect = choose_character_effect(
        prompt="Choose a Princess character to remove up to 3 damage from",
        character_filter=lambda char: "Princess" in getattr(char, 'subtypes', []),
        effect_on_selected=REMOVE_DAMAGE_3,
        ability_name="A WONDERFUL DREAM",
        allow_none=False,  # Must choose a target
        from_play=True,
        from_hand=False,
        controller_characters=True,  # Only friendly characters
        opponent_characters=False
    )
    
    return quick_ability(
        "A WONDERFUL DREAM",
        character,
        when_ability_activated(character, "A WONDERFUL DREAM"),
        CONTROLLER,
        choice_effect
    )