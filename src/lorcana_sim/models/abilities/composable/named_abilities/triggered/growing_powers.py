"""GROWING POWERS - When you play this character, each opponent chooses and exerts one of their ready characters."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import Effect, EXERT
from ...target_selectors import CharacterSelector, ready_filter
from ...triggers import when_enters_play


class GrowingPowersEffect(Effect):
    """Effect that makes each opponent choose and exert one of their ready characters."""
    
    def apply(self, target: Any, context: dict) -> Any:
        game_state = context.get('game_state')
        ability_owner = context.get('ability_owner')
        action_queue = context.get('action_queue')
        
        if not game_state or not ability_owner or not action_queue:
            return target
        
        # For each opponent player, queue a choice effect
        for player in game_state.players:
            if player != ability_owner.controller:
                # Get ready characters for this opponent
                ready_chars = [c for c in player.characters_in_play 
                             if hasattr(c, 'exerted') and not c.exerted]
                
                if ready_chars:
                    # Create a selector for this opponent's ready characters
                    def opponent_ready_filter(char, ctx, current_player=player):
                        return (char.controller == current_player and 
                               ready_filter(char, ctx))
                    
                    opponent_selector = CharacterSelector(opponent_ready_filter)
                    
                    # Create a ChoiceGenerationEffect for this opponent
                    from ...effects import ChoiceGenerationEffect
                    
                    choice_effect = ChoiceGenerationEffect(
                        target_selector=opponent_selector,
                        follow_up_effect=EXERT,
                        ability_name="GROWING POWERS"
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
        return "each opponent chooses and exerts a ready character"


@register_named_ability("GROWING POWERS")
def create_growing_powers(character: Any, ability_data: dict):
    """GROWING POWERS - When you play this character, each opponent chooses and exerts one of their ready characters.
    
    Implementation: Uses new choice-based architectural pattern with multiple opponent choices.
    """
    return (ComposableAbility("GROWING POWERS", character)
            .add_trigger(
                trigger_condition=when_enters_play(character),
                target_selector=CharacterSelector(lambda c, ctx: False),  # No direct target
                effect=GrowingPowersEffect(),
                name="GROWING POWERS"
            ))