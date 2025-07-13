"""State serialization system for step-by-step game progression."""

import json
import copy
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from ..models.game.game_state import GameState
from ..models.cards.base_card import Card
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.location_card import LocationCard


class SerializationError(Exception):
    """Raised when serialization fails."""
    pass


class StateSerializer(ABC):
    """Abstract base class for state serialization."""
    
    @abstractmethod
    def serialize(self, obj: Any) -> Dict[str, Any]:
        """Serialize an object to a dictionary."""
        pass
    
    @abstractmethod
    def deserialize(self, data: Dict[str, Any], obj_type: Type) -> Any:
        """Deserialize a dictionary to an object."""
        pass


class GameStateSerializer(StateSerializer):
    """Serializer for game state objects."""
    
    def __init__(self):
        self.card_serializers = {
            'Character': self._serialize_character_card,
            'Action': self._serialize_action_card,
            'Item': self._serialize_item_card,
            'Location': self._serialize_location_card
        }
        
        self.card_deserializers = {
            'Character': self._deserialize_character_card,
            'Action': self._deserialize_action_card,
            'Item': self._deserialize_item_card,
            'Location': self._deserialize_location_card
        }
    
    def serialize(self, obj: Any) -> Dict[str, Any]:
        """Serialize a game object to dictionary."""
        if isinstance(obj, GameState):
            return self._serialize_game_state(obj)
        elif isinstance(obj, Card):
            return self._serialize_card(obj)
        elif hasattr(obj, '__dict__'):
            return self._serialize_generic_object(obj)
        else:
            return {'value': obj, 'type': type(obj).__name__}
    
    def deserialize(self, data: Dict[str, Any], obj_type: Type) -> Any:
        """Deserialize dictionary to object."""
        if obj_type == GameState:
            return self._deserialize_game_state(data)
        elif issubclass(obj_type, Card):
            return self._deserialize_card(data)
        else:
            return self._deserialize_generic_object(data, obj_type)
    
    def _serialize_game_state(self, game_state: GameState) -> Dict[str, Any]:
        """Serialize a game state."""
        return {
            'type': 'GameState',
            'turn_number': game_state.turn_number,
            'current_player_index': game_state.current_player_index,
            'current_phase': game_state.current_phase.value,
            'winner': game_state.winner,
            'ink_played_this_turn': game_state.ink_played_this_turn,
            'first_turn_draw_skipped': game_state.first_turn_draw_skipped,
            'actions_this_turn': [action.value for action in game_state.actions_this_turn],
            'players': [self._serialize_player(player) for player in game_state.players]
        }
    
    def _serialize_player(self, player) -> Dict[str, Any]:
        """Serialize a player."""
        return {
            'type': 'Player',
            'name': player.name,
            'lore': player.lore,
            'available_ink': player.available_ink,
            'total_ink': player.total_ink,
            'hand': [self._serialize_card(card) for card in player.hand],
            'deck': [self._serialize_card(card) for card in player.deck.cards],
            'discard_pile': [self._serialize_card(card) for card in player.discard_pile],
            'inkwell': [self._serialize_card(card) for card in player.inkwell],
            'characters_in_play': [self._serialize_card(char) for char in player.characters_in_play],
            'items_in_play': [self._serialize_card(item) for item in player.items_in_play],
            'locations_in_play': [self._serialize_card(loc) for loc in player.locations_in_play]
        }
    
    def _serialize_card(self, card: Card) -> Dict[str, Any]:
        """Serialize a card based on its type."""
        card_type = card.card_type.value
        if card_type in self.card_serializers:
            return self.card_serializers[card_type](card)
        else:
            return self._serialize_base_card(card)
    
    def _serialize_base_card(self, card: Card) -> Dict[str, Any]:
        """Serialize base card properties."""
        return {
            'type': 'Card',
            'card_type': card.card_type.value,
            'name': card.name,
            'cost': card.cost,
            'ink_cost': card.ink_cost,
            'inkwell': card.inkwell,
            'color': card.color.value if card.color else None,
            'rarity': card.rarity.value if card.rarity else None,
            'set_name': card.set_name,
            'set_number': card.set_number,
            'abilities': [str(ability) for ability in card.abilities],
            'keywords': card.keywords,
            'flavor_text': card.flavor_text,
            'image_url': card.image_url
        }
    
    def _serialize_character_card(self, card: CharacterCard) -> Dict[str, Any]:
        """Serialize a character card."""
        base_data = self._serialize_base_card(card)
        base_data.update({
            'type': 'CharacterCard',
            'strength': card.strength,
            'willpower': card.willpower,
            'lore': card.lore,
            'current_damage': card.current_damage,
            'is_exerted': card.is_exerted,
            'turn_played': card.turn_played,
            'classifications': card.classifications,
            'version': card.version
        })
        return base_data
    
    def _serialize_action_card(self, card: ActionCard) -> Dict[str, Any]:
        """Serialize an action card."""
        base_data = self._serialize_base_card(card)
        base_data.update({
            'type': 'ActionCard',
            'is_song': card.is_song,
            'song_cost': card.song_cost
        })
        return base_data
    
    def _serialize_item_card(self, card: ItemCard) -> Dict[str, Any]:
        """Serialize an item card."""
        base_data = self._serialize_base_card(card)
        base_data.update({
            'type': 'ItemCard',
            'is_permanent': card.is_permanent,
            'is_attachment': card.is_attachment,
            'attached_to': card.attached_to.name if card.attached_to else None
        })
        return base_data
    
    def _serialize_location_card(self, card: LocationCard) -> Dict[str, Any]:
        """Serialize a location card."""
        base_data = self._serialize_base_card(card)
        base_data.update({
            'type': 'LocationCard',
            'willpower': card.willpower,
            'current_damage': card.current_damage,
            'move_cost': card.move_cost
        })
        return base_data
    
    def _serialize_generic_object(self, obj: Any) -> Dict[str, Any]:
        """Serialize a generic object with __dict__."""
        result = {'type': type(obj).__name__}
        for key, value in obj.__dict__.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                result[key] = value
            elif isinstance(value, (list, tuple)):
                result[key] = [self.serialize(item) for item in value]
            elif isinstance(value, dict):
                result[key] = {k: self.serialize(v) for k, v in value.items()}
            else:
                result[key] = self.serialize(value)
        return result
    
    def _deserialize_game_state(self, data: Dict[str, Any]) -> GameState:
        """Deserialize a game state (simplified implementation)."""
        # This would need full reconstruction logic
        # For now, return a placeholder noting this needs implementation
        raise NotImplementedError("GameState deserialization requires full reconstruction logic")
    
    def _deserialize_card(self, data: Dict[str, Any]) -> Card:
        """Deserialize a card based on its type."""
        card_type = data.get('card_type', data.get('type', 'Card'))
        if card_type in self.card_deserializers:
            return self.card_deserializers[card_type](data)
        else:
            raise SerializationError(f"Unknown card type: {card_type}")
    
    def _deserialize_character_card(self, data: Dict[str, Any]) -> CharacterCard:
        """Deserialize a character card (simplified)."""
        # This would need full reconstruction with all dependencies
        raise NotImplementedError("Card deserialization requires card factory integration")
    
    def _deserialize_action_card(self, data: Dict[str, Any]) -> ActionCard:
        """Deserialize an action card (simplified)."""
        raise NotImplementedError("Card deserialization requires card factory integration")
    
    def _deserialize_item_card(self, data: Dict[str, Any]) -> ItemCard:
        """Deserialize an item card (simplified)."""
        raise NotImplementedError("Card deserialization requires card factory integration")
    
    def _deserialize_location_card(self, data: Dict[str, Any]) -> LocationCard:
        """Deserialize a location card (simplified)."""
        raise NotImplementedError("Card deserialization requires card factory integration")
    
    def _deserialize_generic_object(self, data: Dict[str, Any], obj_type: Type) -> Any:
        """Deserialize a generic object."""
        raise NotImplementedError("Generic object deserialization needs type-specific logic")


