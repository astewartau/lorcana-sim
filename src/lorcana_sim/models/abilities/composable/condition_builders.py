"""
Enhanced condition builders for complex ability triggers.

This system allows creating sophisticated conditions like:
- during_opponent_turn() & is_illusion() & same_controller()
- has_character_named("Anna") & current_turn()
- character_count(lambda c: "Dreamborn" in c.subtypes) >= 3
"""

from typing import Any, Dict, Callable, List, Optional, Union
from abc import ABC, abstractmethod


class Condition(ABC):
    """Base class for composable conditions."""
    
    @abstractmethod
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        """Evaluate this condition given a target and context."""
        pass
    
    def __and__(self, other: 'Condition') -> 'AndCondition':
        """Combine conditions with AND logic."""
        return AndCondition(self, other)
    
    def __or__(self, other: 'Condition') -> 'OrCondition':
        """Combine conditions with OR logic."""
        return OrCondition(self, other)
    
    def __invert__(self) -> 'NotCondition':
        """Negate this condition."""
        return NotCondition(self)
    
    @abstractmethod
    def __str__(self) -> str:
        """String representation of this condition."""
        pass


class LambdaCondition(Condition):
    """Condition that wraps a lambda function."""
    
    def __init__(self, func: Callable[[Any, Dict[str, Any]], bool], description: str = "Custom condition"):
        self.func = func
        self.description = description
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        return self.func(target, context)
    
    def __str__(self) -> str:
        return self.description


class AndCondition(Condition):
    """Condition that requires ALL sub-conditions to be true."""
    
    def __init__(self, *conditions: Condition):
        self.conditions = list(conditions)
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        return all(condition.evaluate(target, context) for condition in self.conditions)
    
    def __str__(self) -> str:
        return f"({' AND '.join(str(c) for c in self.conditions)})"


class OrCondition(Condition):
    """Condition that requires ANY sub-condition to be true."""
    
    def __init__(self, *conditions: Condition):
        self.conditions = list(conditions)
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        return any(condition.evaluate(target, context) for condition in self.conditions)
    
    def __str__(self) -> str:
        return f"({' OR '.join(str(c) for c in self.conditions)})"


class NotCondition(Condition):
    """Condition that negates another condition."""
    
    def __init__(self, condition: Condition):
        self.condition = condition
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        return not self.condition.evaluate(target, context)
    
    def __str__(self) -> str:
        return f"NOT({self.condition})"


# =============================================================================
# TURN AND PLAYER CONDITIONS
# =============================================================================

class DuringOpponentTurnCondition(Condition):
    """True when it's the opponent's turn relative to the ability owner."""
    
    def __init__(self, ability_owner: Any):
        self.ability_owner = ability_owner
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        game_state = context.get('game_state')
        if not game_state or not hasattr(self.ability_owner, 'controller'):
            return False
        
        return game_state.current_player != self.ability_owner.controller
    
    def __str__(self) -> str:
        return "during opponent's turn"


class DuringControllerTurnCondition(Condition):
    """True when it's the controller's turn."""
    
    def __init__(self, ability_owner: Any):
        self.ability_owner = ability_owner
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        game_state = context.get('game_state')
        if not game_state or not hasattr(self.ability_owner, 'controller'):
            return False
        
        return game_state.current_player == self.ability_owner.controller
    
    def __str__(self) -> str:
        return "during controller's turn"


class SameControllerCondition(Condition):
    """True when target has same controller as ability owner."""
    
    def __init__(self, ability_owner: Any):
        self.ability_owner = ability_owner
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        if not hasattr(self.ability_owner, 'controller') or not hasattr(target, 'controller'):
            return False
        
        return target.controller == self.ability_owner.controller
    
    def __str__(self) -> str:
        return "same controller"


