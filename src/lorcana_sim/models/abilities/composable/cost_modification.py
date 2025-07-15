"""Cost modification system for conditional abilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ...cards.base_card import Card
    from ...cards.character_card import CharacterCard
    from ...game.game_state import GameState
    from ...game.player import Player


class CostModificationType(Enum):
    """Types of cost modifications."""
    INK_COST_REDUCTION = "ink_cost_reduction"
    INK_COST_INCREASE = "ink_cost_increase"
    FREE_PLAY = "free_play"
    ALTERNATIVE_COST = "alternative_cost"


@dataclass
class CostModifier:
    """Represents a modification to a card's cost."""
    
    # Core identification
    modifier_id: str
    source_card: 'CharacterCard'
    modification_type: CostModificationType
    
    # Cost modification details
    amount: int = 0  # Reduction/increase amount
    alternative_cost: Optional[Dict[str, Any]] = None  # For alternative costs
    
    # Applicability conditions
    applies_to_filter: Callable[['Card', 'GameState'], bool] = field(default=lambda c, gs: True)
    condition_func: Callable[['GameState', 'CharacterCard'], bool] = field(default=lambda gs, sc: True)
    
    # Priority and stacking
    priority: int = 0  # Higher priority modifiers apply first
    stacks_with_others: bool = True
    
    # State tracking
    is_active: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate cost modifier after creation."""
        if not self.modifier_id:
            raise ValueError("CostModifier must have a non-empty modifier_id")
        if not self.source_card:
            raise ValueError("CostModifier must have a source_card")
    
    def is_applicable_to_card(self, card: 'Card', game_state: 'GameState') -> bool:
        """Check if this modifier applies to the given card."""
        if not self.is_active:
            return False
        
        if not self.condition_func(game_state, self.source_card):
            return False
        
        return self.applies_to_filter(card, game_state)
    
    def calculate_modified_cost(self, original_cost: int, card: 'Card', game_state: 'GameState') -> int:
        """Calculate the modified cost for a card."""
        if not self.is_applicable_to_card(card, game_state):
            return original_cost
        
        if self.modification_type == CostModificationType.INK_COST_REDUCTION:
            return max(0, original_cost - self.amount)
        elif self.modification_type == CostModificationType.INK_COST_INCREASE:
            return original_cost + self.amount
        elif self.modification_type == CostModificationType.FREE_PLAY:
            return 0
        elif self.modification_type == CostModificationType.ALTERNATIVE_COST:
            # Return alternative cost if specified, otherwise original
            if self.alternative_cost and 'ink_cost' in self.alternative_cost:
                return self.alternative_cost['ink_cost']
        
        return original_cost
    
    def activate(self) -> None:
        """Activate this cost modifier."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate this cost modifier."""
        self.is_active = False


