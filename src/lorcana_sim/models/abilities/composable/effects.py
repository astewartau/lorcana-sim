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
    
    def __str__(self) -> str:
        return f"sing together {self.required_cost}"


class CostModification(Effect):
    """Modify the cost of playing cards or abilities."""
    
    def __init__(self, cost_change: int, target_type: str = "all"):
        self.cost_change = cost_change  # Negative for cost reduction
        self.target_type = target_type  # "all", "characters", "actions", "items"
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        # This effect typically applies to the player's hand or game state
        # Implementation would depend on how cost modifications are tracked
        event_context = context.get('event_context')
        if event_context and event_context.additional_data:
            event_context.additional_data[f'cost_modification_{self.target_type}'] = self.cost_change
        return target
    
    def __str__(self) -> str:
        sign = "+" if self.cost_change >= 0 else ""
        return f"modify {self.target_type} cost by {sign}{self.cost_change}"


class ExertCharacter(Effect):
    """Exert a character."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'exerted'):
            target.exerted = True
        return target
    
    def __str__(self) -> str:
        return "exert character"


class ReadyCharacter(Effect):
    """Ready (un-exert) a character."""
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        if hasattr(target, 'exerted'):
            target.exerted = False
        return target
    
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