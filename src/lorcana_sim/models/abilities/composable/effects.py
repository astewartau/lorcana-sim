"""Composable effect system for abilities."""

from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from ....utils.logging_config import get_game_logger

logger = get_game_logger(__name__)


class DamageType(Enum):
    """Types of damage that can be dealt."""
    CHALLENGE = "challenge"      # Damage from character challenges
    ABILITY = "ability"          # Damage from ability effects
    DIRECT = "direct"           # Direct damage (unmodifiable)

class Effect(ABC):
    """Base class for composable effects."""
    
    @abstractmethod
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply this effect to a target."""
        pass
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """
        Get the events that this effect will emit after execution.
        
        Args:
            target: The target the effect was applied to
            context: The context the effect was applied with
            result: The result returned by apply()
            
        Returns:
            List of event dictionaries to be emitted
        """
        # Default implementation returns empty list
        # Subclasses should override to declare their events
        return []
    
    def __add__(self, other: 'Effect') -> 'CompositeEffect':
        """Combine effects with +"""
        if isinstance(other, CompositeEffect):
            return CompositeEffect([self] + other.effects)
        return CompositeEffect([self, other])
    
    def __mul__(self, count: int) -> 'RepeatedEffect':
        """Repeat effect with *"""
        return RepeatedEffect(self, count)
    
    def __or__(self, other: 'Effect') -> 'ChoiceEffect':
        """Create choice between effects with |"""
        return ChoiceEffect([self, other])
    
    def __str__(self) -> str:
        return self.__class__.__name__


class AbilityTriggerEffect(Effect):
    """Effect that represents an ability triggering, which then queues the actual effect."""
    
    def __init__(self, ability_name: str, source_card: Any, actual_effect: Effect):
        self.ability_name = ability_name
        self.source_card = source_card
        self.actual_effect = actual_effect
    
    def apply(self, target: Any, context: Dict[str, Any]) -> None:
        """Queue the actual effect for the next message call."""
        action_queue = context.get('action_queue')
        if action_queue:
            # Import here to avoid circular imports
            from ....engine.action_queue import ActionPriority
            # Queue the real effect with ability attribution
            source_name = getattr(self.source_card, 'name', 'Unknown')
            action_queue.enqueue(
                effect=self.actual_effect,
                target=target,
                context=context,
                priority=ActionPriority.HIGH,
                source_description=f"🔮 {source_name}'s {self.ability_name}"
            )
        else:
            # Fallback: apply immediately if no action_queue available
            self.actual_effect.apply(target, context)
    
    def __str__(self) -> str:
        return f"ability trigger"


class CompositeEffect(Effect):
    """Multiple effects applied in sequence."""
    
    def __init__(self, effects: List[Effect]):
        self.effects = effects
        self._sub_results = []  # Track results from each sub-effect
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        result = target
        self._sub_results = []
        for effect in self.effects:
            result = effect.apply(result, context)
            self._sub_results.append((effect, result))
        return result
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Aggregate events from all sub-effects."""
        all_events = []
        # Use the stored sub-results if available, otherwise re-calculate
        if self._sub_results:
            for effect, sub_result in self._sub_results:
                events = effect.get_events(target, context, sub_result)
                all_events.extend(events)
        else:
            # Fallback: use final result for all effects
            for effect in self.effects:
                events = effect.get_events(target, context, result)
                all_events.extend(events)
        return all_events
    
    def __str__(self) -> str:
        return " + ".join(str(effect) for effect in self.effects)


class RepeatedEffect(Effect):
    """Effect repeated N times."""
    
    def __init__(self, effect: Effect, count: int):
        self.effect = effect
        self.count = count
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        result = target
        for _ in range(self.count):
            result = self.effect.apply(result, context)
        return result
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events from repeated effect."""
        all_events = []
        for _ in range(self.count):
            events = self.effect.get_events(target, context, result)
            all_events.extend(events)
        return all_events
    
    def __str__(self) -> str:
        return f"({self.effect}) * {self.count}"


class ChoiceEffect(Effect):
    """Player chooses between effects."""
    
    def __init__(self, effects: List[Effect]):
        self.effects = effects
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # TODO: Integrate with decision system
        # For now, just apply first effect
        return self.effects[0].apply(target, context)
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events from chosen effect."""
        # For now, return events from first effect
        return self.effects[0].get_events(target, context, result)
    
    def __str__(self) -> str:
        return " | ".join(str(effect) for effect in self.effects)


class ConditionalEffect(Effect):
    """Apply effect only if condition is met."""
    
    def __init__(self, condition: Callable[[Any, Dict], bool], effect: Effect, else_effect: Effect = None):
        self.condition = condition
        self.effect = effect
        self.else_effect = else_effect
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if self.condition(target, context):
            return self.effect.apply(target, context)
        elif self.else_effect:
            return self.else_effect.apply(target, context)
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events from conditional effect."""
        if self.condition(target, context):
            return self.effect.get_events(target, context, result)
        elif self.else_effect:
            return self.else_effect.get_events(target, context, result)
        return []
    
    def __str__(self) -> str:
        else_str = f" else {self.else_effect}" if self.else_effect else ""
        return f"if condition then {self.effect}{else_str}"


class StatefulConditionalEffect(Effect):
    """Conditional effect that tracks state to avoid redundant applications."""
    
    def __init__(self, 
                 condition: Callable[[Any, Dict], bool], 
                 true_effect: Effect,
                 false_effect: Effect,
                 state_key: str):
        self.condition = condition
        self.true_effect = true_effect
        self.false_effect = false_effect
        self.state_key = state_key
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        should_be_active = self.condition(target, context)
        current_state = context.get(f'conditional_state_{self.state_key}', None)
        
        # Only apply effects if state changed
        if should_be_active and current_state != 'active':
            context[f'conditional_state_{self.state_key}'] = 'active'
            return self.true_effect.apply(target, context)
        elif not should_be_active and current_state != 'inactive':
            context[f'conditional_state_{self.state_key}'] = 'inactive'
            return self.false_effect.apply(target, context)
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events from stateful conditional effect."""
        should_be_active = self.condition(target, context)
        current_state = context.get(f'conditional_state_{self.state_key}', None)
        
        # Only return events if state changed
        if should_be_active and current_state != 'active':
            return self.true_effect.get_events(target, context, result)
        elif not should_be_active and current_state != 'inactive':
            return self.false_effect.get_events(target, context, result)
        
        return []
    
    def __str__(self) -> str:
        return f"stateful conditional: {self.true_effect} vs {self.false_effect}"


# =============================================================================
# TEMPORARY ABILITY INFRASTRUCTURE FOR AUTO-EXPIRING ABILITIES
# =============================================================================

class TemporaryAbility:
    """Base class for temporary abilities that auto-expire via event system."""
    
    def __init__(self, name: str, target: Any, expiration_trigger: 'GameEvent'):
        """Initialize temporary ability.
        
        Args:
            name: Name of the temporary ability
            target: Character that has this temporary ability
            expiration_trigger: GameEvent that causes this ability to expire
        """
        self.name = name
        self.target = target
        self.character = target  # Alias for compatibility with ComposableAbility interface
        self.expiration_trigger = expiration_trigger
        self._event_manager = None
        self._registered = False
        
        # Zone validation for compatibility with ComposableAbility interface
        from .activation_zones import ActivationZone
        self.activation_zones = {ActivationZone.PLAY}  # Default to play only
        
        # Create listeners for compatibility with GameEventManager
        self.listeners = [TemporaryAbilityListener(self)]
    
    def get_relevant_events(self) -> List['GameEvent']:
        """Return events this ability cares about (required by GameEventManager)."""
        events = [self.expiration_trigger]
        
        # Add ability-specific events (override in subclasses)
        ability_events = self.get_ability_events()
        if ability_events:
            events.extend(ability_events)
            
        return events
    
    def get_ability_events(self) -> List['GameEvent']:
        """Override in subclasses to specify events the ability responds to."""
        return []
    
    def register_with_event_manager(self, event_manager) -> None:
        """Register this temporary ability with the event manager."""
        if not self._registered:
            self._event_manager = event_manager
            event_manager.register_composable_ability(self)
            self._registered = True
    
    def handle_event(self, event_context) -> None:
        """Handle event triggering - called by GameEventManager."""
        if event_context.event_type == self.expiration_trigger:
            self._expire(event_context)
        elif self.should_trigger(event_context):
            self.apply_effect(event_context)
    
    def _expire(self, event_context) -> None:
        """Remove this ability when expiration event occurs."""
        if self.target and hasattr(self.target, 'composable_abilities'):
            # Remove from target's ability list
            if self in self.target.composable_abilities:
                self.target.composable_abilities.remove(self)
        
        # Unregister from event system
        if self._event_manager and self._registered:
            # Remove from all event listener lists
            for event_type in self.get_relevant_events():
                if event_type in self._event_manager._composable_listeners:
                    if self in self._event_manager._composable_listeners[event_type]:
                        self._event_manager._composable_listeners[event_type].remove(self)
            
            # Remove from registered abilities set
            if self in self._event_manager._registered_abilities:
                self._event_manager._registered_abilities.remove(self)
            
            self._registered = False
    
    def should_trigger(self, event_context) -> bool:
        """Override in subclasses to define when this ability triggers."""
        return False
    
    def apply_effect(self, event_context) -> None:
        """Override in subclasses to define the ability's effect."""
        pass
    
    def __str__(self) -> str:
        return f"TemporaryAbility({self.name})"


class TemporaryAbilityListener:
    """Lightweight listener that delegates to TemporaryAbility methods."""
    
    def __init__(self, temporary_ability: TemporaryAbility):
        self.temporary_ability = temporary_ability
    
    def should_trigger(self, event_context) -> bool:
        """Delegate to the temporary ability's should_trigger method."""
        return (event_context.event_type == self.temporary_ability.expiration_trigger or 
                self.temporary_ability.should_trigger(event_context))
    
    def relevant_events(self) -> List['GameEvent']:
        """Get relevant events from the temporary ability."""
        return self.temporary_ability.get_relevant_events()


