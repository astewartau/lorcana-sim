"""Zone management component for GameState."""

from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState


class ZoneManagementComponent:
    """Handles zone-related operations for the game state."""
    
    def __init__(self):
        self._zone_manager: Optional[Any] = None  # ZoneManager instance (lazy loaded)
    
    @property
    def zone_manager(self):
        """Get or create the zone manager instance."""
        if self._zone_manager is None:
            from ...abilities.composable.zone_manager import ZoneManager
            self._zone_manager = ZoneManager()
        return self._zone_manager
    
    def register_card_conditional_effects(self, card) -> None:
        """Register all conditional effects from a card with the zone manager."""
        if hasattr(card, 'conditional_effects'):
            for effect in card.conditional_effects:
                self.zone_manager.register_conditional_effect(effect)
    
    def unregister_card_conditional_effects(self, card) -> None:
        """Unregister all conditional effects from a card."""
        if hasattr(card, 'conditional_effects'):
            for effect in card.conditional_effects:
                self.zone_manager.unregister_conditional_effect(effect)
    
    def notify_card_zone_change(self, card, from_zone_name: Optional[str], to_zone_name: Optional[str], game_state: "GameState") -> List[Dict]:
        """Notify zone manager of card movement and return any events generated."""
        if not hasattr(card, 'conditional_effects') or not card.conditional_effects:
            return []
        
        # Convert zone names to ActivationZone enums
        from ...abilities.composable.conditional_effects import ActivationZone
        
        zone_map = {
            'hand': ActivationZone.HAND,
            'play': ActivationZone.PLAY,
            'discard': ActivationZone.DISCARD,
            'deck': ActivationZone.DECK,
            'ink_well': ActivationZone.INK_WELL
        }
        
        from_zone = zone_map.get(from_zone_name) if from_zone_name else None
        to_zone = zone_map.get(to_zone_name) if to_zone_name else None
        
        return self.zone_manager.handle_zone_transition(card, from_zone, to_zone, game_state)
    
    def evaluate_conditional_effects(self, game_state: "GameState") -> List[Dict]:
        """Evaluate all conditional effects and return any events generated."""
        return self.zone_manager.evaluate_all_effects(game_state)