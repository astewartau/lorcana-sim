"""Zone management system for tracking card locations and conditional effects."""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, TYPE_CHECKING
from collections import defaultdict

from .conditional_effects import ConditionalEffect, ActivationZone

if TYPE_CHECKING:
    from ...cards.character_card import CharacterCard
    from ...game.game_state import GameState
    from ...game.player import Player


@dataclass
class ZoneManager:
    """Manages zone transitions and conditional effect activation/deactivation."""
    
    # Track effects by zone for efficient lookup
    effects_by_zone: Dict[ActivationZone, Set[ConditionalEffect]] = field(default_factory=lambda: defaultdict(set))
    
    # Track all registered effects
    all_effects: Set[ConditionalEffect] = field(default_factory=set)
    
    # Track zone transitions for debugging
    recent_transitions: List[Tuple[str, ActivationZone, ActivationZone]] = field(default_factory=list)
    max_transition_history: int = 50
    
    def register_conditional_effect(self, effect: ConditionalEffect) -> None:
        """Register a conditional effect with the zone manager."""
        self.all_effects.add(effect)
        
        # Add to zone-specific tracking
        for zone in effect.activation_zones:
            self.effects_by_zone[zone].add(effect)
    
    def unregister_conditional_effect(self, effect: ConditionalEffect) -> None:
        """Unregister a conditional effect from the zone manager."""
        self.all_effects.discard(effect)
        
        # Remove from zone-specific tracking
        for zone in effect.activation_zones:
            self.effects_by_zone[zone].discard(effect)
    
    def handle_zone_transition(self, 
                             card: 'CharacterCard', 
                             from_zone: Optional[ActivationZone], 
                             to_zone: Optional[ActivationZone],
                             game_state: 'GameState') -> List[Dict]:
        """Handle a card moving between zones and return any events generated."""
        events = []
        
        # Track the transition
        if from_zone and to_zone:
            self._record_transition(card.name, from_zone, to_zone)
        
        # Find all conditional effects on this card
        card_effects = getattr(card, 'conditional_effects', [])
        
        for effect in card_effects:
            # Check if effect should be activated or deactivated
            was_valid = from_zone in effect.activation_zones if from_zone else False
            is_valid = to_zone in effect.activation_zones if to_zone else False
            
            if not was_valid and is_valid:
                # Effect becomes valid - register it and potentially activate
                self.register_conditional_effect(effect)
                if effect.evaluate_condition(game_state):
                    event = effect.apply_effect(game_state)
                    if event:
                        events.append(event)
            
            elif was_valid and not is_valid:
                # Effect becomes invalid - deactivate if active and unregister
                if effect.is_active:
                    event = effect.remove_effect(game_state)
                    if event:
                        events.append(event)
                self.unregister_conditional_effect(effect)
            
            elif is_valid:
                # Effect was and still is valid - ensure it's registered and evaluate
                if effect not in self.all_effects:
                    self.register_conditional_effect(effect)
                if effect.should_evaluate(game_state):
                    should_be_active = effect.evaluate_condition(game_state)
                    if should_be_active and not effect.is_active:
                        event = effect.apply_effect(game_state)
                        if event:
                            events.append(event)
                    elif not should_be_active and effect.is_active:
                        event = effect.remove_effect(game_state)
                        if event:
                            events.append(event)
        
        return events
    
    def get_effects_in_zone(self, zone: ActivationZone) -> Set[ConditionalEffect]:
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
    
    def get_all_effects_for_card(self, card: 'CharacterCard') -> List[ConditionalEffect]:
        """Get all conditional effects registered for a specific card."""
        return [effect for effect in self.all_effects if effect.source_card == card]
    
    def evaluate_zone_effects(self, zone: ActivationZone, game_state: 'GameState') -> List[Dict]:
        """Evaluate all effects that could be active in a zone and return any events."""
        events = []
        zone_effects = self.get_effects_in_zone(zone)
        
        for effect in zone_effects:
            # Check if the effect's source card is actually in this zone
            if not effect.is_in_valid_zone(game_state):
                continue
            
            # Skip if we don't need to evaluate
            if not effect.should_evaluate(game_state):
                continue
            
            # Evaluate condition
            should_be_active = effect.evaluate_condition(game_state)
            
            if should_be_active and not effect.is_active:
                # Apply effect
                event = effect.apply_effect(game_state)
                if event:
                    events.append(event)
            elif not should_be_active and effect.is_active:
                # Remove effect
                event = effect.remove_effect(game_state)
                if event:
                    events.append(event)
        
        return events
    
    def evaluate_all_effects(self, game_state: 'GameState') -> List[Dict]:
        """Evaluate all registered conditional effects and return any events."""
        events = []
        
        for effect in self.all_effects:
            # Check if effect is in a valid zone
            if not effect.is_in_valid_zone(game_state):
                # If effect was active but source moved to invalid zone, deactivate
                if effect.is_active:
                    event = effect.remove_effect(game_state)
                    if event:
                        events.append(event)
                continue
            
            # Skip if we don't need to evaluate
            if not effect.should_evaluate(game_state):
                continue
            
            # Evaluate condition
            should_be_active = effect.evaluate_condition(game_state)
            
            if should_be_active and not effect.is_active:
                # Apply effect
                event = effect.apply_effect(game_state)
                if event:
                    events.append(event)
            elif not should_be_active and effect.is_active:
                # Remove effect
                event = effect.remove_effect(game_state)
                if event:
                    events.append(event)
        
        return events
    
    def force_evaluate_card_effects(self, card: 'CharacterCard', game_state: 'GameState') -> List[Dict]:
        """Force evaluation of all effects on a specific card."""
        events = []
        card_effects = getattr(card, 'conditional_effects', [])
        
        for effect in card_effects:
            # Force evaluation regardless of timing
            effect.last_evaluation_turn = -1
            
            # Check if effect is in valid zone
            if not effect.is_in_valid_zone(game_state):
                if effect.is_active:
                    event = effect.remove_effect(game_state)
                    if event:
                        events.append(event)
                continue
            
            # Evaluate condition
            should_be_active = effect.evaluate_condition(game_state)
            
            if should_be_active and not effect.is_active:
                event = effect.apply_effect(game_state)
                if event:
                    events.append(event)
            elif not should_be_active and effect.is_active:
                event = effect.remove_effect(game_state)
                if event:
                    events.append(event)
        
        return events
    
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
            'total_effects': len(self.all_effects),
            'effects_by_zone': {zone.value: len(effects) for zone, effects in self.effects_by_zone.items()},
            'active_effects': len([e for e in self.all_effects if e.is_active]),
            'recent_transitions': len(self.recent_transitions)
        }