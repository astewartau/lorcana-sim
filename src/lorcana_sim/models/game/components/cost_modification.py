"""Cost modification component for GameState."""

from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState


class CostModificationComponent:
    """Handles cost modification operations for the game state."""
    
    def __init__(self):
        self._cost_modification_manager: Optional[Any] = None  # CostModificationManager instance (lazy loaded)
    
    @property
    def cost_modification_manager(self):
        """Get or create the cost modification manager instance."""
        if self._cost_modification_manager is None:
            from ...abilities.composable.cost_modification import CostModificationManager
            self._cost_modification_manager = CostModificationManager()
        return self._cost_modification_manager
    
    def get_modified_card_cost(self, card, game_state: "GameState") -> int:
        """Get the modified cost for a card after all applicable cost modifiers."""
        return self.cost_modification_manager.get_modified_cost(card, game_state)
    
    def register_cost_modifier(self, modifier) -> None:
        """Register a cost modifier with the game state."""
        self.cost_modification_manager.register_cost_modifier(modifier)
    
    def unregister_cost_modifier(self, modifier) -> None:
        """Unregister a cost modifier from the game state."""
        self.cost_modification_manager.unregister_cost_modifier(modifier)