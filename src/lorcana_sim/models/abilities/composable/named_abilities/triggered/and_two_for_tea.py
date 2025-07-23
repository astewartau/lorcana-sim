"""AND TWO FOR TEA! - When you play this character, you may remove up to 2 damage from each of your Musketeer characters."""

from typing import Any, Dict, List
from ..registry import register_named_ability
from ...composable_ability import ComposableAbility
from ...effects import RemoveDamageEffect, ChoiceGenerationEffect, Effect
from ...target_selectors import SelfSelector
from ...triggers import when_enters_play


class MusketeerHealingSelector:
    """Target selector for a specific damaged Musketeer."""
    
    def __init__(self, musketeer: Any):
        self.musketeer = musketeer
        
    def select(self, context: Dict[str, Any]) -> List[Any]:
        """Return the specific musketeer."""
        return [self.musketeer]
        
    def get_choice_options(self, context: Dict[str, Any]) -> List[Any]:
        """Generate healing amount options for this Musketeer."""
        from lorcana_sim.engine.choice_system import ChoiceOption
        
        max_healing = min(2, self.musketeer.damage)
        
        # Create options for 0 to max healing
        options = []
        for amount in range(max_healing + 1):
            if amount == 0:
                desc = f"Remove no damage from {self.musketeer.name}"
            else:
                desc = f"Remove {amount} damage from {self.musketeer.name}"
            
            options.append(ChoiceOption(
                id=f"heal_{amount}",
                description=desc,
                target=self.musketeer,
                effect=RemoveDamageEffect(amount) if amount > 0 else None,
                data={'amount': amount}
            ))
        
        return options


class ApplyChosenHealingEffect(Effect):
    """Effect that applies the healing amount chosen by the player."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply the healing effect chosen by the player."""
        # Get the chosen option from the choice resolution context
        chosen_option_id = context.get('chosen_option_id')
        
        # Try other possible locations for the choice information
        if not chosen_option_id:
            choice_exec_context = context.get('_choice_execution_context')
            if choice_exec_context:
                chosen_option_id = choice_exec_context.get('chosen_option_id')
        
        if not chosen_option_id:
            # Apply optimal healing (up to 2 damage removal) as fallback
            # This matches the expected behavior for "remove up to 2 damage"
            if hasattr(target, 'damage') and target.damage > 0:
                amount = min(2, target.damage)
                target.damage = max(0, target.damage - amount)
            return target
            
        # Extract the healing amount from the option ID (e.g., "heal_2" -> 2)
        if chosen_option_id.startswith('heal_'):
            amount_str = chosen_option_id[5:]  # Remove "heal_" prefix
            amount = int(amount_str)
            if amount > 0:
                # Apply healing (reduce damage)
                if hasattr(target, 'damage'):
                    target.damage = max(0, target.damage - amount)
                
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for healing."""
        return []  # No special events needed
    
    def __str__(self) -> str:
        return "apply chosen healing amount"


class AndTwoForTeaEffect(Effect):
    """Effect that queues individual choice effects for each damaged Musketeer."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Queue choice effects for each damaged friendly Musketeer."""
        game_state = context.get('game_state')
        ability_owner = context.get('ability_owner')
        action_queue = context.get('action_queue')
        
        if not game_state or not ability_owner or not action_queue:
            return "Missing required context"
            
        # Find all damaged friendly Musketeers
        damaged_musketeers = self._find_damaged_musketeers(game_state, ability_owner)
        
        if not damaged_musketeers:
            return "No damaged Musketeers to heal"
        
        # Queue a ChoiceGenerationEffect for each damaged Musketeer
        for musketeer in reversed(damaged_musketeers):  # Reverse order for correct execution
            musketeer_selector = MusketeerHealingSelector(musketeer)
            healing_effect = ApplyChosenHealingEffect()
            
            choice_effect = ChoiceGenerationEffect(
                target_selector=musketeer_selector,
                follow_up_effect=healing_effect,
                ability_name=f"AND TWO FOR TEA! - {musketeer.name}"
            )
            
            # Queue the choice effect for this musketeer
            action_queue.enqueue(
                choice_effect,
                musketeer,
                context
            )
        
        return f"Queued healing choices for {len(damaged_musketeers)} Musketeers"
    
    def _find_damaged_musketeers(self, game_state: Any, ability_owner: Any) -> List[Any]:
        """Find all damaged friendly Musketeer characters."""
        damaged_musketeers = []
        controller = ability_owner.controller
        
        for player in game_state.players:
            if player == controller:
                for char in player.characters_in_play:
                    if (hasattr(char, 'has_subtype') and char.has_subtype('Musketeer') and 
                        hasattr(char, 'damage') and char.damage > 0):
                        damaged_musketeers.append(char)
                break
                
        return damaged_musketeers
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for queuing multiple choices."""
        return []  # No events needed for queueing effects
    
    def __str__(self) -> str:
        return "queue healing choices for damaged Musketeers"


@register_named_ability("AND TWO FOR TEA!")
def create_and_two_for_tea(character: Any, ability_data: dict):
    """AND TWO FOR TEA! - When you play this character, you may remove up to 2 damage from each of your Musketeer characters.
    
    Implementation: Creates sequential healing choices for each damaged Musketeer using ChoiceGenerationEffect.
    """
    return (ComposableAbility("AND TWO FOR TEA!", character)
            .add_trigger(
                trigger_condition=when_enters_play(character),
                target_selector=SelfSelector(),  # Target the tea character itself
                effect=AndTwoForTeaEffect(),
                name="AND TWO FOR TEA!"
            ))