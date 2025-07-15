"""GROWING POWERS - When you play this character, each opponent chooses and exerts one of their ready characters."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import EXERT_CHARACTER
from ...target_selectors import CONTROLLER
from ...triggers import when_enters_play
from ......engine.choice_system import choose_character_effect


class GrowingPowersEffect:
    """Effect that makes each opponent choose and exert one of their ready characters."""
    
    def apply(self, target: Any, context: dict) -> Any:
        game_state = context.get('game_state')
        ability_owner = context.get('ability_owner')
        choice_manager = context.get('choice_manager')
        
        if not game_state or not ability_owner or not choice_manager:
            return target
        
        # For each opponent player
        for player in game_state.players:
            if player != ability_owner.controller:
                # Get ready characters for this opponent
                ready_chars = [c for c in player.characters_in_play 
                             if hasattr(c, 'exerted') and not c.exerted]
                
                if ready_chars:
                    # Create a choice for this specific opponent
                    # Note: We need to capture the player variable properly in the lambda
                    current_player = player  # Capture the current player value
                    choice_effect = choose_character_effect(
                        prompt="Choose one of your ready characters to exert",
                        character_filter=lambda char, current_player=current_player: not char.exerted and char.controller == current_player,
                        effect_on_selected=EXERT_CHARACTER,
                        ability_name="GROWING POWERS",
                        allow_none=False,  # Must choose a character
                        from_play=True,
                        from_hand=False,
                        controller_characters=True,  # Show the choosing player's characters
                        opponent_characters=False
                    )
                    
                    # Apply the choice effect to this specific player
                    choice_context = context.copy()
                    choice_context['player'] = player
                    choice_context['ability_owner'] = ability_owner
                    choice_effect.apply(player, choice_context)
        
        return target
    
    def __str__(self) -> str:
        return "each opponent chooses and exerts a ready character"


@register_named_ability("GROWING POWERS")
def create_growing_powers(character: Any, ability_data: dict):
    """GROWING POWERS - When you play this character, each opponent chooses and exerts one of their ready characters.
    
    Implementation: Uses new choice system to let each opponent choose which character to exert.
    """
    return quick_ability(
        "GROWING POWERS",
        character,
        when_enters_play(character),
        CONTROLLER,
        GrowingPowersEffect()
    )