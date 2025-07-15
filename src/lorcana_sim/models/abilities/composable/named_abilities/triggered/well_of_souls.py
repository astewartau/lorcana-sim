"""WELL OF SOULS - When you play this character, return a character card from your discard to your hand."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import ReturnToHand
from ...target_selectors import CONTROLLER
from ...triggers import when_enters_play
from ......engine.choice_system import choose_card_effect


@register_named_ability("WELL OF SOULS")
def create_well_of_souls(character: Any, ability_data: dict):
    """WELL OF SOULS - When you play this character, return a character card from your discard to your hand.
    
    Implementation: Uses new choice system to let player choose which character card to return from discard.
    """
    # Create the choice effect: choose a character card from discard to return to hand
    choice_effect = choose_card_effect(
        prompt="Choose a character card from your discard to return to your hand",
        card_filter=lambda card: hasattr(card, 'strength'),  # Filter for character cards
        effect_on_selected=ReturnToHand(),
        ability_name="WELL OF SOULS",
        from_hand=False,
        from_discard=True
    )
    
    return quick_ability(
        "WELL OF SOULS",
        character,
        when_enters_play(character),
        CONTROLLER,
        choice_effect
    )