"""Main composable ability class and listener system."""

from typing import List, Callable, Dict, Any, Optional, Set
from dataclasses import dataclass, field

from .effects import Effect
from .target_selectors import TargetSelector
from .conditional_effects import ActivationZone
from ....engine.event_system import GameEvent, EventContext


@dataclass
class ComposableListener:
    """Individual listener for a composable ability."""
    trigger_condition: Callable[[EventContext], bool]
    target_selector: TargetSelector
    effect: Effect
    priority: int = 0
    name: str = ""
    
    def should_trigger(self, event_context: EventContext) -> bool:
        """Check if this listener should trigger for the event."""
        result = self.trigger_condition(event_context)
        return result
    
    def execute(self, event_context: EventContext) -> None:
        """Execute this listener's effect."""
        
        # Create context for target selection and effect application
        context = {
            'event_context': event_context,
            'source': event_context.source,
            'game_state': event_context.game_state,
            'player': event_context.player,
            'ability_name': self.name,
            'ability_owner': event_context.source,  # Default fallback
            'action_queue': getattr(event_context, 'action_queue', None)
        }
        
        # Add ability owner info if available (this will override the fallback above)
        if hasattr(event_context, 'additional_data') and event_context.additional_data:
            context.update(event_context.additional_data)
        
        # Queue ability trigger effect instead of direct effect (TWO-STAGE EXECUTION)
        action_queue = context.get('action_queue')
        
        from ....engine.action_queue import ActionPriority
        from .effects import AbilityTriggerEffect, TargetedEffect, ChoiceGenerationEffect
            
        
        # Check if this is already a ChoiceGenerationEffect (new pattern)
        if isinstance(self.effect, ChoiceGenerationEffect):
            # For choice effects, queue the ChoiceGenerationEffect directly
            # It will handle creating the choice and queueing the follow-up effect
            trigger_effect = AbilityTriggerEffect(
                ability_name=self.name,
                source_card=context.get('ability_owner', event_context.source),
                actual_effect=self.effect  # This is already a ChoiceGenerationEffect
            )
        else:
            # For non-choice effects, resolve targets immediately and set up TargetedEffect
            targets = self.target_selector.select(context)
            context['resolved_targets'] = targets  # Pre-resolve targets for TargetedEffect
            
            targeted_effect = TargetedEffect(
                base_effect=self.effect,
                ability_name=self.name
            )
            
            trigger_effect = AbilityTriggerEffect(
                ability_name=self.name,
                source_card=context.get('ability_owner', event_context.source),
                actual_effect=targeted_effect
            )
        
        # Get full ability description for richer trigger messages
        full_description = self._get_full_ability_description(context)
        
        action_queue.enqueue(
            effect=trigger_effect,  # Queue the wrapper with the appropriate effect
            target=event_context.source,  # Use the ability owner as the initial target
            context=context,
            priority=ActionPriority.HIGH,  # Triggered effects go to front
            source_description=f"✨ Triggered {getattr(context.get('ability_owner'), 'name', 'Unknown')}'s {self.name}: {full_description}"
        )
    
    def _get_full_ability_description(self, context: dict) -> str:
        """Get the full description of this ability for trigger messages.
        
        Args:
            context: The context dict containing ability_owner and other data
            
        Returns:
            Full ability description if available, fallback to effect string
        """
        ability_owner = context.get('ability_owner')
        
        # First try: Get description from card's full_text
        if ability_owner and hasattr(ability_owner, 'full_text') and ability_owner.full_text:
            # Look for this specific ability name in the full_text
            full_text = ability_owner.full_text
            
            # Try to extract the specific ability description
            # Most cards have format like "ABILITY_NAME - Description text"
            if self.name in full_text:
                lines = full_text.split('\n')
                for line in lines:
                    if self.name in line and ' - ' in line:
                        # Extract text after the ability name and dash
                        parts = line.split(' - ', 1)
                        if len(parts) > 1:
                            return parts[1].strip()
        
        # Second try: Get description from named ability registry docstring
        try:
            from .named_abilities.registry import _NAMED_ABILITY_REGISTRY
            creator_func = _NAMED_ABILITY_REGISTRY.get(self.name)
            if creator_func and hasattr(creator_func, '__doc__') and creator_func.__doc__:
                doc = creator_func.__doc__.strip()
                if doc:
                    # Extract the first line which contains the ability description
                    first_line = doc.split('\n')[0].strip()
                    # Remove the ability name prefix if present (e.g., "THAT'S BETTER - ")
                    if self.name in first_line and ' - ' in first_line:
                        parts = first_line.split(' - ', 1)
                        if len(parts) > 1:
                            return parts[1].strip()
                    return first_line
        except ImportError:
            # Registry might not be available in all contexts
            pass
        
        # Fallback: Use the effect string representation
        return str(self.effect)
    
    def relevant_events(self) -> List[GameEvent]:
        """Get list of events this listener cares about."""
        # Return only events this trigger actually cares about
        if hasattr(self.trigger_condition, 'get_relevant_events'):
            return self.trigger_condition.get_relevant_events()
        
        # Fallback: analyze the trigger condition to determine relevant events
        if hasattr(self.trigger_condition, 'event_type'):
            return [self.trigger_condition.event_type]
        
        # Conservative fallback - return empty list to avoid spurious triggers
        return []
    
    def __str__(self) -> str:
        name_part = f"{self.name}: " if self.name else ""
        return f"{name_part}{self.target_selector} → {self.effect}"