class TemporaryChallengerAbility(TemporaryAbility):
    """Temporary ability that grants Challenger +X until expiration."""
    
    def __init__(self, strength_bonus: int, target: Any, expiration_trigger: 'GameEvent'):
        """Initialize temporary Challenger ability.
        
        Args:
            strength_bonus: Amount of strength bonus to grant during challenges
            target: Character that has this temporary ability
            expiration_trigger: GameEvent that causes this ability to expire
        """
        super().__init__(f"Challenger +{strength_bonus}", target, expiration_trigger)
        self.strength_bonus = strength_bonus
    
    def get_ability_events(self) -> List['GameEvent']:
        """Return events this challenger ability responds to."""
        from ....engine.event_system import GameEvent
        return [GameEvent.CHARACTER_CHALLENGES]
    
    def should_trigger(self, event_context) -> bool:
        """Trigger when this character initiates a challenge."""
        from ....engine.event_system import GameEvent
        
        # Only trigger on CHARACTER_CHALLENGES events where this character is the attacker
        if event_context.event_type != GameEvent.CHARACTER_CHALLENGES:
            return False
        
        # Check if this character is the one initiating the challenge
        attacker = event_context.additional_data.get('attacker') if event_context.additional_data else None
        return attacker is self.target
    
    def apply_effect(self, event_context) -> None:
        """Apply the challenger bonus to combat calculation."""
        if event_context.additional_data:
            # Get the challenge context
            challenge_context = event_context.additional_data.get('context', {})
            
            # Add our bonus to the attacker's strength for this challenge
            if 'attacker' in challenge_context and challenge_context['attacker'] is self.target:
                # Modify the damage calculation
                current_damage = challenge_context.get('damage_to_defender', 0)
                challenge_context['damage_to_defender'] = current_damage + self.strength_bonus
                
                # Also ensure the challenge result reflects this
                challenge_result = event_context.additional_data.get('challenge_result', {})
                if challenge_result and 'damage_to_defender' in challenge_result:
                    challenge_result['damage_to_defender'] += self.strength_bonus
    
    def __str__(self) -> str:
        return f"Challenger +{self.strength_bonus} (temporary)"


# =============================================================================
# ATOMIC EFFECTS FOR ALL EXISTING ABILITIES
# =============================================================================

class StatModification(Effect):
    """Modify a character's stat (for Support, Resist, etc.)."""
    
    def __init__(self, stat: str, amount: int, duration: str = "permanent"):
        self.stat = stat
        self.amount = amount
        self.duration = duration
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # If target is None, this effect cannot be applied (no valid targets)
        if target is None:
            return None
        
        if hasattr(target, f'modify_{self.stat}'):
            getattr(target, f'modify_{self.stat}')(self.amount)
        elif self.stat == "damage" and self.amount < 0:
            # Healing (negative damage)
            if hasattr(target, 'heal_damage'):
                target.heal_damage(-self.amount)
        else:
            # Direct modification as fallback
            current_value = getattr(target, self.stat, 0)
            setattr(target, self.stat, current_value + self.amount)
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for stat modification."""
        if result is None:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.STAT_MODIFIED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'stat_name': self.stat,
                'stat_change': self.amount,
                'duration': self.duration,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        sign = "+" if self.amount >= 0 else ""
        return f"{self.stat} {sign}{self.amount} ({self.duration})"


class DrawCards(Effect):
    """Draw cards effect."""
    
    def __init__(self, count: int):
        self.count = count
        self._drawn_cards = []
        self._player = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # If target is already a player/controller, use it directly
        if hasattr(target, 'draw_cards'):
            self._player = target
            self._drawn_cards = target.draw_cards(self.count)
        else:
            # Otherwise get controller from target
            controller = getattr(target, 'controller', None)
            if not controller:
                # Fallback: get controller from source character
                source = context.get('source')
                if source and hasattr(source, 'controller'):
                    controller = source.controller
            
            if controller and hasattr(controller, 'draw_cards'):
                self._player = controller
                self._drawn_cards = controller.draw_cards(self.count)
        
        # Mark draw as completed if this was the mandatory draw
        game_state = context.get('game_state')
        if game_state and context.get('mandatory_draw'):
            game_state.card_drawn_this_turn = True
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get CARD_DRAWN events for each card drawn."""
        if not self._player or not self._drawn_cards:
            return []
        
        # Filter out None values
        actual_cards = [card for card in self._drawn_cards if card is not None]
        if not actual_cards:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        # Create one event per card drawn (for true atomicity)
        events = []
        for card in actual_cards:
            events.append({
                'type': GameEvent.CARD_DRAWN,
                'player': self._player,
                'source': context.get('source') or context.get('ability_owner'),
                'additional_data': {
                    'card_drawn': card,
                    'card_name': card.name if hasattr(card, 'name') else 'Unknown Card',
                    'source': 'ability',
                    'ability_name': context.get('ability_name', 'Unknown'),
                    'hand_size_after': len(self._player.hand),
                    'deck_size_after': len(self._player.deck)
                }
            })
        
        return events
    
    def __str__(self) -> str:
        return f"draw {self.count} card{'s' if self.count != 1 else ''}"


class DamageEffect(Effect):
    """Deal damage to a character."""
    
    def __init__(self, target, amount: int, source=None, damage_type: DamageType = DamageType.DIRECT):
        self.target = target
        self.amount = amount
        self.source = source
        self.damage_type = damage_type
        self._actual_damage = 0
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Use the stored target, not the passed target
        actual_target = self.target
        
        if not hasattr(actual_target, 'damage'):
            logger.warning(f"Target {actual_target} cannot take damage")
            return target
        
        # Get event manager from context
        event_manager = context.get('event_manager')
        if not event_manager:
            # Fallback: apply damage directly without event
            self._actual_damage = max(0, self.amount)
            actual_target.damage += self._actual_damage
            return target
        
        # Create damage event for modification
        from ....engine.event_system import GameEvent, EventContext
        damage_context = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=actual_target,
            source=self.source,
            player=actual_target.controller if hasattr(actual_target, 'controller') else None,
            game_state=context.get('game_state'),
            additional_data={
                'damage': self.amount,
                'damage_type': self.damage_type,
                'damage_source': self.source,
                'modifiable': True
            }
        )
        
        # Trigger event - abilities like Resist can modify the damage
        event_manager.trigger_event(damage_context)
        
        # Apply the potentially modified damage
        final_damage = max(0, damage_context.additional_data.get('damage', self.amount))
        self._actual_damage = final_damage
        actual_target.damage += final_damage
        
        # Log damage application
        logger.debug(f"{actual_target} took {final_damage} damage (from {self.amount})")
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for damage dealt."""
        if self._actual_damage <= 0:
            return []
        
        return [{
            'type': GameEvent.DAMAGE_DEALT,
            'source': self.source,
            'target': self.target,
            'additional_data': {
                'damage_amount': self._actual_damage,
                'damage_type': self.damage_type,
                'ability_name': context.get('ability_name', 'Direct Damage')
            }
        }]
    
    def __str__(self) -> str:
        return f"deal {self.amount} damage"


class BanishCharacter(Effect):
    """Banish target character."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the character's controller and banish through player
        if hasattr(target, 'controller') and target.controller:
            controller = target.controller
            if hasattr(controller, 'banish_character'):
                controller.banish_character(target)
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get CHARACTER_BANISHED event for this effect."""
        if not hasattr(target, 'controller'):
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CHARACTER_BANISHED,
            'source': target,
            'target': target,
            'player': target.controller,
            'additional_data': {
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'banishment_cause': 'ability',
                'ability_name': context.get('ability_name', 'Unknown'),
                'choice_manager': context.get('choice_manager'),
                'action_queue': context.get('action_queue')
            }
        }]
    
    def __str__(self) -> str:
        return "banish character"


class ReturnToHand(Effect):
    """Return target to owner's hand."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'controller') and hasattr(target.controller, 'return_to_hand'):
            target.controller.return_to_hand(target)
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get CARD_RETURNED_TO_HAND event for this effect."""
        if not hasattr(target, 'controller'):
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CARD_RETURNED_TO_HAND,
            'source': target,
            'player': target.controller,
            'additional_data': {
                'card_name': target.name if hasattr(target, 'name') else 'Unknown Card',
                'from_zone': 'play',  # Assuming from play, could be enhanced
                'source': 'ability',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "return to hand"


class DiscardCard(Effect):
    """Discard target card from hand."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the controller who owns this card
        controller = self._get_controller(target, context)
        
        if controller and hasattr(controller, 'hand') and target in controller.hand:
            controller.hand.remove(target)
            controller.discard_pile.append(target)
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get the CARD_DISCARDED event for this effect."""
        controller = self._get_controller(target, context)
        
        if not controller:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        card_name = target.name if hasattr(target, 'name') else 'Unknown Card'
        
        return [{
            'type': GameEvent.CARD_DISCARDED,
            'player': controller,
            'source': target,
            'additional_data': {
                'card_discarded': target,
                'card_name': card_name,
                'source': 'ability',
                'ability_name': context.get('ability_name', 'Unknown'),
                'hand_size_after': len(controller.hand),
                'discard_size_after': len(controller.discard_pile)
            }
        }]
    
    def _get_controller(self, target: Any, context: Dict[str, Any]) -> Any:
        """Helper to get the controller of a card."""
        # First try to get controller from target
        if hasattr(target, 'controller') and target.controller:
            return target.controller
        
        # If target doesn't have controller, get from context
        # Try ability owner first, then player
        ability_owner = context.get('ability_owner')
        if ability_owner and hasattr(ability_owner, 'controller'):
            return ability_owner.controller
        
        # Try getting player directly from context
        return context.get('player')
    
    def __str__(self) -> str:
        return "discard card"


class ExertCharacter(Effect):
    """Exert a character."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'exerted'):
            target.exerted = True
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for exerting character."""
        if not hasattr(target, 'controller'):
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CHARACTER_EXERTED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller,
            'additional_data': {
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "exert character"


class PreventEffect(Effect):
    """Prevent an effect (for Ward)."""
    
    def __init__(self, effect_type: str = "targeting"):
        self.effect_type = effect_type
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Set prevention flag in context
        event_context = context.get('event_context')
        if event_context and hasattr(event_context, 'prevent'):
            event_context.prevent()
        elif event_context:
            event_context.additional_data = event_context.additional_data or {}
            event_context.additional_data['prevented'] = True
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for preventing effect."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.EFFECT_PREVENTED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'effect_type': self.effect_type,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"prevent {self.effect_type}"


class ModifyDamage(Effect):
    """Modify incoming damage (for Resist)."""
    
    def __init__(self, reduction: int):
        self.reduction = reduction
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        event_context = context.get('event_context')
        if event_context and 'damage' in event_context.additional_data:
            current_damage = event_context.additional_data['damage']
            event_context.additional_data['damage'] = max(0, current_damage - self.reduction)
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for damage modification."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.DAMAGE_MODIFIED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'damage_reduction': self.reduction,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"reduce damage by {self.reduction}"


class ForceRetarget(Effect):
    """Force retargeting (for Bodyguard)."""
    
    def __init__(self, new_target_selector: Optional['TargetSelector'] = None):
        self.new_target_selector = new_target_selector
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        event_context = context.get('event_context')
        if event_context:
            # If we have a specific target selector, use it
            if self.new_target_selector:
                new_targets = self.new_target_selector.select(context)
                if new_targets:
                    event_context.target = new_targets[0]
            else:
                # Otherwise, retarget to self (typical Bodyguard behavior)
                event_context.target = context.get('source')
            
            event_context.additional_data = event_context.additional_data or {}
            event_context.additional_data['retargeted'] = True
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for force retargeting."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        event_context = context.get('event_context')
        new_target = event_context.target if event_context else None
        
        return [{
            'type': GameEvent.TARGET_CHANGED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'new_target': new_target.name if hasattr(new_target, 'name') else str(new_target),
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "force retarget"


class GrantProperty(Effect):
    """Grant a property to target (for Rush, Evasive checks)."""
    
    def __init__(self, property_name: str, value: Any = True):
        self.property_name = property_name
        self.value = value
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'metadata'):
            target.metadata[self.property_name] = self.value
        else:
            # Create metadata dict if it doesn't exist
            target.metadata = {self.property_name: self.value}
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for granting property."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.PROPERTY_GRANTED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'property_name': self.property_name,
                'property_value': self.value,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"grant {self.property_name}"


class RemoveProperty(Effect):
    """Remove a property from target."""
    
    def __init__(self, property_name: str):
        self.property_name = property_name
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'metadata') and self.property_name in target.metadata:
            del target.metadata[self.property_name]
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        return [{
            'type': GameEvent.PROPERTY_REMOVED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'property_name': self.property_name,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"remove {self.property_name}"


class TargetedEffect(Effect):
    """Effect that operates on pre-selected targets only. Never generates choices."""
    
    def __init__(self, base_effect, ability_name="Unknown"):
        self.base_effect = base_effect
        self.ability_name = ability_name
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply effect to pre-resolved targets only."""
        logger.debug("TargetedEffect.apply called for ability {self.ability_name}")
        # This effect should ONLY be called when targets are already resolved
        targets = context.get('resolved_targets')
        
        if targets is None:
            raise ValueError(f"TargetedEffect for {self.ability_name} called without resolved targets")
        
        logger.debug("Using resolved targets: {targets}")
        
        # Note: choice_manager should always be present via event_context.additional_data
        # If it's missing, that indicates a bug in the event emission logic
        
        # Apply base effect to all selected targets
        result = target
        logger.debug("Applying base effect {self.base_effect} to {len(targets)} targets")
        for selected_target in targets:
            # Skip None targets (when player chose "no target")
            if selected_target is not None:
                logger.debug("Applying effect to target: {selected_target}")
                result = self.base_effect.apply(selected_target, context)
                logger.debug("Effect applied successfully")
        
        logger.debug("TargetedEffect completed, returning: {result}")
        return result
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for targeted effect."""
        targets = context.get('resolved_targets', [])
        
        if not targets:
            return []
        
        # Aggregate events from base effect for all targets
        all_events = []
        for selected_target in targets:
            if hasattr(self.base_effect, 'get_events'):
                events = self.base_effect.get_events(selected_target, context, result)
                all_events.extend(events)
        
        return all_events
    
    def __str__(self) -> str:
        return f"apply to selected targets: {self.base_effect}"


class StoreTargetEffect(Effect):
    """Effect that stores a selected target for later use."""
    
    def __init__(self, selected_target):
        self.selected_target = selected_target
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Store the selected target in the game state for later use."""
        logger.debug("StoreTargetEffect.apply called with selected_target: {self.selected_target}")
        game_state = context.get('game_state')
        if game_state:
            if not hasattr(game_state, 'selected_targets'):
                game_state.selected_targets = []
            game_state.selected_targets.append(self.selected_target)
            logger.debug("Stored target {self.selected_target} in game_state.selected_targets, now has {len(game_state.selected_targets)} targets")
        else:
            logger.debug("No game_state found in context")
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for target storage."""
        return []
    
    def __str__(self) -> str:
        return f"store target {getattr(self.selected_target, 'name', str(self.selected_target))}"


class NoEffect(Effect):
    """No effect (for passive abilities that just modify rules)."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for no effect."""
        return []
    
    def __str__(self) -> str:
        return "no effect"


