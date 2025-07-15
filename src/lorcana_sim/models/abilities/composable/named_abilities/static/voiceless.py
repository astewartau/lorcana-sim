"""VOICELESS - This character can't ⟳ to sing songs."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import PREVENT_SINGING
from ...target_selectors import SELF
from ...triggers import when_enters_play


@register_named_ability("VOICELESS")
def create_voiceless(character: Any, ability_data: dict):
    """VOICELESS - This character can't ⟳ to sing songs.
    
    Implementation: When this character enters play, mark it as unable to sing.
    """
    return quick_ability(
        "VOICELESS",
        character,
        when_enters_play(character),
        SELF,
        PREVENT_SINGING
    )