class ComposableAbility:
    """Main composable ability class that supports fluent interface."""
    
    def __init__(self, name: str, character: Any):
        self.name = name
        self.character = character
        self.listeners: List[ComposableListener] = []
        self._event_manager: Optional[Any] = None
        self._registered_events: Set[GameEvent] = set()
        self.activation_zones: Set[ActivationZone] = {ActivationZone.PLAY}  # Default to play only
    
    def add_trigger(self, 
                   trigger_condition: Callable[[EventContext], bool],
                   target_selector: TargetSelector,
                   effect: Effect,
                   priority: int = 0,
                   name: str = "") -> 'ComposableAbility':
        """Add a trigger to this ability (fluent interface)."""
        listener = ComposableListener(
            trigger_condition=trigger_condition,
            target_selector=target_selector,
            effect=effect,
            priority=priority,
            name=name or f"Trigger{len(self.listeners) + 1}"
        )
        self.listeners.append(listener)
        
        # If already registered with event manager, register this new listener
        if self._event_manager:
            self._register_listener(listener)
        
        return self
    
    def active_in_zones(self, *zones: ActivationZone) -> 'ComposableAbility':
        """Set which zones this ability can be active in (fluent interface)."""
        self.activation_zones = set(zones)
        return self
    
    def handle_event(self, event_context: EventContext) -> None:
        """Handle an incoming event."""
        # Add ability owner to context additional_data
        if not event_context.additional_data:
            event_context.additional_data = {}
        event_context.additional_data['ability_owner'] = self.character
        
        # Sort listeners by priority (higher priority first)
        sorted_listeners = sorted(self.listeners, key=lambda l: l.priority, reverse=True)
        
        for listener in sorted_listeners:
            if listener.should_trigger(event_context):
                listener.execute(event_context)
                
                # Check if event was prevented
                if event_context.additional_data and event_context.additional_data.get('prevented', False):
                    break  # Stop processing if event was prevented
    
    def register_with_event_manager(self, event_manager) -> None:
        """Register this ability with the event manager."""
        # Don't register again if already registered with the same event manager
        if self._event_manager is event_manager:
            return
            
        self._event_manager = event_manager
        
        # Use the new composable ability registration if available
        if hasattr(event_manager, 'register_composable_ability'):
            event_manager.register_composable_ability(self)
        else:
            # Fallback to listener-by-listener registration
            for listener in self.listeners:
                self._register_listener(listener)
    
    def _register_listener(self, listener: ComposableListener) -> None:
        """Register a single listener with the event manager."""
        if not self._event_manager:
            return
            
        relevant_events = listener.relevant_events()
        for event in relevant_events:
            if event not in self._registered_events:
                # Register the ability itself as the listener
                # The event manager will call our handle_event method
                if hasattr(self._event_manager, 'register_ability_listener'):
                    self._event_manager.register_ability_listener(event, self)
                elif hasattr(self._event_manager, 'register_listener'):
                    self._event_manager.register_listener(event, self)
                self._registered_events.add(event)
    
    def unregister_from_event_manager(self) -> None:
        """Unregister this ability from the event manager."""
        if not self._event_manager:
            return
            
        # Use the new composable ability unregistration if available
        if hasattr(self._event_manager, 'unregister_composable_ability'):
            self._event_manager.unregister_composable_ability(self)
        else:
            # Fallback to old method
            for event in self._registered_events:
                if hasattr(self._event_manager, 'unregister_ability_listener'):
                    self._event_manager.unregister_ability_listener(event, self)
                elif hasattr(self._event_manager, 'unregister_listener'):
                    self._event_manager.unregister_listener(event, self)
        
        self._registered_events.clear()
        self._event_manager = None
    
    def get_ability_type(self) -> str:
        """Get ability type."""
        return "composable"
    
    def modifies_game_rules(self) -> bool:
        """Check if this ability modifies game rules."""
        # Check if any listeners have prevention or modification effects
        from .effects import PreventEffect, ModifyDamage, ForceRetarget
        for listener in self.listeners:
            if isinstance(listener.effect, (PreventEffect, ModifyDamage, ForceRetarget)):
                return True
        return False
    
    def allows_ability_targeting(self, source_type: str, target_type: str) -> bool:
        """Check if this ability allows targeting."""
        # Check if any listeners prevent targeting
        from .effects import PreventEffect
        for listener in self.listeners:
            if isinstance(listener.effect, PreventEffect):
                return False
        return True
    
    def can_sing_song(self, required_cost: int) -> bool:
        """Check if this ability allows singing songs."""
        from .effects import ModifySongCost
        for listener in self.listeners:
            if isinstance(listener.effect, ModifySongCost):
                # Singer X can sing songs that require cost X or less
                return required_cost <= listener.effect.singer_cost
        return False
    
    def choice_effect(self, 
                     trigger_condition: Callable[[EventContext], bool],
                     target_selector: TargetSelector,
                     effect: Effect,
                     priority: int = 0,
                     name: str = "") -> 'ComposableAbility':
        """Add a choice-based trigger that uses the new architectural pattern (fluent interface)."""
        from .effects import ChoiceGenerationEffect, TargetedEffect
        
        # Create the targeted effect that will be queued after choice resolution
        targeted_effect = TargetedEffect(
            base_effect=effect,
            ability_name=name or f"ChoiceEffect{len(self.listeners) + 1}"
        )
        
        # Create the choice generation effect that handles the choice creation
        choice_effect = ChoiceGenerationEffect(
            target_selector=target_selector,
            follow_up_effect=targeted_effect,
            ability_name=name or f"ChoiceEffect{len(self.listeners) + 1}"
        )
        
        # Add as a normal trigger, but with the choice generation effect
        listener = ComposableListener(
            trigger_condition=trigger_condition,
            target_selector=target_selector,  # This will be used to generate choices
            effect=choice_effect,
            priority=priority,
            name=name or f"ChoiceEffect{len(self.listeners) + 1}"
        )
        self.listeners.append(listener)
        
        # If already registered with event manager, register this new listener
        if self._event_manager:
            self._register_listener(listener)
        
        return self
    
    def __str__(self) -> str:
        return f"{self.name} (Composable: {len(self.listeners)} triggers)"
    
    def __repr__(self) -> str:
        listeners_str = "\n".join(f"  - {listener}" for listener in self.listeners)
        return f"ComposableAbility({self.name}):\n{listeners_str}"