@dataclass
class CostModificationManager:
    """Manages all cost modifiers in the game."""
    
    # Track all registered modifiers
    all_modifiers: List[CostModifier] = field(default_factory=list)
    
    # Performance optimization - group by source
    modifiers_by_source: Dict[str, List[CostModifier]] = field(default_factory=dict)
    
    def register_cost_modifier(self, modifier: CostModifier) -> None:
        """Register a cost modifier with the manager."""
        if modifier not in self.all_modifiers:
            self.all_modifiers.append(modifier)
            
            # Group by source for efficiency
            source_id = id(modifier.source_card)
            if source_id not in self.modifiers_by_source:
                self.modifiers_by_source[source_id] = []
            self.modifiers_by_source[source_id].append(modifier)
    
    def unregister_cost_modifier(self, modifier: CostModifier) -> None:
        """Unregister a cost modifier from the manager."""
        if modifier in self.all_modifiers:
            self.all_modifiers.remove(modifier)
            
            # Remove from source grouping
            source_id = id(modifier.source_card)
            if source_id in self.modifiers_by_source:
                self.modifiers_by_source[source_id].remove(modifier)
                if not self.modifiers_by_source[source_id]:
                    del self.modifiers_by_source[source_id]
    
    def get_modified_cost(self, card: 'Card', game_state: 'GameState') -> int:
        """Get the final modified cost for a card after all applicable modifiers."""
        original_cost = getattr(card, 'cost', 0)
        
        # Get all applicable modifiers
        applicable_modifiers = []
        for modifier in self.all_modifiers:
            if modifier.is_applicable_to_card(card, game_state):
                applicable_modifiers.append(modifier)
        
        # Sort by priority (higher priority first)
        applicable_modifiers.sort(key=lambda m: m.priority, reverse=True)
        
        # Apply modifiers in priority order
        current_cost = original_cost
        applied_reductions = 0
        applied_increases = 0
        
        for modifier in applicable_modifiers:
            if modifier.modification_type == CostModificationType.FREE_PLAY:
                # Free play overrides everything
                return 0
            elif modifier.modification_type == CostModificationType.ALTERNATIVE_COST:
                # Alternative cost overrides normal cost calculation
                if modifier.alternative_cost and 'ink_cost' in modifier.alternative_cost:
                    return modifier.alternative_cost['ink_cost']
            elif modifier.modification_type == CostModificationType.INK_COST_REDUCTION:
                if modifier.stacks_with_others or applied_reductions == 0:
                    current_cost = max(0, current_cost - modifier.amount)
                    applied_reductions += 1
            elif modifier.modification_type == CostModificationType.INK_COST_INCREASE:
                if modifier.stacks_with_others or applied_increases == 0:
                    current_cost += modifier.amount
                    applied_increases += 1
        
        return max(0, current_cost)
    
    def get_applicable_modifiers(self, card: 'Card', game_state: 'GameState') -> List[CostModifier]:
        """Get all modifiers that apply to a specific card."""
        applicable = []
        for modifier in self.all_modifiers:
            if modifier.is_applicable_to_card(card, game_state):
                applicable.append(modifier)
        return applicable
    
    def get_modifiers_by_source(self, source_card: 'CharacterCard') -> List[CostModifier]:
        """Get all modifiers created by a specific source card."""
        source_id = id(source_card)
        return self.modifiers_by_source.get(source_id, []).copy()
    
    def activate_modifiers_by_source(self, source_card: 'CharacterCard') -> None:
        """Activate all modifiers from a specific source."""
        for modifier in self.get_modifiers_by_source(source_card):
            modifier.activate()
    
    def deactivate_modifiers_by_source(self, source_card: 'CharacterCard') -> None:
        """Deactivate all modifiers from a specific source."""
        for modifier in self.get_modifiers_by_source(source_card):
            modifier.deactivate()
    
    def clear_all_modifiers(self) -> None:
        """Clear all registered cost modifiers."""
        self.all_modifiers.clear()
        self.modifiers_by_source.clear()
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debugging information about cost modifiers."""
        active_count = len([m for m in self.all_modifiers if m.is_active])
        by_type = {}
        for modifier in self.all_modifiers:
            mod_type = modifier.modification_type.value
            by_type[mod_type] = by_type.get(mod_type, 0) + 1
        
        return {
            'total_modifiers': len(self.all_modifiers),
            'active_modifiers': active_count,
            'modifiers_by_type': by_type,
            'sources_with_modifiers': len(self.modifiers_by_source)
        }


# Cost modifier factory functions
def create_ink_reduction_modifier(modifier_id: str, 
                                source_card: 'CharacterCard',
                                reduction_amount: int,
                                applies_to_filter: Callable[['Card', 'GameState'], bool],
                                condition_func: Callable[['GameState', 'CharacterCard'], bool] = lambda gs, sc: True,
                                priority: int = 0) -> CostModifier:
    """Create an ink cost reduction modifier."""
    return CostModifier(
        modifier_id=modifier_id,
        source_card=source_card,
        modification_type=CostModificationType.INK_COST_REDUCTION,
        amount=reduction_amount,
        applies_to_filter=applies_to_filter,
        condition_func=condition_func,
        priority=priority
    )


def create_character_type_filter(character_subtypes: List[str]) -> Callable[['Card', 'GameState'], bool]:
    """Create a filter that applies to characters with specific subtypes."""
    def filter_func(card: 'Card', game_state: 'GameState') -> bool:
        if not hasattr(card, 'subtypes'):
            return False
        
        for subtype in character_subtypes:
            if hasattr(card, 'has_subtype') and card.has_subtype(subtype):
                return True
        return False
    
    return filter_func


def create_controller_only_filter() -> Callable[['Card', 'GameState'], bool]:
    """Create a filter that only applies to cards controlled by the modifier's source owner."""
    def filter_func(card: 'Card', game_state: 'GameState') -> bool:
        # This would need to be implemented based on how card ownership is tracked
        # For now, assume it applies to all cards
        return True
    
    return filter_func


def create_hand_only_filter() -> Callable[['Card', 'GameState'], bool]:
    """Create a filter that only applies to cards in hand."""
    def filter_func(card: 'Card', game_state: 'GameState') -> bool:
        # Check if card is in any player's hand
        for player in game_state.players:
            if card in player.hand:
                return True
        return False
    
    return filter_func