class ModifySongCost(Effect):
    """Modify song singing cost (for Singer)."""
    
    def __init__(self, singer_cost: int):
        self.singer_cost = singer_cost
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        event_context = context.get('event_context')
        if event_context and event_context.additional_data:
            # Mark that this character can sing songs
            event_context.additional_data['can_sing'] = True
            event_context.additional_data['singer_cost'] = self.singer_cost
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for song cost modification."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.SINGING_COST_MODIFIED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'singer_cost': self.singer_cost,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"can sing songs (cost {self.singer_cost})"


# =============================================================================
# PRE-BUILT EFFECTS FOR COMMON USE CASES
# =============================================================================

# Stat modifications
LORE_PLUS_1 = StatModification("lore", 1, "this_turn")
LORE_PLUS_2 = StatModification("lore", 2, "this_turn")
LORE_PLUS_3 = StatModification("lore", 3, "this_turn")
STRENGTH_PLUS_1 = StatModification("strength", 1, "this_turn")
STRENGTH_PLUS_2 = StatModification("strength", 2, "this_turn")
STRENGTH_PLUS_3 = StatModification("strength", 3, "this_turn")
WILLPOWER_PLUS_1 = StatModification("willpower", 1, "this_turn")
WILLPOWER_PLUS_2 = StatModification("willpower", 2, "this_turn")
WILLPOWER_PLUS_3 = StatModification("willpower", 3, "this_turn")

# Damage/Heal
DAMAGE_1 = StatModification("damage", 1)
DAMAGE_2 = StatModification("damage", 2)
DAMAGE_3 = StatModification("damage", 3)
HEAL_1 = StatModification("damage", -1)
HEAL_2 = StatModification("damage", -2)
HEAL_3 = StatModification("damage", -3)

# Card draw
DRAW_1 = DrawCards(1)
DRAW_2 = DrawCards(2)
DRAW_3 = DrawCards(3)

# Other common effects
BANISH = BanishCharacter()
RETURN_TO_HAND = ReturnToHand()
DISCARD_CARD = DiscardCard()
EXERT_CHARACTER = ExertCharacter()
PREVENT_TARGETING = PreventEffect("targeting")
NO_EFFECT = NoEffect()


# =============================================================================
# PLAYER ACTION EFFECTS (Phase 1 - TODO 9 Implementation)
# =============================================================================

class InkCardEffect(Effect):
    """Effect for inking a card."""
    
    def __init__(self, card: Any):
        self.card = card
        self._player = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        player = target  # Target is the player from ExecutionEngine
        game_state = context.get('game_state')
        
        # Validate ink hasn't been played this turn
        if game_state and game_state.ink_played_this_turn:
            return target  # Skip if already inked
        
        if player and hasattr(player, 'play_ink'):
            success = player.play_ink(self.card)
            if success and game_state:
                game_state.ink_played_this_turn = True
            self._player = player  # Store for event generation
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get INK_PLAYED event for this effect."""
        if not self._player:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.INK_PLAYED,
            'player': self._player,
            'source': self.card,
            'additional_data': {
                'card_inked': self.card,
                'card_name': self.card.name if hasattr(self.card, 'name') else 'Unknown Card',
                'ink_well_size_after': len(self._player.ink_well) if hasattr(self._player, 'ink_well') else 0
            }
        }]
    
    def __str__(self) -> str:
        card_name = self.card.name if hasattr(self.card, 'name') else 'Unknown Card'
        return f"ink {card_name}"


class PlayCharacterEffect(Effect):
    """Effect for playing a character card."""
    
    def __init__(self, card: Any):
        self.card = card
        self._player = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        player = target
        if not player or not hasattr(player, 'play_character'):
            return target
            
        # Extract ink_cost from context or calculate from card
        ink_cost = context.get('ink_cost') or getattr(self.card, 'cost', 0)
        
        success = player.play_character(self.card, ink_cost)
        if success:
            self._player = player  # Store for event generation
            
            # Queue dry ink effect for next ready phase of this player using event-triggered system
            action_queue = context.get('action_queue')
            if action_queue and hasattr(action_queue, 'enqueue_for_event'):
                # Import here to avoid circular imports
                from ....engine.action_queue import ActionPriority
                from ....engine.event_system import GameEvent
                
                dry_effect = DryInkEffect(self.card)
                
                # Create a condition that checks if this is the correct player's ready phase
                # We need to ensure this triggers only when the original player starts their next turn
                def is_correct_players_ready_phase(event_context):
                    context_player = getattr(event_context, 'player', None)
                    game_state = getattr(event_context, 'game_state', None)
                    
                    # Must be the correct player
                    if context_player != player:
                        return False
                    
                    # Must be that player's turn (current_player)
                    if game_state and game_state.current_player != player:
                        return False
                    
                    return True
                
                action_queue.enqueue_for_event(
                    effect=dry_effect,
                    target=self.card,
                    context=context,
                    trigger_event=GameEvent.READY_PHASE,
                    condition=is_correct_players_ready_phase,
                    priority=ActionPriority.CLEANUP,
                    source_description=f"{self.card.name}'s ink drying"
                )
            
            # Register the character's composable abilities with the event system
            # This must happen after playing but before events are emitted
            if hasattr(self.card, 'composable_abilities') and self.card.composable_abilities:
                # Get event manager from context
                game_state = context.get('game_state')
                event_manager = getattr(game_state, 'event_manager', None) if game_state else None
                
                if event_manager:
                    for ability in self.card.composable_abilities:
                        if hasattr(ability, 'register_with_event_manager'):
                            ability.register_with_event_manager(event_manager)
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get CHARACTER_ENTERS_PLAY and CHARACTER_PLAYED events for this effect."""
        if not self._player:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        # Emit both CHARACTER_PLAYED (specific) and CHARACTER_ENTERS_PLAY (general)
        # CHARACTER_ENTERS_PLAY is what triggered abilities listen for
        # CHARACTER_PLAYED is for specific "played from hand" tracking
        return [
            {
                'type': GameEvent.CHARACTER_ENTERS_PLAY,
                'player': self._player,
                'source': self.card,
                'additional_data': {
                    'character_played': self.card,
                    'character_name': self.card.name if hasattr(self.card, 'name') else 'Unknown Character',
                    'cost_paid': getattr(self.card, 'cost', 0)
                }
            },
            {
                'type': GameEvent.CHARACTER_PLAYED,
                'player': self._player,
                'source': self.card,
                'additional_data': {
                    'character_played': self.card,
                    'character_name': self.card.name if hasattr(self.card, 'name') else 'Unknown Character',
                    'cost_paid': getattr(self.card, 'cost', 0)
                }
            }
        ]
    
    def __str__(self) -> str:
        card_name = self.card.name if hasattr(self.card, 'name') else 'Unknown Character'
        return f"play character {card_name}"


