"""Composable trigger system for building complex ability triggers with AND/OR logic."""

from typing import Any, Callable
from .triggers import when_event
from ....engine.event_system import GameEvent


class ComposableTrigger:
    """A trigger that can be composed with conditions using & and | operators."""
    
    def __init__(self, event_type: GameEvent, source_filter: Callable[[Any, Any], bool]):
        self.event_type = event_type
        self.source_filter = source_filter
    
    def __and__(self, condition: Callable[[Any, Any], bool]) -> 'ComposableTrigger':
        """AND composition using & operator."""
        def enhanced_filter(source, event_context):
            # First check the base trigger
            if not self.source_filter(source, event_context):
                return False  # Short-circuit for AND
            # Then check the condition
            return condition(source, event_context)
        
        return ComposableTrigger(self.event_type, enhanced_filter)
    
    def __or__(self, other) -> 'ComposableTrigger':
        """OR composition using | operator."""
        if isinstance(other, ComposableTrigger):
            # Combining two triggers - need to handle different event types
            def combined_filter(source, event_context):
                # Check if this event matches either trigger
                if event_context.event_type == self.event_type:
                    return self.source_filter(source, event_context)
                elif event_context.event_type == other.event_type:
                    return other.source_filter(source, event_context)
                return False
            
            # For OR of different triggers, we need to register for both events
            # This is more complex and might need special handling
            return ComposableTrigger(self.event_type, combined_filter)
        else:
            # Combining with a condition
            def enhanced_filter(source, event_context):
                # Either the base trigger matches OR the condition is true
                base_matches = self.source_filter(source, event_context)
                condition_matches = other(source, event_context)
                return base_matches or condition_matches
            
            return ComposableTrigger(self.event_type, enhanced_filter)
    
    def __add__(self, condition: Callable[[Any, Any], bool]) -> 'ComposableTrigger':
        """Default to AND for + operator."""
        return self.__and__(condition)
    
    def to_trigger(self):
        """Convert back to a standard trigger for use in quick_ability."""
        return when_event(self.event_type, source_filter=self.source_filter)


# =============================================================================
# CONDITION FUNCTIONS
# =============================================================================

def character_present(name: str = None, subtype: str = None, controller: str = None) -> Callable[[Any, Any], bool]:
    """Returns a condition function that checks if specified character is in play.
    
    Args:
        name: Character name to look for (partial match)
        subtype: Character subtype to look for
        controller: 'self' (default) or 'opponent' - whose characters to check
    """
    def condition(character, event_context):
        game_state = event_context.game_state
        if not game_state or not hasattr(character, 'controller'):
            return False
        
        # Determine which player's characters to check
        if controller == 'opponent':
            # Find the opponent
            controller_to_check = None
            for player in game_state.players:
                if player != character.controller:
                    controller_to_check = player
                    break
        else:
            # Default to character's controller
            controller_to_check = character.controller
        
        if not controller_to_check:
            return False
        
        # Check characters in play
        for char in controller_to_check.characters_in_play:
            if name and hasattr(char, 'name') and name in char.name:
                return True
            if subtype and hasattr(char, 'subtypes') and subtype in char.subtypes:
                return True
        
        return False
    
    return condition


def card_type_in_play(card_type: str, controller: str = None) -> Callable[[Any, Any], bool]:
    """Returns condition for checking if card type/subtype is in play."""
    return character_present(subtype=card_type, controller=controller)


def player_has_lore(amount: int, operator: str = ">=") -> Callable[[Any, Any], bool]:
    """Returns condition for checking player lore.
    
    Args:
        amount: Lore amount to compare
        operator: ">=", "<=", "==", ">", "<"
    """
    def condition(character, event_context):
        if not hasattr(character, 'controller'):
            return False
        
        controller = character.controller
        player_lore = controller.lore
        
        if operator == ">=":
            return player_lore >= amount
        elif operator == "<=":
            return player_lore <= amount
        elif operator == "==":
            return player_lore == amount
        elif operator == ">":
            return player_lore > amount
        elif operator == "<":
            return player_lore < amount
        else:
            return False
    
    return condition


def not_condition(condition: Callable[[Any, Any], bool]) -> Callable[[Any, Any], bool]:
    """Negate a condition."""
    def negated_condition(character, event_context):
        return not condition(character, event_context)
    return negated_condition


# =============================================================================
# HELPER CONDITION FUNCTIONS
# =============================================================================

def high_lore(amount: int = 3) -> Callable[[Any, Any], bool]:
    """Check if player has high lore (3+ by default)."""
    return player_has_lore(amount)


# =============================================================================
# ENHANCED BASE TRIGGERS
# =============================================================================

def when_enters_play(character: Any) -> ComposableTrigger:
    """Trigger when the specified character enters play."""
    def source_filter(source, event_context):
        return source == character
    
    return ComposableTrigger(GameEvent.CHARACTER_ENTERS_PLAY, source_filter)


def when_quests(character: Any) -> ComposableTrigger:
    """Trigger when the specified character quests."""
    def source_filter(source, event_context):
        return source == character
    
    return ComposableTrigger(GameEvent.CHARACTER_QUESTS, source_filter)


def when_takes_damage(character: Any) -> ComposableTrigger:
    """Trigger when the specified character takes damage."""
    def source_filter(source, event_context):
        return source == character
    
    return ComposableTrigger(GameEvent.CHARACTER_TAKES_DAMAGE, source_filter)


def when_deals_damage(character: Any) -> ComposableTrigger:
    """Trigger when the specified character deals damage."""
    def source_filter(source, event_context):
        return source == character
    
    return ComposableTrigger(GameEvent.CHARACTER_DEALS_DAMAGE, source_filter)


def when_banished(character: Any) -> ComposableTrigger:
    """Trigger when the specified character is banished."""
    def source_filter(source, event_context):
        return source == character
    
    return ComposableTrigger(GameEvent.CHARACTER_BANISHED, source_filter)