class OpponentControllerCondition(Condition):
    """True when target has different controller than ability owner."""
    
    def __init__(self, ability_owner: Any):
        self.ability_owner = ability_owner
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        if not hasattr(self.ability_owner, 'controller') or not hasattr(target, 'controller'):
            return False
        
        return target.controller != self.ability_owner.controller
    
    def __str__(self) -> str:
        return "opponent controller"


# =============================================================================
# CHARACTER TYPE AND PROPERTY CONDITIONS
# =============================================================================

class HasSubtypeCondition(Condition):
    """True when target has a specific subtype."""
    
    def __init__(self, subtype: str):
        self.subtype = subtype
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        if not hasattr(target, 'subtypes'):
            return False
        
        return self.subtype in target.subtypes
    
    def __str__(self) -> str:
        return f"has subtype '{self.subtype}'"


class HasNameCondition(Condition):
    """True when target has a specific name (partial match)."""
    
    def __init__(self, name: str, exact: bool = False):
        self.name = name
        self.exact = exact
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        if not hasattr(target, 'name'):
            return False
        
        if self.exact:
            return target.name == self.name
        else:
            return self.name in target.name
    
    def __str__(self) -> str:
        match_type = "exactly" if self.exact else "contains"
        return f"name {match_type} '{self.name}'"


class StatCondition(Condition):
    """True when target's stat meets a condition."""
    
    def __init__(self, stat_name: str, operator: str, value: int):
        self.stat_name = stat_name
        self.operator = operator
        self.value = value
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        if not hasattr(target, self.stat_name):
            return False
        
        stat_value = getattr(target, self.stat_name)
        
        if self.operator == "==":
            return stat_value == self.value
        elif self.operator == "!=":
            return stat_value != self.value
        elif self.operator == "<":
            return stat_value < self.value
        elif self.operator == "<=":
            return stat_value <= self.value
        elif self.operator == ">":
            return stat_value > self.value
        elif self.operator == ">=":
            return stat_value >= self.value
        
        return False
    
    def __str__(self) -> str:
        return f"{self.stat_name} {self.operator} {self.value}"


class IsDamagedCondition(Condition):
    """True when target has damage."""
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        return hasattr(target, 'damage') and target.damage > 0
    
    def __str__(self) -> str:
        return "is damaged"


class IsExertedCondition(Condition):
    """True when target is exerted."""
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        return hasattr(target, 'exerted') and target.exerted
    
    def __str__(self) -> str:
        return "is exerted"


# =============================================================================
# BOARD STATE CONDITIONS
# =============================================================================

class HasCharacterNamedCondition(Condition):
    """True when controller has a character with specific name in play."""
    
    def __init__(self, character_name: str, ability_owner: Any):
        self.character_name = character_name
        self.ability_owner = ability_owner
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        game_state = context.get('game_state')
        if not game_state or not hasattr(self.ability_owner, 'controller'):
            return False
        
        controller = self.ability_owner.controller
        
        for player in game_state.players:
            if player == controller:
                for char in player.characters_in_play:
                    if hasattr(char, 'name') and self.character_name in char.name:
                        return True
        
        return False
    
    def __str__(self) -> str:
        return f"has character named '{self.character_name}'"


class CharacterCountCondition(Condition):
    """True when character count meets a condition."""
    
    def __init__(self, filter_func: Callable[[Any], bool], operator: str, count: int, ability_owner: Any):
        self.filter_func = filter_func
        self.operator = operator
        self.count = count
        self.ability_owner = ability_owner
    
    def evaluate(self, target: Any, context: Dict[str, Any]) -> bool:
        game_state = context.get('game_state')
        if not game_state or not hasattr(self.ability_owner, 'controller'):
            return False
        
        controller = self.ability_owner.controller
        matching_count = 0
        
        for player in game_state.players:
            if player == controller:
                for char in player.characters_in_play:
                    if self.filter_func(char):
                        matching_count += 1
        
        if self.operator == "==":
            return matching_count == self.count
        elif self.operator == "!=":
            return matching_count != self.count
        elif self.operator == "<":
            return matching_count < self.count
        elif self.operator == "<=":
            return matching_count <= self.count
        elif self.operator == ">":
            return matching_count > self.count
        elif self.operator == ">=":
            return matching_count >= self.count
        
        return False
    
    def __str__(self) -> str:
        return f"character count {self.operator} {self.count}"


