"""SINISTER PLOT - This character gets +1 ◊ for each other Villain character you have in play."""

from typing import Any, Dict
from ..registry import register_named_ability
from ...composable_ability import quick_ability
from ...effects import StatefulConditionalEffect, ModifyStat, NoEffect
from ...target_selectors import SELF
from ...triggers import when_enters_play, when_leaves_play, or_conditions


def _calculate_villain_lore_bonus(character):
    """Create a condition function that calculates lore bonus based on other villain characters."""
    def condition(target: Any, context: Dict[str, Any]) -> bool:
        """Always return True - we'll apply the bonus dynamically in the effect."""
        return True
    return condition


def _get_villain_count(character):
    """Get the count of other villain characters the controller has in play."""
    def count_function(target: Any, context: Dict[str, Any]) -> int:
        """Count other villain characters in play for lore bonus calculation."""
        game_state = context.get('game_state')
        if not game_state or not hasattr(character, 'controller'):
            return 0
        
        controller = character.controller
        villain_count = 0
        
        # Count other villain characters controlled by this player
        for char in controller.characters_in_play:
            # Skip self
            if char == character:
                continue
                
            # Check if character has Villain subtype
            if hasattr(char, 'subtypes') and 'Villain' in char.subtypes:
                villain_count += 1
            elif hasattr(char, 'has_subtype') and char.has_subtype('Villain'):
                villain_count += 1
        
        return villain_count
    
    return count_function


@register_named_ability("SINISTER PLOT")
def create_sinister_plot(character: Any, ability_data: dict):
    """SINISTER PLOT - This character gets +1 ◊ for each other Villain character you have in play.
    
    Implementation: Dynamic stat modification based on other villain character count.
    """
    
    # Create a dynamic effect that applies lore bonus based on villain count
    class DynamicVillainLoreEffect:
        """Effect that applies variable lore bonus based on villain count."""
        
        def __init__(self, character, count_function):
            self.character = character
            self.count_function = count_function
            self.current_bonus = 0
        
        def apply(self, target: Any, context: Dict[str, Any]) -> Any:
            # Calculate new bonus
            new_bonus = self.count_function(target, context)
            
            # Apply the difference from current bonus
            lore_change = new_bonus - self.current_bonus
            
            if lore_change != 0:
                # Modify lore on the character
                if hasattr(self.character, 'lore'):
                    self.character.lore += lore_change
                elif hasattr(self.character, 'metadata'):
                    current_lore_bonus = self.character.metadata.get('sinister_plot_lore_bonus', 0)
                    self.character.metadata['sinister_plot_lore_bonus'] = current_lore_bonus + lore_change
                
                # Update tracking
                self.current_bonus = new_bonus
            
            return target
        
        def get_events(self, target: Any, context: Dict[str, Any], result: Any):
            """Generate events for the lore modification."""
            if self.current_bonus > 0:
                return [{
                    'type': 'stat_modified',
                    'target': self.character,
                    'stat': 'lore',
                    'bonus': self.current_bonus,
                    'source': 'SINISTER PLOT',
                    'additional_data': {
                        'villain_count': self.current_bonus
                    }
                }]
            return []
        
        def __str__(self) -> str:
            return f"gain +{self.current_bonus} lore from villains"
    
    # Create the dynamic effect
    villain_lore_effect = DynamicVillainLoreEffect(character, _get_villain_count(character))
    
    # Evaluate when characters enter or leave play (villain count changes)
    evaluation_trigger = or_conditions(
        when_enters_play(None),         # Any character enters play (could be villain)
        when_leaves_play(None),         # Any character leaves play (could be villain)
        when_enters_play(character)     # This character enters play (initial setup)
    )
    
    return quick_ability(
        "SINISTER PLOT",
        character,
        evaluation_trigger,
        SELF,
        villain_lore_effect
    )