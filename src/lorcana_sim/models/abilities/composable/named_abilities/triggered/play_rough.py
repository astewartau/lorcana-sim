"""PLAY ROUGH - Whenever this character quests, exert chosen opposing character."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import EXERT
from ...target_selectors import ENEMY_CHARACTER
from ...triggers import when_quests


@register_named_ability("PLAY ROUGH")
def create_play_rough(character: Any, ability_data: dict):
    """PLAY ROUGH - Whenever this character quests, exert chosen opposing character.
    
    Implementation: Uses new choice-based architectural pattern with ChoiceGenerationEffect.
    """
    return (ComposableAbility("PLAY ROUGH", character)
            .choice_effect(
                trigger_condition=when_quests(character),
                target_selector=ENEMY_CHARACTER,
                effect=EXERT,
                name="PLAY ROUGH"
            ))