# =============================================================================
# FACTORY FUNCTIONS FOR EASY CONDITION BUILDING
# =============================================================================

def during_opponent_turn(ability_owner: Any) -> DuringOpponentTurnCondition:
    """Create condition: during opponent's turn."""
    return DuringOpponentTurnCondition(ability_owner)

def during_controller_turn(ability_owner: Any) -> DuringControllerTurnCondition:
    """Create condition: during controller's turn."""
    return DuringControllerTurnCondition(ability_owner)

def same_controller(ability_owner: Any) -> SameControllerCondition:
    """Create condition: target has same controller as ability owner."""
    return SameControllerCondition(ability_owner)

def opponent_controller(ability_owner: Any) -> OpponentControllerCondition:
    """Create condition: target has different controller than ability owner."""
    return OpponentControllerCondition(ability_owner)

def is_illusion() -> HasSubtypeCondition:
    """Create condition: target is an Illusion."""
    return HasSubtypeCondition("Illusion")

def is_dreamborn() -> HasSubtypeCondition:
    """Create condition: target is Dreamborn."""
    return HasSubtypeCondition("Dreamborn")

def is_storyborn() -> HasSubtypeCondition:
    """Create condition: target is Storyborn."""
    return HasSubtypeCondition("Storyborn")

def is_floodborn() -> HasSubtypeCondition:
    """Create condition: target is Floodborn."""
    return HasSubtypeCondition("Floodborn")

def has_name(name: str, exact: bool = False) -> HasNameCondition:
    """Create condition: target has specific name."""
    return HasNameCondition(name, exact)

def is_damaged() -> IsDamagedCondition:
    """Create condition: target is damaged."""
    return IsDamagedCondition()

def is_exerted() -> IsExertedCondition:
    """Create condition: target is exerted."""
    return IsExertedCondition()

def strength_equals(value: int) -> StatCondition:
    """Create condition: target strength equals value."""
    return StatCondition("strength", "==", value)

def strength_greater_than(value: int) -> StatCondition:
    """Create condition: target strength > value."""
    return StatCondition("strength", ">", value)

def willpower_equals(value: int) -> StatCondition:
    """Create condition: target willpower equals value."""
    return StatCondition("willpower", "==", value)

def lore_equals(value: int) -> StatCondition:
    """Create condition: target lore equals value."""
    return StatCondition("lore", "==", value)

def has_character_named(name: str, ability_owner: Any) -> HasCharacterNamedCondition:
    """Create condition: controller has character named X."""
    return HasCharacterNamedCondition(name, ability_owner)

def character_count(filter_func: Callable[[Any], bool], operator: str, count: int, ability_owner: Any) -> CharacterCountCondition:
    """Create condition: number of matching characters meets criteria."""
    return CharacterCountCondition(filter_func, operator, count, ability_owner)

def custom_condition(func: Callable[[Any, Dict[str, Any]], bool], description: str = "Custom condition") -> LambdaCondition:
    """Create custom condition from lambda function."""
    return LambdaCondition(func, description)

# Convenience functions for common patterns
def dreamborn_count_at_least(count: int, ability_owner: Any) -> CharacterCountCondition:
    """Create condition: at least N Dreamborn characters in play."""
    return character_count(lambda c: "Dreamborn" in getattr(c, 'subtypes', []), ">=", count, ability_owner)

def damaged_character_exists(ability_owner: Any) -> CharacterCountCondition:
    """Create condition: at least one damaged character in play."""
    return character_count(lambda c: getattr(c, 'damage', 0) > 0, ">=", 1, ability_owner)