"""PLUCKY PLAY - When you play this character, each opponent chooses one of their characters to deal 1 damage to."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import Effect, DAMAGE_1
from ...target_selectors import CharacterSelector
from ...triggers import when_enters_play


class PluckyPlayEffect(Effect):
    """Effect that makes each opponent choose one of their characters to deal 1 damage to."""
    
    def apply(self, target: Any, context: dict) -> Any:
        game_state = context.get('game_state')
        ability_owner = context.get('ability_owner')
        action_queue = context.get('action_queue')
        
        if not game_state or not ability_owner or not action_queue:
            return target
        
        # For each opponent player, queue a choice effect
        for player in game_state.players:
            if player != ability_owner.controller:
                # Get characters for this opponent
                opponent_chars = [c for c in player.characters_in_play]
                
                if opponent_chars:
                    # Create a selector for this opponent's characters
                    def opponent_filter(char, ctx, current_player=player):
                        return char.controller == current_player
                    
                    opponent_selector = CharacterSelector(opponent_filter)
                    
                    # Create a ChoiceGenerationEffect for this opponent
                    from ...effects import ChoiceGenerationEffect
                    
                    choice_effect = ChoiceGenerationEffect(
                        target_selector=opponent_selector,
                        follow_up_effect=DAMAGE_1,
                        ability_name="PLUCKY PLAY"
                    )
                    
                    # Queue the choice effect with the opponent as the target
                    choice_context = context.copy()
                    choice_context['player'] = player
                    choice_context['ability_owner'] = ability_owner
                    
                    action_queue.enqueue(
                        choice_effect,
                        player,  # The opponent who will make the choice
                        choice_context
                    )
        
        return target
    
    def __str__(self) -> str:
        return "each opponent chooses a character to deal 1 damage to"


@register_named_ability("PLUCKY PLAY")
def create_plucky_play(character: Any, ability_data: dict):
    """PLUCKY PLAY - When you play this character, each opponent chooses one of their characters to deal 1 damage to.
    
    Implementation: Uses new choice-based architectural pattern with multiple opponent choices.
    """
    return (ComposableAbility("PLUCKY PLAY", character)
            .add_trigger(
                trigger_condition=when_enters_play(character),
                target_selector=CharacterSelector(lambda c, ctx: False),  # No direct target
                effect=PluckyPlayEffect(),
                name="PLUCKY PLAY"
            ))