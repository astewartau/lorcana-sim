"""PLAY ROUGH - Whenever this character quests, exert chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import EXERT_CHARACTER
from ...target_selectors import CONTROLLER
from ...triggers import when_quests
from ......engine.choice_system import choose_character_effect


@register_named_ability("PLAY ROUGH")
def create_play_rough(character: Any, ability_data: dict):
    """PLAY ROUGH - Whenever this character quests, exert chosen opposing character.
    
    Implementation: Uses new choice system to let player choose which opposing character to exert.
    """
    # Create the choice effect: choose an opposing character to exert
    choice_effect = choose_character_effect(
        prompt="Choose an opposing character to exert",
        character_filter=lambda char: True,  # Any opposing character
        effect_on_selected=EXERT_CHARACTER,
        ability_name="PLAY ROUGH",
        allow_none=False,  # Must choose a character
        from_play=True,
        from_hand=False,
        controller_characters=False,  # Only opposing characters
        opponent_characters=True
    )
    
    return quick_ability(
        "PLAY ROUGH",
        character,
        when_quests(character),
        CONTROLLER,
        choice_effect
    )