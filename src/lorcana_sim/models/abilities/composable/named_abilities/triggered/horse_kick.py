"""HORSE KICK - When you play this character, chosen character gets -2 ⚔ this turn."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import StatModification
from ...target_selectors import CharacterSelector
from ...triggers import when_enters_play


@register_named_ability("HORSE KICK")
def create_horse_kick(character: Any, ability_data: dict):
    """HORSE KICK - When you play this character, chosen character gets -2 ⚔ this turn.
    
    Implementation: When this character enters play, target a character and give temporary -2 strength.
    """
    return (ComposableAbility("HORSE KICK", character)
            .choice_effect(
                trigger_condition=when_enters_play(character),
                target_selector=CharacterSelector(),  # Any character can be chosen
                effect=StatModification("strength", -2, "this_turn"),
                name="HORSE KICK"
            ))