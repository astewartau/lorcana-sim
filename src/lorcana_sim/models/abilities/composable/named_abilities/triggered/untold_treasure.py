"""UNTOLD TREASURE - When you play this character, if you have an Illusion character in play, you may draw a card."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import DRAW_CARD
from ...target_selectors import CONTROLLER
from ...composable_triggers import when_enters_play, character_present
from ......engine.choice_system import may_effect


@register_named_ability("UNTOLD TREASURE")
def create_untold_treasure(character: Any, ability_data: dict):
    """UNTOLD TREASURE - When you play this character, if you have an Illusion character in play, you may draw a card.
    
    Implementation: Composable trigger using when_enters_play & character_present.
    Clean, reusable, and easy to understand.
    """
    # Create choice effect for "may draw a card"
    choice_effect = may_effect(
        prompt="Draw a card?",
        effect=DRAW_CARD,
        ability_name="UNTOLD TREASURE"
    )
    
    # Compose the trigger: when this character enters play AND illusion is in play
    trigger = when_enters_play(character) & character_present(subtype="Illusion")
    
    return quick_ability(
        "UNTOLD TREASURE",
        character,
        trigger.to_trigger(),  # Convert back to standard trigger
        CONTROLLER,
        choice_effect
    )