# =============================================================================
# BUILDER PATTERNS FOR FLUENT INTERFACE
# =============================================================================

class AbilityBuilder:
    """Builder for creating composable abilities with fluent interface."""
    
    def __init__(self, name: str):
        self.name = name
        self.character = None
        self.triggers = []
    
    def for_character(self, character: Any) -> 'AbilityBuilder':
        """Set the character this ability belongs to."""
        self.character = character
        return self
    
    def when(self, trigger_condition: Callable) -> 'TriggerBuilder':
        """Start building a trigger."""
        return TriggerBuilder(self, trigger_condition)
    
    def build(self) -> ComposableAbility:
        """Build the final ability."""
        if not self.character:
            raise ValueError("Character must be set with for_character()")
        
        ability = ComposableAbility(self.name, self.character)
        for trigger_data in self.triggers:
            ability.add_trigger(**trigger_data)
        return ability


class TriggerBuilder:
    """Builder for individual triggers."""
    
    def __init__(self, ability_builder: AbilityBuilder, trigger_condition: Callable):
        self.ability_builder = ability_builder
        self.trigger_condition = trigger_condition
        self.target_selector = None
        self.effect = None
        self.priority = 0
        self.name = ""
    
    def target(self, selector: TargetSelector) -> 'TriggerBuilder':
        """Set the target selector."""
        self.target_selector = selector
        return self
    
    def apply(self, effect: Effect) -> 'AbilityBuilder':
        """Set the effect and return to ability builder."""
        self.effect = effect
        
        if not self.target_selector:
            raise ValueError("Target selector must be set with target()")
        
        self.ability_builder.triggers.append({
            'trigger_condition': self.trigger_condition,
            'target_selector': self.target_selector,
            'effect': self.effect,
            'priority': self.priority,
            'name': self.name
        })
        
        return self.ability_builder
    
    def with_priority(self, priority: int) -> 'TriggerBuilder':
        """Set the priority for this trigger."""
        self.priority = priority
        return self
    
    def named(self, name: str) -> 'TriggerBuilder':
        """Set a name for this trigger."""
        self.name = name
        return self


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def ability(name: str) -> AbilityBuilder:
    """Start building a composable ability."""
    return AbilityBuilder(name)


def quick_ability(name: str, character: Any, trigger_condition: Callable, 
                  target_selector: TargetSelector, effect: Effect) -> ComposableAbility:
    """Quick way to create a simple composable ability."""
    return (ComposableAbility(name, character)
            .add_trigger(trigger_condition, target_selector, effect, name=name))


