"""MYSTERIOUS ADVANTAGE - When you play this character, you may choose and discard a card to gain 2 lore."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import GAIN_LORE, DISCARD_CARD, CompositeEffect
from ...target_selectors import CARDS_IN_HAND
from ...triggers import when_enters_play


@register_named_ability("MYSTERIOUS ADVANTAGE")
def create_mysterious_advantage(character: Any, ability_data: dict):
    """MYSTERIOUS ADVANTAGE - When you play this character, you may choose and discard a card to gain 2 lore.
    
    Implementation: Uses new choice-based architectural pattern with ChoiceGenerationEffect.
    """
    return (ComposableAbility("MYSTERIOUS ADVANTAGE", character)
            .choice_effect(
                trigger_condition=when_enters_play(character),
                target_selector=CARDS_IN_HAND,
                effect=CompositeEffect([DISCARD_CARD, GAIN_LORE(2)]),
                name="MYSTERIOUS ADVANTAGE"
            ))