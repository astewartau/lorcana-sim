"""Zone management system for tracking card locations and conditional effects."""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, TYPE_CHECKING, Any
from collections import defaultdict

from .activation_zones import ActivationZone

if TYPE_CHECKING:
    from ...cards.character_card import CharacterCard
    from ...game.game_state import GameState
    from ...game.player import Player


@dataclass
class ZoneManager:
    """Manages zone transitions and conditional effect activation/deactivation.
    
    NOTE: This class is part of the legacy conditional effect system and is being phased out
    in favor of the new StatefulConditionalEffect pattern. Many methods are disabled to avoid
    import errors from the removed ConditionalEffect class.
    """
    
    # Track effects by zone for efficient lookup
    effects_by_zone: Dict[ActivationZone, Set[Any]] = field(default_factory=lambda: defaultdict(set))
    
    # Track all registered effects
    all_effects: Set[Any] = field(default_factory=set)
    
    # Track zone transitions for debugging
    recent_transitions: List[Tuple[str, ActivationZone, ActivationZone]] = field(default_factory=list)
    max_transition_history: int = 50
    
    def register_conditional_effect(self, effect: Any) -> None:
        """Register a conditional effect with the zone manager."""
        # NOTE: Disabled for legacy migration - StatefulConditionalEffect pattern doesn't use ZoneManager
        pass
    
    def unregister_conditional_effect(self, effect: Any) -> None:
        """Unregister a conditional effect from the zone manager."""
        # NOTE: Disabled for legacy migration - StatefulConditionalEffect pattern doesn't use ZoneManager
        pass
    
    def handle_zone_transition(self, 
                             card: 'CharacterCard', 
                             from_zone: Optional[ActivationZone], 
                             to_zone: Optional[ActivationZone],
                             game_state: 'GameState') -> List[Dict]:
        """Handle a card moving between zones and return any events generated."""
        # NOTE: Disabled for legacy migration - StatefulConditionalEffect pattern doesn't use ZoneManager
        return []
    
    def get_effects_in_zone(self, zone: ActivationZone) -> Set[Any]:
        """Get all conditional effects that can be active in the specified zone."""
        return self.effects_by_zone.get(zone, set()).copy()
    
    def get_card_zone(self, card: 'CharacterCard', game_state: 'GameState') -> Optional[ActivationZone]:
        """Determine which zone a card is currently in."""
        for player in game_state.players:
            if card in player.characters_in_play:
                return ActivationZone.PLAY
            elif card in player.hand:
                return ActivationZone.HAND
            elif card in player.discard_pile:
                return ActivationZone.DISCARD
            elif card in player.deck:
                return ActivationZone.DECK
            elif card in player.inkwell:
                return ActivationZone.INK_WELL
        
        return None
    
    def get_all_effects_for_card(self, card: 'CharacterCard') -> List[Any]:
        """Get all conditional effects registered for a specific card."""
        # NOTE: Disabled for legacy migration - StatefulConditionalEffect pattern doesn't use ZoneManager
        return []
    
    def evaluate_zone_effects(self, zone: ActivationZone, game_state: 'GameState') -> List[Dict]:
        """Evaluate all effects that could be active in a zone and return any events."""
        # NOTE: Disabled for legacy migration - StatefulConditionalEffect pattern doesn't use ZoneManager
        return []
    
    def evaluate_all_effects(self, game_state: 'GameState') -> List[Dict]:
        """Evaluate all registered conditional effects and return any events."""
        # NOTE: Disabled for legacy migration - StatefulConditionalEffect pattern doesn't use ZoneManager
        return []
    
    def force_evaluate_card_effects(self, card: 'CharacterCard', game_state: 'GameState') -> List[Dict]:
        """Force evaluation of all effects on a specific card."""
        # NOTE: Disabled for legacy migration - StatefulConditionalEffect pattern doesn't use ZoneManager
        return []
    
    def _record_transition(self, card_name: str, from_zone: ActivationZone, to_zone: ActivationZone) -> None:
        """Record a zone transition for debugging."""
        self.recent_transitions.append((card_name, from_zone, to_zone))
        
        # Limit history size
        if len(self.recent_transitions) > self.max_transition_history:
            self.recent_transitions.pop(0)
    
    def get_transition_history(self) -> List[Tuple[str, ActivationZone, ActivationZone]]:
        """Get recent zone transitions for debugging."""
        return self.recent_transitions.copy()
    
    def get_debug_info(self) -> Dict:
        """Get debugging information about the zone manager state."""
        return {
            'total_effects': 0,
            'effects_by_zone': {},
            'active_effects': 0,
            'recent_transitions': len(self.recent_transitions)
        }