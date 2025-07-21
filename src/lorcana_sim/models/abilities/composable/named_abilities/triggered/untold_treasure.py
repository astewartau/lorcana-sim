"""UNTOLD TREASURE - When you play this character, if you have an Illusion character in play, you may draw a card."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import DRAW_CARD
from ...target_selectors import CONTROLLER
from ...composable_triggers import when_enters_play, character_present


@register_named_ability("UNTOLD TREASURE")
def create_untold_treasure(character: Any, ability_data: dict):
    """UNTOLD TREASURE - When you play this character, if you have an Illusion character in play, you may draw a card.
    
    Implementation: Uses new choice-based architectural pattern with optional choice.
    """
    # Compose the trigger: when this character enters play AND illusion is in play
    trigger = when_enters_play(character) & character_present(subtype="Illusion")
    
    return (ComposableAbility("UNTOLD TREASURE", character)
            .choice_effect(
                trigger_condition=trigger.to_trigger(),
                target_selector=CONTROLLER,
                effect=DRAW_CARD,
                name="UNTOLD TREASURE"
            ))