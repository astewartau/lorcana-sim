"""WHAT DO WE DO NOW? - Whenever this character quests, if you have a character named Anna in play, gain 1 lore."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GAIN_LORE
from ...target_selectors import CONTROLLER
from ...composable_triggers import when_quests, character_present


@register_named_ability("WHAT DO WE DO NOW?")
def create_what_do_we_do_now(character: Any, ability_data: dict):
    """WHAT DO WE DO NOW? - Whenever this character quests, if you have a character named Anna in play, gain 1 lore.
    
    Implementation: Composable trigger using when_quests & character_present.
    Clean, reusable, and easy to understand.
    """
    
    return quick_ability(
        "WHAT DO WE DO NOW?",
        character,
        (when_quests(character) & character_present(name="Anna")).to_trigger(),  # Convert back to standard trigger
        CONTROLLER,
        GAIN_LORE(1)
    )
