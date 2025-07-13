"""Main composable ability class and listener system."""

from typing import List, Callable, Dict, Any, Optional, Set
from dataclasses import dataclass, field

from .effects import Effect
from .target_selectors import TargetSelector
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
        try:
            return self.trigger_condition(event_context)
        except Exception:
            # If trigger check fails, don't trigger
            return False
    
    def execute(self, event_context: EventContext) -> None:
        """Execute this listener's effect."""
        # Create context for target selection and effect application
        context = {
            'event_context': event_context,
            'source': event_context.source,
            'game_state': event_context.game_state,
            'player': event_context.player
        }
        
        # Add ability owner info if available
        if hasattr(event_context, 'additional_data') and event_context.additional_data:
            context.update(event_context.additional_data)
        
        # Select targets
        targets = self.target_selector.select(context)
        
        # Apply effect to each target, or to None if no targets (for effects like PreventEffect)
        if targets:
            for target in targets:
                try:
                    self.effect.apply(target, context)
                except Exception as e:
                    # Log error but don't crash the game
                    print(f"Error applying effect {self.effect} to target {target}: {e}")
        else:
            # For effects that don't need targets (like PreventEffect)
            try:
                self.effect.apply(None, context)
            except Exception as e:
                # Log error but don't crash the game
                print(f"Error applying effect {self.effect} with no target: {e}")
    
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
    
    # Compatibility methods for existing ability system
    def get_ability_type(self) -> str:
        """Get ability type for compatibility."""
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
        """Check if this ability allows targeting (for Ward compatibility)."""
        # Check if any listeners prevent targeting
        from .effects import PreventEffect
        for listener in self.listeners:
            if isinstance(listener.effect, PreventEffect):
                return False
        return True
    
    def can_sing_song(self, required_cost: int) -> bool:
        """Check if this ability allows singing songs (for Singer compatibility)."""
        from .effects import ModifySongCost
        for listener in self.listeners:
            if isinstance(listener.effect, ModifySongCost):
                # Singer X can sing songs that require cost X or less
                return required_cost <= listener.effect.singer_cost
        return False
    
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
            .add_trigger(trigger_condition, target_selector, effect))


# =============================================================================
# ADAPTATION HELPERS FOR EXISTING SYSTEM
# =============================================================================

def adapt_legacy_ability(legacy_ability: Any, character: Any) -> ComposableAbility:
    """Adapt a legacy ability to composable format."""
    # This would analyze the legacy ability and create equivalent composable version
    # For now, just create a basic wrapper
    return ComposableAbility(f"Adapted {legacy_ability.name}", character)