class PlayActionEffect(Effect):
    """Effect for playing an action card."""
    
    def __init__(self, card: Any):
        self.card = card
        self._player = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the player who is playing the action
        player = target if hasattr(target, 'play_action') else context.get('player')
        
        if player and hasattr(player, 'play_action'):
            self._player = player
            # Use the card's cost as the ink cost
            ink_cost = getattr(self.card, 'cost', 0)
            player.play_action(self.card, ink_cost)
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get ACTION_PLAYED event for this effect."""
        if not self._player:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.ACTION_PLAYED,
            'player': self._player,
            'source': self.card,
            'additional_data': {
                'action_played': self.card,
                'action_name': self.card.name if hasattr(self.card, 'name') else 'Unknown Action',
                'cost_paid': getattr(self.card, 'cost', 0)
            }
        }]
    
    def __str__(self) -> str:
        card_name = self.card.name if hasattr(self.card, 'name') else 'Unknown Action'
        return f"play action {card_name}"


class PlayItemEffect(Effect):
    """Effect for playing an item card."""
    
    def __init__(self, card: Any):
        self.card = card
        self._player = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the player who is playing the item
        player = target if hasattr(target, 'play_item') else context.get('player')
        
        if player and hasattr(player, 'play_item'):
            self._player = player
            player.play_item(self.card)
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get ITEM_PLAYED event for this effect."""
        if not self._player:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.ITEM_PLAYED,
            'player': self._player,
            'source': self.card,
            'additional_data': {
                'item_played': self.card,
                'item_name': self.card.name if hasattr(self.card, 'name') else 'Unknown Item',
                'cost_paid': getattr(self.card, 'cost', 0)
            }
        }]
    
    def __str__(self) -> str:
        card_name = self.card.name if hasattr(self.card, 'name') else 'Unknown Item'
        return f"play item {card_name}"


class QuestEffect(Effect):
    """Effect for questing with a character."""
    
    def __init__(self, character: Any):
        self.character = character
        self._lore_gained = None
        self._player = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the player who owns the character
        player = None
        if hasattr(self.character, 'controller') and self.character.controller:
            player = self.character.controller
        elif context.get('player'):
            player = context.get('player')
        elif context.get('game_state'):
            # Fallback to current player if no controller is set
            player = context.get('game_state').current_player
        
        # Validate that the character can quest (check wet ink restriction)
        game_state = context.get('game_state')
        current_turn = game_state.turn_number if game_state else 0
        
        if not hasattr(self.character, 'can_quest') or not self.character.can_quest(current_turn):
            # Character cannot quest (wet ink, exerted, or other restriction)
            return target
        
        if player and hasattr(self.character, 'current_lore'):
            self._player = player
            # Calculate lore gained (current_lore includes all bonuses from abilities)
            self._lore_gained = self.character.current_lore
            # Gain lore
            player.lore += self._lore_gained
            # Exert the character
            if hasattr(self.character, 'exerted'):
                self.character.exerted = True
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get CHARACTER_QUESTS and LORE_GAINED events for this effect."""
        if not self._player:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        events = []
        
        # Character quests event
        events.append({
            'type': GameEvent.CHARACTER_QUESTS,
            'player': self._player,
            'source': self.character,
            'additional_data': {
                'character': self.character,
                'character_name': self.character.name if hasattr(self.character, 'name') else 'Unknown Character',
                'lore_value': getattr(self.character, 'lore', 0)
            }
        })
        
        # Lore gained event if lore was actually gained
        if self._lore_gained and self._lore_gained > 0:
            events.append({
                'type': GameEvent.LORE_GAINED,
                'player': self._player,
                'source': self.character,
                'additional_data': {
                    'lore_amount': self._lore_gained,
                    'source': 'quest',
                    'character_name': self.character.name if hasattr(self.character, 'name') else 'Unknown Character'
                }
            })
        
        return events
    
    def __str__(self) -> str:
        character_name = self.character.name if hasattr(self.character, 'name') else 'Unknown Character'
        return f"quest with {character_name}"


class ChallengeEffect(Effect):
    """Effect for challenging with a character."""
    
    def __init__(self, attacker: Any, defender: Any):
        self.attacker = attacker
        self.defender = defender
        self._player = None
        self._challenge_result = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the player who owns the attacking character
        player = self.attacker.controller if hasattr(self.attacker, 'controller') else context.get('player')
        self._player = player
        
        # Validate that the attacker can challenge (check wet ink restriction)
        game_state = context.get('game_state')
        current_turn = game_state.turn_number if game_state else 0
        
        if not hasattr(self.attacker, 'can_challenge') or not self.attacker.can_challenge(current_turn):
            # Attacker cannot challenge (wet ink, exerted, or other restriction)
            return target
        
        # Exert the attacker
        self.attacker.exerted = True
        
        # Mark character as having acted this turn
        if game_state and hasattr(game_state, 'mark_character_acted'):
            game_state.mark_character_acted(self.attacker.id)
        
        # Get action queue from context for queuing damage effects
        action_queue = context.get('action_queue')
        if not action_queue:
            # Fallback: apply damage directly if no action queue available
            damage_to_defender = self.attacker.current_strength if hasattr(self.attacker, 'current_strength') else self.attacker.strength
            damage_to_attacker = self.defender.current_strength if hasattr(self.defender, 'current_strength') else self.defender.strength
            
            self.defender.damage += damage_to_defender
            self.attacker.damage += damage_to_attacker
            
            self._challenge_result = {
                'attacker': self.attacker,
                'defender': self.defender,
                'damage_to_attacker': damage_to_attacker,
                'damage_to_defender': damage_to_defender
            }
        else:
            # Queue damage effects for proper event handling
            attacker_strength = self.attacker.current_strength if hasattr(self.attacker, 'current_strength') else self.attacker.strength
            defender_strength = self.defender.current_strength if hasattr(self.defender, 'current_strength') else self.defender.strength
            
            # Queue damage to defender
            if attacker_strength > 0:
                damage_to_defender = DamageEffect(
                    self.defender, attacker_strength, 
                    source=self.attacker, damage_type=DamageType.CHALLENGE
                )
                from ....engine.action_queue import ActionPriority
                action_queue.enqueue(
                    damage_to_defender, 
                    target=self.defender,
                    context=context,
                    priority=ActionPriority.HIGH
                )
            
            # Queue damage to attacker
            if defender_strength > 0:
                damage_to_attacker = DamageEffect(
                    self.attacker, defender_strength,
                    source=self.defender, damage_type=DamageType.CHALLENGE
                )
                action_queue.enqueue(
                    damage_to_attacker, 
                    target=self.attacker,
                    context=context,
                    priority=ActionPriority.HIGH
                )
            
            self._challenge_result = {
                'attacker': self.attacker,
                'defender': self.defender,
                'damage_queued_to_attacker': defender_strength,
                'damage_queued_to_defender': attacker_strength
            }
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get CHARACTER_CHALLENGES event for this effect."""
        if not self._player:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CHARACTER_CHALLENGES,
            'player': self._player,
            'source': self.attacker,
            'target': self.defender,
            'additional_data': {
                'context': self._challenge_result,
                'attacker': self.attacker,
                'defender': self.defender,
                'attacker_name': self.attacker.name if hasattr(self.attacker, 'name') else 'Unknown Character',
                'defender_name': self.defender.name if hasattr(self.defender, 'name') else 'Unknown Character',
                'challenge_result': self._challenge_result
            }
        }]
    
    def __str__(self) -> str:
        attacker_name = self.attacker.name if hasattr(self.attacker, 'name') else 'Unknown Character'
        defender_name = self.defender.name if hasattr(self.defender, 'name') else 'Unknown Character'
        return f"{attacker_name} challenges {defender_name}"


class SingEffect(Effect):
    """Effect for singing a song with a character."""
    
    def __init__(self, singer: Any, song: Any):
        self.singer = singer
        self.song = song
        self._player = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the player who owns the singing character
        player = self.singer.controller if hasattr(self.singer, 'controller') else context.get('player')
        
        if player and hasattr(player, 'sing_song'):
            self._player = player
            player.sing_song(self.singer, self.song)
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get SONG_SUNG event for this effect."""
        if not self._player:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.SONG_SUNG,
            'player': self._player,
            'source': self.singer,
            'additional_data': {
                'singer': self.singer,
                'song': self.song,
                'singer_name': self.singer.name if hasattr(self.singer, 'name') else 'Unknown Character',
                'song_name': self.song.name if hasattr(self.song, 'name') else 'Unknown Song'
            }
        }]
    
    def __str__(self) -> str:
        singer_name = self.singer.name if hasattr(self.singer, 'name') else 'Unknown Character'
        song_name = self.song.name if hasattr(self.song, 'name') else 'Unknown Song'
        return f"{singer_name} sings {song_name}"


# =============================================================================
# AUTOMATIC GAME OPERATION EFFECTS (Phase 1 - TODO 9 Implementation)
# =============================================================================

# DealDamageEffect has been replaced by DamageEffect which provides better event handling
# This class remains for backwards compatibility but should not be used in new code
class DealDamageEffect(Effect):
    """Effect for dealing damage to a character.
    
    DEPRECATED: Use DamageEffect instead for proper event handling and damage modification.
    """
    
    def __init__(self, amount: int, source: Any = None):
        self.amount = amount
        self.source = source
        self._damage_dealt = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # For backwards compatibility, still use the old approach
        # but recommend switching to DamageEffect
        if hasattr(target, 'take_damage'):
            self._damage_dealt = target.take_damage(self.amount)
        elif hasattr(target, 'damage'):
            # Direct damage application as fallback
            target.damage = getattr(target, 'damage', 0) + self.amount
            self._damage_dealt = self.amount
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get CHARACTER_TAKES_DAMAGE event for this effect."""
        if self._damage_dealt is None or self._damage_dealt <= 0:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CHARACTER_TAKES_DAMAGE,
            'target': target,
            'source': self.source or context.get('source'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'damage_amount': self._damage_dealt,
                'target_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'source_name': self.source.name if (self.source and hasattr(self.source, 'name')) else 'Unknown Source'
            }
        }]
    
    def __str__(self) -> str:
        return f"deal {self.amount} damage"


