"""Target selection system for composable abilities."""

from abc import ABC, abstractmethod
from typing import List, Any, Callable, Dict, Set, Optional
from dataclasses import dataclass


class TargetSelector(ABC):
    """Base class for target selection."""
    
    @abstractmethod
    def select(self, context: Dict[str, Any]) -> List[Any]:
        """Select targets from the game state."""
        pass
    
    def __add__(self, other: 'TargetSelector') -> 'UnionSelector':
        """Union of targets with +"""
        return UnionSelector([self, other])
    
    def __sub__(self, other: 'TargetSelector') -> 'DifferenceSelector':
        """Difference of targets with -"""
        return DifferenceSelector(self, other)
    
    def __and__(self, other: 'TargetSelector') -> 'IntersectionSelector':
        """Intersection of targets with &"""
        return IntersectionSelector(self, other)
    
    def __str__(self) -> str:
        return self.__class__.__name__


class CharacterSelector(TargetSelector):
    """Select characters based on filter."""
    
    def __init__(self, filter_func: Callable[[Any, Dict], bool] = None, count: int = 1):
        self.filter_func = filter_func or (lambda char, ctx: True)
        self.count = count
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        game_state = context.get('game_state')
        if not game_state:
            # Try to get from event_context
            event_context = context.get('event_context')
            if event_context:
                game_state = event_context.game_state
        
        if not game_state:
            return []
        
        # Get all characters from all players
        all_characters = []
        if hasattr(game_state, 'all_players'):
            for player in game_state.all_players:
                if hasattr(player, 'characters_in_play'):
                    all_characters.extend(player.characters_in_play)
        elif hasattr(game_state, 'current_player') and hasattr(game_state, 'opponent'):
            # Handle both players
            for player in [game_state.current_player, game_state.opponent]:
                if hasattr(player, 'characters_in_play'):
                    all_characters.extend(player.characters_in_play)
        
        # Apply filter
        valid_characters = [char for char in all_characters 
                          if self.filter_func(char, context)]
        
        # Return up to count characters
        # In real implementation, this would trigger targeting UI if count > len(valid_characters)
        return valid_characters[:self.count]
    
    def __str__(self) -> str:
        return f"CharacterSelector(count={self.count})"


class SelfSelector(TargetSelector):
    """Select the ability's owner character."""
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        # First try to get the ability owner (the character that has the ability)
        ability_owner = context.get('ability_owner')
        if ability_owner:
            return [ability_owner]
        
        # Fallback to event source (for backward compatibility)
        source = context.get('source')
        if not source:
            event_context = context.get('event_context')
            if event_context:
                source = event_context.source
        return [source] if source else []
    
    def __str__(self) -> str:
        return "Self"


class NoTargetSelector(TargetSelector):
    """Select no targets (for prevention effects)."""
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        return []
    
    def __str__(self) -> str:
        return "NoTarget"


class EventTargetSelector(TargetSelector):
    """Select the target of the triggering event."""
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        event_context = context.get('event_context')
        if event_context and event_context.target:
            return [event_context.target]
        return []
    
    def __str__(self) -> str:
        return "EventTarget"


class EventSourceSelector(TargetSelector):
    """Select the source of the triggering event."""
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        event_context = context.get('event_context')
        if event_context and event_context.source:
            return [event_context.source]
        return []
    
    def __str__(self) -> str:
        return "EventSource"


class UnionSelector(TargetSelector):
    """Union of multiple selectors."""
    
    def __init__(self, selectors: List[TargetSelector]):
        self.selectors = selectors
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        all_targets = []
        seen = set()
        for selector in self.selectors:
            for target in selector.select(context):
                # Use id to handle deduplication
                target_id = id(target)
                if target_id not in seen:
                    seen.add(target_id)
                    all_targets.append(target)
        return all_targets
    
    def __str__(self) -> str:
        return f"({' + '.join(str(s) for s in self.selectors)})"


class DifferenceSelector(TargetSelector):
    """Difference between two selectors."""
    
    def __init__(self, include_selector: TargetSelector, exclude_selector: TargetSelector):
        self.include_selector = include_selector
        self.exclude_selector = exclude_selector
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        included = self.include_selector.select(context)
        excluded_ids = {id(t) for t in self.exclude_selector.select(context)}
        return [t for t in included if id(t) not in excluded_ids]
    
    def __str__(self) -> str:
        return f"({self.include_selector} - {self.exclude_selector})"


