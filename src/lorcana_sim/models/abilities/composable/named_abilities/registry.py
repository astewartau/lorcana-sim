"""Registry system for named abilities."""

from typing import Dict, Callable, Any, Optional
from ..composable_ability import ComposableAbility

# Global registry of named ability creators
_NAMED_ABILITY_REGISTRY: Dict[str, Callable[[Any, dict], ComposableAbility]] = {}

def register_named_ability(ability_name: str):
    """Decorator to register a named ability creator function."""
    def decorator(creator_func: Callable[[Any, dict], ComposableAbility]):
        _NAMED_ABILITY_REGISTRY[ability_name] = creator_func
        return creator_func
    return decorator

class NamedAbilityRegistry:
    """Registry for creating named abilities from card data."""
    
    @staticmethod
    def create_ability(ability_name: str, character: Any, ability_data: dict) -> Optional[ComposableAbility]:
        """Create a named ability if an implementation exists.
        
        Args:
            ability_name: The name of the ability (e.g., "KEEPING WATCH")
            character: The character that has this ability
            ability_data: The ability data from the card JSON
            
        Returns:
            ComposableAbility instance if implementation exists, None otherwise
        """
        creator_func = _NAMED_ABILITY_REGISTRY.get(ability_name)
        if creator_func:
            return creator_func(character, ability_data)
        return None
    
    @staticmethod
    def get_registered_abilities() -> Dict[str, Callable]:
        """Get all registered named abilities."""
        return _NAMED_ABILITY_REGISTRY.copy()
    
    @staticmethod
    def is_ability_implemented(ability_name: str) -> bool:
        """Check if a named ability is implemented."""
        return ability_name in _NAMED_ABILITY_REGISTRY