class PhaseProgressionEffect(Effect):
    """Effect for progressing to the next phase - pure phase transition only."""
    
    def __init__(self, phase: str = None):
        self.phase = phase
        self._previous_phase = None
        self._new_phase = None
        self._player = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the game state
        game_state = context.get('game_state')
        
        if game_state:
            # Store previous phase for event generation
            self._previous_phase = getattr(game_state, 'current_phase', None)
            self._player = getattr(game_state, 'current_player', None)
            
            # Get phase management effects but don't call advance_phase() to avoid recursion
            # Instead, get the next phase manually and set it directly
            from ...game.game_state import Phase
            current_phase = game_state.current_phase
            
            next_phase = None
            if current_phase == Phase.READY:
                next_phase = Phase.SET
            elif current_phase == Phase.SET:
                next_phase = Phase.DRAW
            elif current_phase == Phase.DRAW:
                next_phase = Phase.PLAY
            elif current_phase == Phase.PLAY:
                # End turn - transition to next player's READY phase
                # First end the current turn
                game_state.end_turn()  # This switches players and resets to READY phase
                next_phase = Phase.READY
                self._player = game_state.current_player  # Update to new player
            
            if next_phase:
                game_state.current_phase = next_phase
                self._new_phase = next_phase
            else:
                self._new_phase = self._previous_phase
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get phase progression events for this effect."""
        events = []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        from ...game.game_state import Phase
        
        # Check if this was a turn transition (PLAY -> READY with new player)
        if (self._previous_phase == Phase.PLAY and 
            self._new_phase == Phase.READY and 
            self._player):
            
            # Get game state to determine who the previous player was
            game_state = context.get('game_state')
            if game_state:
                # Find the previous player (the other player)
                prev_player = None
                for player in game_state.players:
                    if player != self._player:
                        prev_player = player
                        break
                
                # Generate TURN_ENDS event for previous player
                if prev_player:
                    events.append({
                        'type': GameEvent.TURN_ENDS,
                        'player': prev_player,
                        'source': context.get('source'),
                        'additional_data': {
                            'turn_number': game_state.turn_number - 1
                        }
                    })
                
                # Generate TURN_BEGINS event for new player
                events.append({
                    'type': GameEvent.TURN_BEGINS,
                    'player': self._player,
                    'source': context.get('source'),
                    'additional_data': {
                        'turn_number': game_state.turn_number
                    }
                })
        
        # Add phase transition event
        if self._player and self._new_phase:
            # Map phase names to events
            phase_events = {
                'ready': GameEvent.READY_PHASE,
                'set': GameEvent.SET_PHASE,
                'draw': GameEvent.DRAW_PHASE,
                'play': GameEvent.PLAY_PHASE,
            }
            
            event_type = phase_events.get(self._new_phase.value.lower()) if self._new_phase else None
            
            if event_type:
                events.append({
                    'type': event_type,
                    'player': self._player,
                    'source': context.get('source'),
                    'additional_data': {
                        'previous_phase': self._previous_phase,
                        'new_phase': self._new_phase
                    }
                })
        
        return events
    
    def __str__(self) -> str:
        if self.phase:
            return f"progress to {self.phase} phase"
        return "progress to next phase"


class DryInkEffect(Effect):
    """Effect to dry a character's ink, making it ready to act."""
    
    def __init__(self, character):
        self.character = character
        self._dried = False
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Dry the character's ink if it's still alive."""
        if self.character and hasattr(self.character, 'is_alive') and self.character.is_alive:
            old_dry_status = getattr(self.character, 'is_dry', True)
            self.character.is_dry = True
            self._dried = not old_dry_status  # Only count as dried if it was previously wet
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get ink drying events."""
        events = []
        
        if self._dried and self.character:
            # Import here to avoid circular imports
            from ....engine.event_system import GameEvent
            
            events.append({
                'type': GameEvent.CHARACTER_READIED,
                'target': self.character,
                'source': None,
                'player': getattr(self.character, 'controller', None),
                'additional_data': {
                    'character_name': getattr(self.character, 'name', 'Unknown'),
                    'reason': 'ink_dried'
                }
            })
        
        return events
    
    def __str__(self) -> str:
        if self.character:
            char_name = getattr(self.character, 'name', 'Unknown')
            return f"{char_name}'s ink dried"
        return "character's ink dried"


# =============================================================================
# ADDITIONAL EFFECTS FOR ADVANCED ABILITIES
# =============================================================================

class ShiftEffect(Effect):
    """Play a character for reduced cost by discarding another character (Shift)."""
    
    def __init__(self, cost_reduction: int = 0):
        self.cost_reduction = cost_reduction
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # This is a play-time effect that modifies how the character can be played
        # The actual cost reduction logic would be handled in the game engine
        if hasattr(target, 'metadata'):
            target.metadata['shift_cost_reduction'] = self.cost_reduction
        else:
            target.metadata = {'shift_cost_reduction': self.cost_reduction}
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for shift activation."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.SHIFT_ACTIVATED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'cost_reduction': self.cost_reduction,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        if self.cost_reduction > 0:
            return f"shift (reduce cost by {self.cost_reduction})"
        return "shift"


class ChallengerEffect(Effect):
    """Grant +X strength while challenging (Challenger +X)."""
    
    def __init__(self, strength_bonus: int, duration: str = "permanent"):
        self.strength_bonus = strength_bonus
        self.duration = duration
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        # Create temporary challenger ability for event-driven expiration
        expiration_event = self._get_expiration_event(self.duration)
        temp_ability = TemporaryChallengerAbility(
            self.strength_bonus, 
            target, 
            expiration_event
        )
        
        # Add to target's abilities
        if not hasattr(target, 'composable_abilities'):
            target.composable_abilities = []
        target.composable_abilities.append(temp_ability)
        
        # Register with event system if available
        event_manager = context.get('event_manager')
        game_state = context.get('game_state')
        
        # Try multiple ways to get event manager
        if not event_manager and game_state:
            event_manager = getattr(game_state, 'event_manager', None)
        
        if event_manager:
            temp_ability.register_with_event_manager(event_manager)
                
        return target
    
    def _get_expiration_event(self, duration: str):
        """Map duration strings to GameEvent types."""
        from ....engine.event_system import GameEvent
        
        if duration == "this_turn":
            return GameEvent.TURN_ENDS
        elif duration == "this_challenge":
            return GameEvent.CHALLENGE_RESOLVED
        elif duration == "end_of_turn":
            return GameEvent.TURN_ENDS
        else:
            # Default to turn end for unknown durations
            return GameEvent.TURN_ENDS
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for challenger activation."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CHALLENGER_ACTIVATED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'strength_bonus': self.strength_bonus,
                'duration': self.duration,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        if self.duration == "permanent":
            return f"challenger +{self.strength_bonus}"
        else:
            return f"challenger +{self.strength_bonus} ({self.duration})"


class VanishEffect(Effect):
    """Banish this character when opponent chooses it for an action (Vanish)."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Banish the character immediately when targeted by opponent
        if hasattr(target, 'banish'):
            # Use the banish method if available (for mock characters in tests)
            target.banish()
        else:
            # For real characters, set the banished metadata
            if hasattr(target, 'metadata'):
                target.metadata['banished'] = True
            else:
                target.metadata = {'banished': True}
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for vanish activation."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CHARACTER_VANISHED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "vanish (banish when targeted by opponent)"


class RecklessEffect(Effect):
    """Prevent questing and force challenging (Reckless)."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Mark character as unable to quest and must challenge
        if hasattr(target, 'metadata'):
            target.metadata['cannot_quest'] = True
            target.metadata['must_challenge_if_able'] = True
        else:
            target.metadata = {'cannot_quest': True, 'must_challenge_if_able': True}
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for reckless activation."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.RECKLESS_ACTIVATED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "reckless (can't quest, must challenge if able)"


class SingTogetherEffect(Effect):
    """Exert multiple characters to sing for free (Sing Together X)."""
    
    def __init__(self, required_cost: int):
        self.required_cost = required_cost
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        event_context = context.get('event_context')
        if event_context and event_context.additional_data:
            # Mark that this character can participate in sing together
            event_context.additional_data['sing_together_required_cost'] = self.required_cost
            event_context.additional_data['can_sing_together'] = True
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for sing together activation."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.SING_TOGETHER_ACTIVATED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'required_cost': self.required_cost,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"sing together {self.required_cost}"


class CostModification(Effect):
    """Modify the cost of a target card."""
    
    def __init__(self, cost_change: int):
        self.cost_change = cost_change  # Negative for cost reduction
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # If target is None, this effect cannot be applied (no valid targets)
        if target is None:
            return None
            
        # If target has a cost attribute, modify it directly
        if hasattr(target, 'cost'):
            target.cost += self.cost_change
        elif hasattr(target, 'modify_cost'):
            # Use modify_cost method if available
            target.modify_cost(self.cost_change)
        else:
            # Fallback: store in metadata
            if not hasattr(target, 'metadata'):
                target.metadata = {}
            target.metadata['cost_modification'] = target.metadata.get('cost_modification', 0) + self.cost_change
        
        return target

    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for cost modification."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.COST_MODIFIED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'cost_change': self.cost_change,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        sign = "+" if self.cost_change >= 0 else ""
        return f"modify cost by {sign}{self.cost_change}"


class ReadyCharacter(Effect):
    """Ready (un-exert) a character."""
    
    def __init__(self, character: Any = None):
        """Initialize ReadyCharacter effect.
        
        Args:
            character: Specific character to ready. If None, uses target from apply() method.
        """
        self.character = character
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Use specific character if provided, otherwise use target
        char_to_ready = self.character if self.character is not None else target
        if hasattr(char_to_ready, 'exerted'):
            char_to_ready.exerted = False
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for readying character."""
        # Use specific character if provided, otherwise use target
        char_to_ready = self.character if self.character is not None else target
        
        if not hasattr(char_to_ready, 'controller'):
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CHARACTER_READIED,
            'target': char_to_ready,
            'source': context.get('source') or context.get('ability_owner'),
            'player': char_to_ready.controller,
            'additional_data': {
                'character_name': char_to_ready.name if hasattr(char_to_ready, 'name') else 'Unknown Character',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "ready character"


class ReadyInk(Effect):
    """Ready (un-exert) ink cards."""
    
    def __init__(self, count: int = None):
        self.count = count  # None means ready all exerted ink
        self.readied_cards = []
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        player = target
        if not hasattr(player, 'inkwell'):
            return target
            
        exerted_ink = [card for card in player.inkwell if card.exerted]
        
        # Ready specified count or all
        cards_to_ready = exerted_ink[:self.count] if self.count else exerted_ink
        
        self.readied_cards = []
        for card in cards_to_ready:
            card.exerted = False
            self.readied_cards.append(card)
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get INK_READIED event for this effect."""
        if not self.readied_cards:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.INK_READIED,
            'player': target,
            'source': context.get('source') or context.get('ability_owner'),
            'additional_data': {
                'player_name': target.name if hasattr(target, 'name') else 'Unknown Player',
                'ink_count': len(self.readied_cards)
            }
        }]
    
    def __str__(self) -> str:
        if self.count:
            return f"ready {self.count} ink"
        return "ready all ink"


