"""Composable effect system for abilities."""

from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Dict, Optional
from dataclasses import dataclass
from enum import Enum


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
            
        if hasattr(target, f'add_{self.stat}_bonus'):
            getattr(target, f'add_{self.stat}_bonus')(self.amount, self.duration)
        elif hasattr(target, f'modify_{self.stat}'):
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
            return target
        
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


class BanishCharacter(Effect):
    """Banish target character."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'banish'):
            target.banish()
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
            'player': target.controller,
            'additional_data': {
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'banishment_cause': 'ability',
                'ability_name': context.get('ability_name', 'Unknown')
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
    
    def __init__(self, strength_bonus: int):
        self.strength_bonus = strength_bonus
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # Apply temporary strength bonus during challenge
        if hasattr(target, 'add_strength_bonus'):
            target.add_strength_bonus(self.strength_bonus, "this_challenge")
        return target
    
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
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return f"challenger +{self.strength_bonus}"


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
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'exerted'):
            target.exerted = False
        return target
    
    def get_events(self, target: Any, context: Dict[str, Any], result: Any) -> List[Dict[str, Any]]:
        """Get events for readying character."""
        if not hasattr(target, 'controller'):
            return []
        
        # Import here to avoid circular imports
        from ....engine.event_system import GameEvent
        
        return [{
            'type': GameEvent.CHARACTER_READIED,
            'target': target,
            'source': context.get('source') or context.get('ability_owner'),
            'player': target.controller,
            'additional_data': {
                'character_name': target.name if hasattr(target, 'name') else 'Unknown Character',
                'ability_name': context.get('ability_name', 'Unknown')
            }
        }]
    
    def __str__(self) -> str:
        return "ready character"


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