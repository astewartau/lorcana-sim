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
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        result = target
        for effect in self.effects:
            result = effect.apply(result, context)
        return result
    
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
    
    def __str__(self) -> str:
        sign = "+" if self.amount >= 0 else ""
        return f"{self.stat} {sign}{self.amount} ({self.duration})"


class DrawCards(Effect):
    """Draw cards effect."""
    
    def __init__(self, count: int):
        self.count = count
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        controller = getattr(target, 'controller', context.get('source', {}).get('controller'))
        if controller and hasattr(controller, 'draw_cards'):
            controller.draw_cards(self.count)
        return target
    
    def __str__(self) -> str:
        return f"draw {self.count} card{'s' if self.count != 1 else ''}"


class BanishCharacter(Effect):
    """Banish target character."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'banish'):
            target.banish()
        return target
    
    def __str__(self) -> str:
        return "banish character"


class ReturnToHand(Effect):
    """Return target to owner's hand."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'controller') and hasattr(target.controller, 'return_to_hand'):
            target.controller.return_to_hand(target)
        return target
    
    def __str__(self) -> str:
        return "return to hand"


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
    
    def __str__(self) -> str:
        return "force retarget"


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
    
    def __str__(self) -> str:
        return f"can sing songs (cost {self.singer_cost})"


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
    
    def __str__(self) -> str:
        return f"grant {self.property_name}"


class NoEffect(Effect):
    """No effect (for passive abilities that just modify rules)."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        return target
    
    def __str__(self) -> str:
        return "no effect"


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
PREVENT_TARGETING = PreventEffect("targeting")
NO_EFFECT = NoEffect()