class PlayCardFromDiscard(Effect):
    """Play a card from discard pile."""
    
    def __init__(self, card_filter: Optional[Callable] = None):
        self.card_filter = card_filter
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Implementation would involve game state manipulation
        # This is a placeholder for the effect
        game_state = context.get('game_state')
        player = context.get('player') or getattr(target, 'controller', None)
        if game_state and player:
            # Mark that player can play from discard
            if not hasattr(player, 'temporary_effects'):
                player.temporary_effects = []
            player.temporary_effects.append(('play_from_discard', self.card_filter))
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for playing card from discard."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.PLAYED_FROM_DISCARD,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': context.get('player') or getattr(target, 'controller', None),
            'additional_data': {
                'has_filter': self.card_filter is not None,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "play card from discard"


class SearchLibrary(Effect):
    """Search library for cards."""
    
    def __init__(self, count: int = 1, card_filter: Optional[Callable] = None, 
                 reveal: bool = False, shuffle_after: bool = True):
        self.count = count
        self.card_filter = card_filter
        self.reveal = reveal
        self.shuffle_after = shuffle_after
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Implementation would involve deck manipulation
        player = context.get('player') or getattr(target, 'controller', None)
        if player and hasattr(player, 'deck'):
            # Mark for later resolution by game engine
            if not hasattr(player, 'pending_searches'):
                player.pending_searches = []
            player.pending_searches.append({
                'count': self.count,
                'filter': self.card_filter,
                'reveal': self.reveal,
                'shuffle': self.shuffle_after
            })
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for searching library."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.LIBRARY_SEARCHED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': context.get('player') or getattr(target, 'controller', None),
            'additional_data': {
                'card_count': self.count,
                'has_filter': self.card_filter is not None,
                'reveal': self.reveal,
                'shuffle_after': self.shuffle_after,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"search library for {self.count} card{'s' if self.count != 1 else ''}"


class BodyguardEffect(Effect):
    """Allow entering play exerted and force targeting (Bodyguard)."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Mark character as having bodyguard
        if hasattr(target, 'metadata'):
            target.metadata['has_bodyguard'] = True
            target.metadata['can_enter_exerted'] = True
        else:
            target.metadata = {'has_bodyguard': True, 'can_enter_exerted': True}
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for bodyguard activation."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.BODYGUARD_ACTIVATED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "bodyguard"


class SupportStrengthEffect(Effect):
    """Add this character's strength to another character this turn (Support)."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the support character (the one with Support ability)
        support_char = context.get('ability_owner')
        if support_char and hasattr(support_char, 'current_strength'):
            # Add support character's strength to target
            if hasattr(target, 'add_strength_bonus'):
                target.add_strength_bonus(support_char.current_strength, "this_turn")
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for support activation."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        support_char = context.get('ability_owner')
        support_strength = support_char.current_strength if (support_char and hasattr(support_char, 'current_strength')) else 0
        
        return [{
            'type': GameEvent.SUPPORT_ACTIVATED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'support_character': support_char.name if (support_char and hasattr(support_char, 'name')) else 'Unknown Character',
                'strength_bonus': support_strength,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "add support character's strength"


# Additional pre-built effects
SHIFT = ShiftEffect()
CHALLENGER_1 = ChallengerEffect(1)
CHALLENGER_2 = ChallengerEffect(2) 
CHALLENGER_3 = ChallengerEffect(3)
VANISH = VanishEffect()
RECKLESS = RecklessEffect()
BODYGUARD = BodyguardEffect()
SUPPORT_STRENGTH = SupportStrengthEffect()
EXERT = ExertCharacter()
READY = ReadyCharacter()
SEARCH_1 = SearchLibrary(1)
PLAY_FROM_DISCARD = PlayCardFromDiscard()


# =============================================================================
# NAMED ABILITY SPECIFIC EFFECTS
# =============================================================================

class PreventSingingEffect(Effect):
    """Prevents a character from singing songs (VOICELESS)."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'can_sing'):
            target.can_sing = False
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for preventing singing."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.SINGING_PREVENTED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "prevent singing"


class RemoveDamageEffect(Effect):
    """Removes damage from a character."""
    
    def __init__(self, amount: int, up_to: bool = False):
        self.amount = amount
        self.up_to = up_to
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'damage'):
            if self.up_to:
                remove_amount = min(self.amount, target.damage)
            else:
                remove_amount = self.amount
            target.damage = max(0, target.damage - remove_amount)
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for removing damage."""
        if not hasattr(target, 'damage'):
            return []
        
        # Calculate actual amount removed
        if self.up_to:
            actual_remove = min(self.amount, target.damage)
        else:
            actual_remove = self.amount
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.DAMAGE_REMOVED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'damage_removed': actual_remove,
                'up_to': self.up_to,
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        prefix = "up to " if self.up_to else ""
        return f"remove {prefix}{self.amount} damage"


class ReturnCardToHandEffect(Effect):
    """Returns a card from discard to hand."""
    
    def __init__(self, card_filter: Callable = None):
        self.card_filter = card_filter
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # This would interact with game state to move card from discard to hand
        # Implementation depends on game state structure
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for returning card to hand."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CARD_RETURNED_TO_HAND,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'card_name': target.name if hasattr(target, 'name') else 'Unknown Card',
                'from_zone': 'discard',
                'has_filter': self.card_filter is not None,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "return card to hand"


class DeckManipulationEffect(Effect):
    """Look at top cards, optionally reveal and take one."""
    
    def __init__(self, cards_to_look: int, card_filter: Callable = None, 
                 reveal: bool = False, to_hand: bool = True):
        self.cards_to_look = cards_to_look
        self.card_filter = card_filter
        self.reveal = reveal
        self.to_hand = to_hand
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # This would interact with game state to manipulate deck
        # Implementation depends on game state structure
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for deck manipulation."""
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.DECK_LOOKED_AT,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller if hasattr(target, 'controller') else context.get('player'),
            'additional_data': {
                'cards_to_look': self.cards_to_look,
                'has_filter': self.card_filter is not None,
                'reveal': self.reveal,
                'to_hand': self.to_hand,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"look at top {self.cards_to_look} cards"


class GainLoreEffect(Effect):
    """Gain lore effect."""
    
    def __init__(self, amount: int):
        self.amount = amount
        self._lore_before = None
        self._lore_after = None
        self._controller = None
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Get the controller who can gain lore
        controller = self._get_lore_controller(target, context)
        
        if controller and hasattr(controller, 'gain_lore'):
            self._controller = controller
            self._lore_before = controller.lore
            
            # Gain the lore
            controller.gain_lore(self.amount)
            
            self._lore_after = controller.lore
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get the LORE_GAINED event for this effect."""
        if not self._controller:
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.LORE_GAINED,
            'player': self._controller,
            'source': context.get('source') or context.get('ability_owner'),
            'additional_data': {
                'lore_amount': self.amount,
                'source': 'ability',
                'ability_name': context.get('ability_name', 'Unknown'),
                'lore_before': self._lore_before,
                'lore_after': self._lore_after
            }
        }]
    
    def _get_lore_controller(self, target: Any, context: Dict[str, Any]) -> Any:
        """Get the controller who can gain lore."""
        # First check if target can gain lore directly (target is a player)
        if hasattr(target, 'gain_lore'):
            return target
        
        # Try to get controller from target
        if hasattr(target, 'controller') and target.controller:
            return target.controller
        
        # If target doesn't have controller, get from context
        ability_owner = context.get('ability_owner')
        if ability_owner and hasattr(ability_owner, 'controller'):
            return ability_owner.controller
        
        # Try getting player directly from context
        return context.get('player')
    
    def __str__(self) -> str:
        return f"gain {self.amount} lore"


# Factory functions for parameterized effects
def GAIN_LORE(amount: int):
    return GainLoreEffect(amount)


# Pre-built named ability effects
PREVENT_SINGING = PreventSingingEffect()
REMOVE_DAMAGE_3 = RemoveDamageEffect(3, up_to=True)
REMOVE_DAMAGE_2 = RemoveDamageEffect(2, up_to=True)
RETURN_CHARACTER_TO_HAND = ReturnCardToHandEffect(lambda card: hasattr(card, 'card_type') and card.card_type == 'Character')
LOOK_AT_TOP_4 = DeckManipulationEffect(4, lambda card: 'Song' in getattr(card, 'card_type', ''), reveal=True)
DRAW_CARD = DrawCards(1)


class ConditionalEffectWrapper(Effect):
    """Wrapper effect for conditional ability events."""
    
    def __init__(self, conditional_event: Dict[str, Any]):
        self.conditional_event = conditional_event
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply the conditional effect by processing the event."""
        # For now, just log the conditional effect application
        # In the future, this could trigger more complex logic
        event_type = self.conditional_event.get('type', 'UNKNOWN')
        ability_name = self.conditional_event.get('ability_name', 'Unknown')
        
        return {
            'type': 'conditional_effect_processed',
            'event_type': event_type,
            'ability_name': ability_name,
            'details': self.conditional_event.get('details', {})
        }
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for conditional effect application."""
        from ...engine.event_system import GameEvent
        return [{
            'event': GameEvent.CONDITIONAL_EFFECT_APPLIED,
            'context': {
                'conditional_event': self.conditional_event,
                'result': result
            }
        }]

    def __str__(self) -> str:
        ability_name = self.conditional_event.get('ability_name', 'Unknown')
        return f"ConditionalEffectWrapper({ability_name})"


class ResolveChoiceEffect(Effect):
    """Effect that resolves a player choice."""
    
    def __init__(self, choice_id: str, option: str):
        self.choice_id = choice_id
        self.option = option
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Resolve a choice by providing targets to the waiting effect."""
        logger.debug("ResolveChoiceEffect.apply called for choice {self.choice_id} with option {self.option}")
        
        # Get the choice manager
        choice_manager = target
        
        # Find and validate the choice
        if not hasattr(choice_manager, 'current_choice') or not choice_manager.current_choice:
            print(f"WARNING: No current choice found in choice manager")
            return target
            
        if choice_manager.current_choice.choice_id != self.choice_id:
            print(f"WARNING: Choice ID mismatch: expected {self.choice_id}, got {choice_manager.current_choice.choice_id}")
            return target
        
        # Get the selected option and its effect
        selected_option = None
        for option in choice_manager.current_choice.options:
            if option.id == self.option:
                selected_option = option
                break
        
        if selected_option is None:
            print(f"WARNING: Invalid option: {self.option}")
            return target
        
        # Determine the target for the effect
        # For options with explicit targets, use option.target
        # For yes/no choices (PlayerChoice), use the original trigger target
        selected_target = selected_option.target
        if selected_target is None:
            # Fall back to the original trigger target from context
            selected_target = choice_manager.current_choice.trigger_context.get('_choice_target')
        
        if selected_target is None:
            print(f"WARNING: No target found for option {self.option}")
            return target
        
        logger.debug("Selected target: {selected_target}")
        
        # Handle both new and legacy choice architectures
        action_queue = context.get('action_queue')
        selected_effect = selected_option.effect
        
        # New architecture: Try waiting action first (for ChoiceGenerationEffect)
        waiting_action_resumed = False
        if action_queue:
            action_id = action_queue.resolve_choice_and_continue(self.choice_id, [selected_target])
            if action_id:
                waiting_action_resumed = True
                logger.debug("Resumed waiting action {action_id} for choice {self.choice_id}")
            else:
                logger.debug("No waiting action found for choice {self.choice_id}")
        
        # Legacy architecture: Execute option effect if present and no waiting action (for PlayerChoice)
        if selected_effect and not waiting_action_resumed:
            if action_queue:
                # Queue the effect with high priority for proper message flow
                from ....engine.action_queue import ActionPriority
                execution_context = choice_manager.current_choice.trigger_context.copy()
                execution_context.update(context)
                action_id = action_queue.enqueue(
                    effect=selected_effect,
                    target=selected_target,
                    context=execution_context,
                    priority=ActionPriority.HIGH,
                    source_description=f"Choice: {choice_manager.current_choice.ability_name} - {selected_option.description}"
                )
                logger.debug("Queued selected option effect with action ID: {action_id}")
            else:
                # Direct execution as last resort (not recommended)
                execution_context = choice_manager.current_choice.trigger_context.get('_choice_execution_context', context)
                result = selected_effect.apply(selected_target, execution_context)
                logger.debug("Executed option effect directly, result: {result}")
        elif not selected_effect and not waiting_action_resumed:
            logger.debug("No effect to execute and no waiting action found")
        
        # Properly clear the choice from the manager's pending list
        if choice_manager.current_choice:
            choice_to_remove = choice_manager.current_choice
            if choice_to_remove in choice_manager.pending_choices:
                choice_manager.pending_choices.remove(choice_to_remove)
        
        # Set next choice or clear if none remaining
        choice_manager.current_choice = choice_manager.pending_choices[0] if choice_manager.pending_choices else None
        
        # Unpause if no more choices
        if not choice_manager.pending_choices:
            choice_manager.game_paused = False
        
        return f"Choice resolved: {self.option}"
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for choice resolution."""
        return []
    
    def __str__(self) -> str:
        return f"resolve choice {self.choice_id} with {self.option}"


class ChoiceGenerationEffect(Effect):
    """Effect that generates a choice and queues the follow-up targeted effect."""
    
    def __init__(self, target_selector, follow_up_effect, ability_name="Unknown"):
        self.target_selector = target_selector
        self.follow_up_effect = follow_up_effect
        self.ability_name = ability_name
    
    def apply(self, target: Any, context: Dict[str, Any]) -> str:
        """Generate choice options and queue the follow-up effect."""
        logger.debug("ChoiceGenerationEffect.apply called for {self.ability_name}")
        
        # Generate choice options using target_selector
        choice_options = self.target_selector.get_choice_options(context)
        logger.debug("Generated {len(choice_options) if choice_options else 0} choice options")
        
        if not choice_options:
            logger.debug("No valid choice options, skipping effect")
            return f"No valid targets for {self.ability_name}"
        
        # Get required managers from context
        choice_manager = context.get('choice_manager')
        action_queue = context.get('action_queue')
        
        # Add missing context from event context if available
        event_context = context.get('event_context')
        if event_context:
            if not choice_manager:
                choice_manager = getattr(event_context, 'choice_manager', None)
            if not action_queue:
                action_queue = getattr(event_context, 'action_queue', None)
        
        # If still no choice_manager, try to get it from game_state
        if not choice_manager:
            game_state = context.get('game_state')
            if game_state and hasattr(game_state, 'choice_manager'):
                choice_manager = game_state.choice_manager
            elif game_state and hasattr(game_state, 'event_manager'):
                # Try to get it from event_manager
                event_manager = game_state.event_manager
                if hasattr(event_manager, 'choice_manager'):
                    choice_manager = event_manager.choice_manager
        
        
        if not choice_manager or not action_queue:
            logger.debug("Missing choice_manager or action_queue in context")
            logger.debug("choice_manager: {choice_manager}")
            logger.debug("action_queue: {action_queue}")
            return f"Cannot generate choice for {self.ability_name}"
        
        # Create a ChoiceContext object
        from ....engine.choice_system import ChoiceContext, ChoiceType
        
        # Get player info
        ability_owner = context.get('ability_owner')
        player = ability_owner.controller if ability_owner else context.get('player')
        
        # Generate choice ID
        choice_id = choice_manager.generate_choice_id()
        
        # Create choice context
        choice_context = ChoiceContext(
            choice_id=choice_id,
            player=player,
            ability_name=self.ability_name,
            prompt=f"Select target enemy character for {self.ability_name}",
            choice_type=ChoiceType.SELECT_TARGETS,
            options=choice_options,
            trigger_context=context,
            timeout_seconds=None,
            default_option=None
        )
        
        # Queue the choice 
        choice_manager.queue_choice(choice_context, target, context)
        logger.debug("Created choice with ID: {choice_id}")
        
        # Queue the follow-up effect to wait for choice resolution
        from ....engine.action_queue import ActionPriority
        action_queue.enqueue_waiting_for_choice(
            effect=self.follow_up_effect,
            choice_id=choice_id,
            target=target,
            context=context,
            priority=ActionPriority.HIGH,
            source_description=f"Apply selected effect for {self.ability_name}"
        )
        logger.debug("Successfully queued follow-up effect")
        
        result_msg = f"Choice generated for {self.ability_name}"
        return result_msg
    
    def __str__(self) -> str:
        return f"generate choice for {self.ability_name}"




class ResetTurnState(Effect):
    """Reset turn state via effect system."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        game_state = context.get('game_state')
        if game_state:
            # Reset turn state properties
            game_state.ink_played_this_turn = False
            game_state.card_drawn_this_turn = False
            game_state.actions_this_turn.clear()
            game_state.characters_acted_this_turn.clear()
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        return [{
            'type': GameEvent.TURN_STATE_RESET,
            'target': target,
            'player': target,
            'additional_data': {'reason': 'turn_transition'}
        }]
    
    def __str__(self) -> str:
        return "reset turn state"


class TriggerPhaseTransition(Effect):
    """Trigger phase transition with proper event generation."""
    
    def __init__(self, from_phase, to_phase):
        self.from_phase = from_phase
        self.to_phase = to_phase
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        game_state = context.get('game_state')
        if game_state:
            game_state.current_phase = self.to_phase
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        events = [
            {
                'type': GameEvent.PHASE_TRANSITION,
                'target': context.get('game_state'),
                'additional_data': {
                    'from_phase': self.from_phase.value,
                    'to_phase': self.to_phase.value
                }
            }
        ]
        
        # Add specific phase begin event if it exists
        phase_begin_event_name = f'{self.to_phase.value.upper()}_BEGINS'
        try:
            phase_begin_event = getattr(GameEvent, phase_begin_event_name)
            events.append({
                'type': phase_begin_event,
                'target': context.get('game_state'),
                'additional_data': {'phase': self.to_phase.value}
            })
        except AttributeError:
            # Phase begin event doesn't exist, that's ok
            pass
        
        return events
    
    def __str__(self) -> str:
        return f"transition from {self.from_phase.value} to {self.to_phase.value}"


class ReadyInk(Effect):
    """Ready all ink cards in a player's inkwell."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        player = target
        if hasattr(player, 'inkwell'):
            for ink_card in player.inkwell:
                if hasattr(ink_card, 'exerted'):
                    ink_card.exerted = False
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        return [{
            'type': GameEvent.INK_READIED,
            'target': target,
            'player': target,
            'additional_data': {
                'ink_count': len(getattr(target, 'inkwell', [])),
                'reason': 'ready_step'
            }
        }]
    
    def __str__(self) -> str:
        return "ready all ink"


class DrawAttemptEffect(Effect):
    """Initiate a draw attempt (can be modified/prevented by abilities)."""
    
    def __init__(self, amount: int = 1, reason: str = "draw_phase"):
        self.amount = amount
        self.reason = reason
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Generate DRAW_ATTEMPT event first
        # This allows abilities to modify or prevent the draw
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        return [{
            'type': GameEvent.DRAW_ATTEMPT,
            'target': target,
            'player': target,
            'additional_data': {
                'amount': self.amount,
                'reason': self.reason,
                'can_be_modified': True
            }
        }]
    
    def __str__(self) -> str:
        return f"attempt to draw {self.amount} card{'s' if self.amount != 1 else ''}"


class ModifyDrawEffect(Effect):
    """Modify an ongoing draw (for replacement effects)."""
    
    def __init__(self, new_amount: Optional[int] = None, replacement_effect: Optional[Effect] = None):
        self.new_amount = new_amount
        self.replacement_effect = replacement_effect
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Modify the draw context
        if self.new_amount is not None:
            context['modified_draw_amount'] = self.new_amount
        if self.replacement_effect:
            context['replacement_effect'] = self.replacement_effect
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        return [{
            'type': GameEvent.DRAW_MODIFIED,
            'target': target,
            'player': target,
            'additional_data': {
                'original_amount': context.get('original_draw_amount'),
                'new_amount': self.new_amount,
                'has_replacement': self.replacement_effect is not None
            }
        }]
    
    def __str__(self) -> str:
        if self.new_amount is not None:
            return f"modify draw to {self.new_amount} cards"
        elif self.replacement_effect:
            return f"replace draw with {self.replacement_effect}"
        return "modify draw"


class NoOpEffect:
    """Effect that does nothing - used for placeholder abilities."""
    
    def apply(self, target: Any, context: dict) -> Any:
        """Do nothing."""
        return target
    
    def get_events(self, target: Any, context: dict, result: Any) -> List[Dict[str, Any]]:
        """Get events for no-op effect."""
        return []
    
    def __str__(self) -> str:
        return "no effect"


class ModifyStat(Effect):
    """Modify a stat (strength, willpower, cost, etc.) on target."""
    
    def __init__(self, stat_name: str, modifier: int, duration_type: str = "permanent"):
        self.stat_name = stat_name
        self.modifier = modifier
        self.duration_type = duration_type  # "permanent", "until_end_of_turn", "while_condition"
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Apply stat modification
        if hasattr(target, self.stat_name):
            current_value = getattr(target, self.stat_name)
            new_value = current_value + self.modifier
            setattr(target, self.stat_name, new_value)
        elif hasattr(target, 'metadata'):
            # Store as metadata if direct attribute doesn't exist
            stat_modifier_key = f'{self.stat_name}_modifier'
            current_modifier = target.metadata.get(stat_modifier_key, 0)
            target.metadata[stat_modifier_key] = current_modifier + self.modifier
        
        # If temporary, register with timing system
        if self.duration_type != "permanent":
            timing_component = context.get('turn_timing')
            if timing_component:
                # Create reverse effect for cleanup
                reverse_effect = ModifyStat(self.stat_name, -self.modifier, "permanent")
                timing_component.register_temporary_effect(
                    reverse_effect, 
                    self.duration_type, 
                    1 if self.duration_type == "until_end_of_turn" else None
                )
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        from ....engine.event_system import GameEvent
        return [{
            'type': GameEvent.STAT_MODIFIED,
            'target': target,
            'source': context.get('source'),
            'additional_data': {
                'stat_name': self.stat_name,
                'modifier': self.modifier,
                'duration': self.duration_type,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        sign = "+" if self.modifier >= 0 else ""
        duration = f" ({self.duration_type})" if self.duration_type != "permanent" else ""
        return f"{sign}{self.modifier} {self.stat_name}{duration}"


class TemporaryEffect(Effect):
    """Wrapper for effects that should expire after a duration."""
    
    def __init__(self, wrapped_effect: Effect, duration_type: str, duration_value: int = 1):
        self.wrapped_effect = wrapped_effect
        self.duration_type = duration_type  # "turns", "until_end_of_turn", "phases"
        self.duration_value = duration_value
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Apply the wrapped effect
        result = self.wrapped_effect.apply(target, context)
        
        # Register for automatic removal
        timing_component = context.get('turn_timing')
        if timing_component:
            # Create cleanup effect
            if hasattr(self.wrapped_effect, 'create_reverse_effect'):
                cleanup_effect = self.wrapped_effect.create_reverse_effect()
            else:
                # Default cleanup: try to reverse common effects
                cleanup_effect = self._create_default_cleanup(target, context)
            
            if cleanup_effect:
                timing_component.register_temporary_effect(
                    cleanup_effect,
                    self.duration_type,
                    self.duration_value
                )
        
        return result
    
    def _create_default_cleanup(self, target: Any, context: Dict[str, Any]) -> Optional[Effect]:
        """Create a default cleanup effect based on the wrapped effect type."""
        if isinstance(self.wrapped_effect, GrantProperty):
            return RemoveProperty(self.wrapped_effect.property_name)
        elif isinstance(self.wrapped_effect, ModifyStat):
            return ModifyStat(
                self.wrapped_effect.stat_name, 
                -self.wrapped_effect.modifier,
                "permanent"
            )
        return None
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        # Forward events from wrapped effect
        events = self.wrapped_effect.get_events(target, context, result)
        
        # Add duration info to events
        for event in events:
            event['additional_data'] = event.get('additional_data', {})
            event['additional_data']['duration_type'] = self.duration_type
            event['additional_data']['duration_value'] = self.duration_value
        
        return events
    
    def __str__(self) -> str:
        return f"{self.wrapped_effect} (until {self.duration_type})"


class PreventReadying(Effect):
    """Prevent characters from readying during ready step."""
    
    def __init__(self, target_selector: Optional[Callable] = None, condition: Optional[Callable] = None):
        self.target_selector = target_selector  # Function to select which characters to prevent
        self.condition = condition  # Additional condition to check
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Grant property that prevents readying
        if not hasattr(target, 'metadata'):
            target.metadata = {}
        target.metadata['prevent_readying'] = True
        
        # Store the condition if provided
        if self.condition:
            target.metadata['readying_condition'] = self.condition
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        from ....engine.event_system import GameEvent
        return [{
            'type': GameEvent.READYING_PREVENTED,
            'target': target,
            'source': context.get('source'),
            'additional_data': {
                'has_condition': self.condition is not None,
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "prevent readying"


class DynamicCostModification(Effect):
    """Modify the cost of playing cards based on dynamic conditions."""
    
    def __init__(self, cost_modifier: Union[int, Callable], condition: Callable[[Any, Dict], bool], applies_to: str = "self"):
        self.cost_modifier = cost_modifier  # Can be int or function that returns int
        self.condition = condition  # Function that evaluates when modifier applies
        self.applies_to = applies_to  # "self", "all_cards", specific card types
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Calculate the actual modifier value if it's a function
        if callable(self.cost_modifier):
            modifier_value = self.cost_modifier(target, context)
        else:
            modifier_value = self.cost_modifier
            
        # Register cost modifier with game state
        game_state = context.get('game_state')
        if game_state and hasattr(game_state, 'cost_modifiers'):
            modifier_info = {
                'source': target,
                'modifier': modifier_value,
                'condition': self.condition,
                'applies_to': self.applies_to,
                'dynamic_calculator': self.cost_modifier if callable(self.cost_modifier) else None
            }
            game_state.cost_modifiers.append(modifier_info)
        elif hasattr(target, 'metadata'):
            # Store on target as fallback
            if 'cost_modifiers' not in target.metadata:
                target.metadata['cost_modifiers'] = []
            target.metadata['cost_modifiers'].append({
                'modifier': modifier_value,
                'condition': self.condition,
                'applies_to': self.applies_to,
                'dynamic_calculator': self.cost_modifier if callable(self.cost_modifier) else None
            })
        
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        from ....engine.event_system import GameEvent
        # Calculate modifier value for event reporting
        if callable(self.cost_modifier):
            modifier_value = self.cost_modifier(target, context)
        else:
            modifier_value = self.cost_modifier
            
        return [{
            'type': GameEvent.COST_MODIFIER_APPLIED,
            'target': target,
            'source': context.get('source'),
            'additional_data': {
                'cost_modifier': modifier_value,
                'applies_to': self.applies_to,
                'ability_name': context.get('ability_name', 'Unknown'),
                'is_dynamic': callable(self.cost_modifier)
            }
        }]
    
    def __str__(self) -> str:
        if callable(self.cost_modifier):
            return f"dynamic cost modification ({self.applies_to})"
        else:
            sign = "+" if self.cost_modifier >= 0 else ""
            return f"cost {sign}{self.cost_modifier} ({self.applies_to})"


class TemporaryEffectCleanup(Effect):
    """Clean up a temporary effect that has expired."""
    
    def __init__(self, expired_effect: Any):
        self.expired_effect = expired_effect
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Execute cleanup for the expired effect
        if hasattr(self.expired_effect, 'cleanup'):
            # If effect has custom cleanup method
            self.expired_effect.cleanup(target, context)
        else:
            # Default cleanup behavior
            self._default_cleanup(target, context)
        
        return target
    
    def _default_cleanup(self, target: Any, context: Dict[str, Any]) -> None:
        """Default cleanup behavior for common effect types."""
        if isinstance(self.expired_effect, GrantProperty):
            # Remove the granted property
            if hasattr(target, 'metadata') and self.expired_effect.property_name in target.metadata:
                del target.metadata[self.expired_effect.property_name]
        
        elif isinstance(self.expired_effect, ModifyStat):
            # Reverse the stat modification
            if hasattr(target, self.expired_effect.stat_name):
                current_value = getattr(target, self.expired_effect.stat_name)
                new_value = current_value - self.expired_effect.modifier
                setattr(target, self.expired_effect.stat_name, new_value)
            elif hasattr(target, 'metadata'):
                stat_modifier_key = f'{self.expired_effect.stat_name}_modifier'
                if stat_modifier_key in target.metadata:
                    current_modifier = target.metadata[stat_modifier_key]
                    new_modifier = current_modifier - self.expired_effect.modifier
                    if new_modifier == 0:
                        del target.metadata[stat_modifier_key]
                    else:
                        target.metadata[stat_modifier_key] = new_modifier
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        from ....engine.event_system import GameEvent
        return [{
            'type': GameEvent.EFFECT_EXPIRED,
            'target': target,
            'source': context.get('source'),
            'additional_data': {
                'expired_effect': str(self.expired_effect),
                'reason': context.get('reason', 'duration_expired')
            }
        }]
    
    def __str__(self) -> str:
        return f"cleanup expired {self.expired_effect}"