"""THAT'S BETTER - When you play this character, chosen character gains Challenger +2 this turn. (They get +2 ¤ while challenging.)"""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GAIN_CHALLENGER_BUFF
from ...target_selectors import CONTROLLER
from ...triggers import when_enters_play
from ......engine.choice_system import choose_character_effect


@register_named_ability("THAT'S BETTER")
def create_thats_better(character: Any, ability_data: dict):
    """THAT'S BETTER - When you play this character, chosen character gains Challenger +2 this turn.
    
    Implementation: Uses new choice system to let player choose which character gains Challenger +2.
    """
    # Create the choice effect: choose a friendly character to gain Challenger +2
    choice_effect = choose_character_effect(
        prompt="Choose a character to gain Challenger +2 this turn",
        character_filter=lambda char: True,  # Any friendly character
        effect_on_selected=GAIN_CHALLENGER_BUFF(2, "turn"),
        ability_name="THAT'S BETTER",
        allow_none=False,  # Must choose a character
        from_play=True,
        from_hand=False,
        controller_characters=True,  # Only friendly characters
        opponent_characters=False
    )
    
    return quick_ability(
        "THAT'S BETTER",
        character,
        when_enters_play(character),
        CONTROLLER,
        choice_effect
    )