@dataclass
class GameStateSnapshot:
    """Represents a snapshot of game state at a specific point."""
    snapshot_id: str
    step_id: str
    timestamp: float
    game_state_data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameStateSnapshot':
        """Create snapshot from dictionary."""
        return cls(**data)


class SnapshotManager:
    """Manages game state snapshots for step-by-step progression."""
    
    def __init__(self, serializer: StateSerializer = None):
        self.serializer = serializer or GameStateSerializer()
        self.snapshots: List[GameStateSnapshot] = []
        self.snapshot_index = 0
        
    def create_snapshot(self, step_id: str, game_state: GameState, 
                       metadata: Dict[str, Any] = None) -> GameStateSnapshot:
        """Create a snapshot of the current game state."""
        import time
        import uuid
        
        snapshot = GameStateSnapshot(
            snapshot_id=str(uuid.uuid4()),
            step_id=step_id,
            timestamp=time.time(),
            game_state_data=self.serializer.serialize(game_state),
            metadata=metadata or {}
        )
        
        self.snapshots.append(snapshot)
        self.snapshot_index = len(self.snapshots) - 1
        return snapshot
    
    def get_current_snapshot(self) -> Optional[GameStateSnapshot]:
        """Get the current snapshot."""
        if 0 <= self.snapshot_index < len(self.snapshots):
            return self.snapshots[self.snapshot_index]
        return None
    
    def get_snapshot_by_step_id(self, step_id: str) -> Optional[GameStateSnapshot]:
        """Get snapshot by step ID."""
        for snapshot in self.snapshots:
            if snapshot.step_id == step_id:
                return snapshot
        return None
    
    def restore_to_snapshot(self, snapshot_id: str) -> Optional[GameStateSnapshot]:
        """Restore to a specific snapshot."""
        for i, snapshot in enumerate(self.snapshots):
            if snapshot.snapshot_id == snapshot_id:
                self.snapshot_index = i
                return snapshot
        return None
    
    def get_all_snapshots(self) -> List[GameStateSnapshot]:
        """Get all snapshots."""
        return self.snapshots.copy()
    
    def clear_snapshots(self) -> None:
        """Clear all snapshots."""
        self.snapshots.clear()
        self.snapshot_index = 0
    
    def export_snapshots_to_json(self, file_path: str) -> None:
        """Export snapshots to JSON file."""
        data = [snapshot.to_dict() for snapshot in self.snapshots]
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_snapshots_from_json(self, file_path: str) -> None:
        """Import snapshots from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.snapshots = [GameStateSnapshot.from_dict(item) for item in data]
        self.snapshot_index = len(self.snapshots) - 1 if self.snapshots else 0