class IntersectionSelector(TargetSelector):
    """Intersection of two selectors."""
    
    def __init__(self, selector1: TargetSelector, selector2: TargetSelector):
        self.selector1 = selector1
        self.selector2 = selector2
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        targets1 = self.selector1.select(context)
        target2_ids = {id(t) for t in self.selector2.select(context)}
        return [t for t in targets1 if id(t) in target2_ids]
    
    def __str__(self) -> str:
        return f"({self.selector1} & {self.selector2})"


# =============================================================================
# FILTER FUNCTIONS FOR ALL EXISTING ABILITIES
# =============================================================================

def friendly_filter(character: Any, context: Dict[str, Any]) -> bool:
    """Filter for friendly characters."""
    source = context.get('source')
    if not source:
        event_context = context.get('event_context')
        if event_context:
            source = event_context.source
    
    if not source or not hasattr(source, 'controller'):
        return False
    return character.controller == source.controller


def enemy_filter(character: Any, context: Dict[str, Any]) -> bool:
    """Filter for enemy characters."""
    source = context.get('source')
    if not source:
        event_context = context.get('event_context')
        if event_context:
            source = event_context.source
    
    if not source or not hasattr(source, 'controller'):
        return False
    return character.controller != source.controller


def ready_filter(character: Any, context: Dict[str, Any]) -> bool:
    """Filter for ready (non-exerted) characters."""
    return not getattr(character, 'exerted', False)


def exerted_filter(character: Any, context: Dict[str, Any]) -> bool:
    """Filter for exerted characters."""
    return getattr(character, 'exerted', False)


def damaged_filter(character: Any, context: Dict[str, Any]) -> bool:
    """Filter for damaged characters."""
    return getattr(character, 'damage', 0) > 0


def undamaged_filter(character: Any, context: Dict[str, Any]) -> bool:
    """Filter for undamaged characters."""
    return getattr(character, 'damage', 0) == 0


def has_ability_filter(ability_name: str):
    """Create a filter for characters with a specific ability."""
    def filter_func(character: Any, context: Dict[str, Any]) -> bool:
        if not hasattr(character, 'abilities'):
            return False
        return any(ability.name == ability_name for ability in character.abilities)
    return filter_func


def cost_filter(min_cost: int = 0, max_cost: int = 999):
    """Create a cost-based filter."""
    def filter_func(character: Any, context: Dict[str, Any]) -> bool:
        cost = getattr(character, 'cost', 0)
        return min_cost <= cost <= max_cost
    return filter_func


def subtype_filter(subtype: str):
    """Create a subtype-based filter."""
    def filter_func(character: Any, context: Dict[str, Any]) -> bool:
        if hasattr(character, 'has_subtype'):
            return character.has_subtype(subtype)
        subtypes = getattr(character, 'subtypes', [])
        return subtype in subtypes
    return filter_func


def not_self_filter(character: Any, context: Dict[str, Any]) -> bool:
    """Filter for characters that are not the source."""
    source = context.get('source')
    if not source:
        event_context = context.get('event_context')
        if event_context:
            source = event_context.source
    return character != source


def bodyguard_filter(character: Any, context: Dict[str, Any]) -> bool:
    """Filter for characters with Bodyguard that are ready."""
    if not ready_filter(character, context):
        return False
    return has_ability_filter("Bodyguard")(character, context)


# =============================================================================
# PRE-BUILT SELECTORS FOR COMMON USE CASES
# =============================================================================

# Single target selectors
SELF = SelfSelector()
EVENT_TARGET = EventTargetSelector()
EVENT_SOURCE = EventSourceSelector()
NO_TARGET = NoTargetSelector()

# Friendly selectors
FRIENDLY_CHARACTER = CharacterSelector(friendly_filter)
FRIENDLY_READY = CharacterSelector(lambda c, ctx: friendly_filter(c, ctx) and ready_filter(c, ctx))
FRIENDLY_EXERTED = CharacterSelector(lambda c, ctx: friendly_filter(c, ctx) and exerted_filter(c, ctx))
FRIENDLY_DAMAGED = CharacterSelector(lambda c, ctx: friendly_filter(c, ctx) and damaged_filter(c, ctx))
ALL_FRIENDLY = CharacterSelector(friendly_filter, count=999)
OTHER_FRIENDLY = CharacterSelector(lambda c, ctx: friendly_filter(c, ctx) and not_self_filter(c, ctx), count=999)

