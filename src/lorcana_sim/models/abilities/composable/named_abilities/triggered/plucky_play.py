"""PLUCKY PLAY - When you play this character, each opponent chooses one of their characters to deal 1 damage to."""

from typing import Any
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import DAMAGE_1
from ...target_selectors import CONTROLLER
from ...triggers import when_enters_play
from ......engine.choice_system import choose_character_effect


class PluckyPlayEffect:
    """Effect that makes each opponent choose one of their characters to deal 1 damage to."""
    
    def apply(self, target: Any, context: dict) -> Any:
        game_state = context.get('game_state')
        ability_owner = context.get('ability_owner')
        choice_manager = context.get('choice_manager')
        
        if not game_state or not ability_owner or not choice_manager:
            return target
        
        # For each opponent player
        for player in game_state.players:
            if player != ability_owner.controller:
                # Get characters for this opponent
                opponent_chars = [c for c in player.characters_in_play if hasattr(c, 'damage')]
                
                if opponent_chars:
                    # Create a choice for this specific opponent
                    current_player = player  # Capture the current player value
                    choice_effect = choose_character_effect(
                        prompt="Choose one of your characters to deal 1 damage to",
                        character_filter=lambda char, current_player=current_player: char.controller == current_player,
                        effect_on_selected=DAMAGE_1,
                        ability_name="PLUCKY PLAY",
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
        return "each opponent chooses a character to deal 1 damage to"


@register_named_ability("PLUCKY PLAY")
def create_plucky_play(character: Any, ability_data: dict):
    """PLUCKY PLAY - When you play this character, each opponent chooses one of their characters to deal 1 damage to.
    
    Implementation: Uses new choice system to let each opponent choose which character takes damage.
    """
    return quick_ability(
        "PLUCKY PLAY",
        character,
        when_enters_play(character),
        CONTROLLER,
        PluckyPlayEffect()
    )