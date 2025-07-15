"""MYSTERIOUS ADVANTAGE - When you play this character, you may choose and discard a card to gain 2 lore."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import GAIN_LORE, DISCARD_CARD, CompositeEffect
from ...target_selectors import CONTROLLER
from ...triggers import when_enters_play
from ......engine.choice_system import may_choose_card_effect


@register_named_ability("MYSTERIOUS ADVANTAGE")
def create_mysterious_advantage(character: Any, ability_data: dict):
    """MYSTERIOUS ADVANTAGE - When you play this character, you may choose and discard a card to gain 2 lore.
    
    Implementation: Uses new choice system to let player select a card to discard and gain 2 lore.
    """
    # Create the choice effect: may choose a card to discard, then gain 2 lore
    choice_effect = may_choose_card_effect(
        prompt="Choose a card to discard and gain 2 lore",
        card_filter=lambda card: True,  # Any card can be discarded
        effect_on_selected=CompositeEffect([DISCARD_CARD, GAIN_LORE(2)]),
        ability_name="MYSTERIOUS ADVANTAGE",
        from_hand=True
    )
    
    return quick_ability(
        "MYSTERIOUS ADVANTAGE",
        character,
        when_enters_play(character),
        CONTROLLER,
        choice_effect
    )