# Enemy selectors
ENEMY_CHARACTER = CharacterSelector(enemy_filter)
ENEMY_EXERTED = CharacterSelector(lambda c, ctx: enemy_filter(c, ctx) and exerted_filter(c, ctx))
ENEMY_DAMAGED = CharacterSelector(lambda c, ctx: enemy_filter(c, ctx) and damaged_filter(c, ctx))
ALL_ENEMIES = CharacterSelector(enemy_filter, count=999)

# Special selectors
DAMAGED_CHARACTER = CharacterSelector(damaged_filter)
ALL_CHARACTERS = CharacterSelector(lambda c, ctx: True, count=999)
ALL_OTHER_CHARACTERS = CharacterSelector(not_self_filter, count=999)
BODYGUARD_CHARACTER = CharacterSelector(bodyguard_filter)


class PlayerSelector(TargetSelector):
    """Select players based on filter."""
    
    def __init__(self, filter_func: Callable[[Any, Dict], bool] = None, count: int = 1):
        self.filter_func = filter_func
        self.count = count
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        game_state = context.get('game_state')
        if not game_state:
            event_context = context.get('event_context')
            if event_context:
                game_state = event_context.game_state
        
        if not game_state:
            return []
        
        # Get ability owner to determine controller
        ability_owner = context.get('ability_owner')
        if ability_owner and hasattr(ability_owner, 'controller'):
            controller = ability_owner.controller
            if self.filter_func is None:  # Default to controller when no filter
                return [controller]
        
        # Get all players
        all_players = []
        if hasattr(game_state, 'players'):
            all_players = game_state.players
        elif hasattr(game_state, 'current_player') and hasattr(game_state, 'opponent'):
            all_players = [game_state.current_player, game_state.opponent]
        
        # Apply filter if we have one
        if self.filter_func:
            valid_players = [player for player in all_players 
                            if self.filter_func(player, context)]
        else:
            # No filter means select all players
            valid_players = all_players
        
        return valid_players[:self.count]


def opposing_player_filter(player: Any, context: Dict[str, Any]) -> bool:
    """Filter for opposing players."""
    ability_owner = context.get('ability_owner')
    if ability_owner and hasattr(ability_owner, 'controller'):
        return player != ability_owner.controller
    return False


class TargetWithCostConstraintSelector(TargetSelector):
    """Select targets with cost constraints."""
    
    def __init__(self, cost_constraint: Callable[[Any], bool], valid_types: List[str] = None, count: int = 1):
        self.cost_constraint = cost_constraint
        self.valid_types = valid_types or ['character', 'item', 'location']
        self.count = count
    
    def select(self, context: Dict[str, Any]) -> List[Any]:
        game_state = context.get('game_state')
        if not game_state:
            event_context = context.get('event_context')
            if event_context:
                game_state = event_context.game_state
        
        if not game_state:
            return []
        
        # Get all valid targets from all players
        all_targets = []
        if hasattr(game_state, 'players'):
            for player in game_state.players:
                if 'character' in self.valid_types and hasattr(player, 'characters_in_play'):
                    all_targets.extend(player.characters_in_play)
                if 'item' in self.valid_types and hasattr(player, 'items_in_play'):
                    all_targets.extend(player.items_in_play)
                if 'location' in self.valid_types and hasattr(player, 'locations_in_play'):
                    all_targets.extend(player.locations_in_play)
        
        # Apply cost constraint
        valid_targets = [target for target in all_targets 
                        if self.cost_constraint(target)]
        
        return valid_targets[:self.count]


def TARGET_WITH_COST_CONSTRAINT(cost_constraint: Callable[[Any], bool], valid_types: List[str] = None):
    return TargetWithCostConstraintSelector(cost_constraint, valid_types)


# Player selectors (defined after PlayerSelector class)
CONTROLLER = PlayerSelector()
ALL_OPPONENTS = PlayerSelector(opposing_player_filter, count=999)


# =============================================================================
# FILTER COMBINATION FUNCTIONS
# =============================================================================

def and_filters(*filters):
    """Combine multiple filters with AND logic."""
    def combined_filter(character: Any, context: Dict[str, Any]) -> bool:
        return all(f(character, context) for f in filters)
    return combined_filter


def or_filters(*filters):
    """Combine multiple filters with OR logic."""
    def combined_filter(character: Any, context: Dict[str, Any]) -> bool:
        return any(f(character, context) for f in filters)
    return combined_filter


def not_filter(filter_func):
    """Negate a filter."""
    def negated_filter(character: Any, context: Dict[str, Any]) -> bool:
        return not filter_func(character, context)
    return negated_filter