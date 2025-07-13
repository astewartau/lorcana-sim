"""Factory for creating card objects from JSON data."""

from typing import Dict, List, Any, Optional

from .base_card import Card, CardColor, Rarity
from .character_card import CharacterCard
from .action_card import ActionCard
from .item_card import ItemCard
from .location_card import LocationCard
# Composable abilities are now handled separately from card creation


class CardFactory:
    """Factory for creating card objects from lorcana-json data."""
    
    @staticmethod
    def from_json(card_data: Dict[str, Any]) -> Card:
        """Create appropriate card type from lorcana-json data."""
        card_type = card_data.get("type")
        
        # Parse common fields first
        common_fields = CardFactory._parse_common_fields(card_data)
        
        if card_type == "Character":
            return CharacterCard(**common_fields, **CardFactory._parse_character_fields(card_data))
        elif card_type == "Action":
            return ActionCard(**common_fields, **CardFactory._parse_action_fields(card_data))
        elif card_type == "Item":
            return ItemCard(**common_fields, **CardFactory._parse_item_fields(card_data))
        elif card_type == "Location":
            return LocationCard(**common_fields, **CardFactory._parse_location_fields(card_data))
        else:
            raise ValueError(f"Unknown card type: {card_type}")
    
    @staticmethod
    def _parse_common_fields(card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse fields common to all card types."""
        # Handle color - could be single color or multi-color like "Amber-Steel"
        color_str = card_data.get("color", "")
        if not color_str:
            raise ValueError(f"Card has empty color field: {card_data.get('fullName', 'Unknown')}")
        
        try:
            color = CardColor(color_str)
        except ValueError:
            # Handle multi-color cards by taking the first color for now
            if "-" in color_str:
                first_color = color_str.split("-")[0]
                color = CardColor(first_color)
            else:
                raise ValueError(f"Unknown card color: {color_str}")
        
        return {
            "id": card_data["id"],
            "name": card_data["name"],
            "version": card_data.get("version"),
            "full_name": card_data["fullName"],
            "cost": card_data["cost"],
            "color": color,
            "inkwell": card_data["inkwell"],
            "rarity": Rarity(card_data["rarity"]),
            "set_code": card_data["setCode"],
            "number": card_data["number"],
            "story": card_data["story"],
            "abilities": CardFactory._parse_abilities(card_data),
            "flavor_text": card_data.get("flavorText"),
            "full_text": card_data.get("fullText", ""),
            "artists": card_data.get("artists", [])
        }
    
    @staticmethod
    def _parse_character_fields(card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse fields specific to character cards."""
        return {
            "strength": card_data.get("strength", 0),
            "willpower": card_data.get("willpower", 0),
            "lore": card_data.get("lore", 0),
            "subtypes": card_data.get("subtypes", [])
        }
    
    @staticmethod
    def _parse_action_fields(card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse fields specific to action cards."""
        # Extract effects from abilities
        effects = []
        for ability in card_data.get("abilities", []):
            if ability.get("effect"):
                effects.append(ability["effect"])
        
        return {
            "effects": effects
        }
    
    @staticmethod
    def _parse_item_fields(card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse fields specific to item cards."""
        # Items don't have special fields beyond the base card
        return {}
    
    @staticmethod
    def _parse_location_fields(card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse fields specific to location cards."""
        return {
            "move_cost": card_data.get("moveCost", 0),
            "willpower": card_data.get("willpower", 0),
            "lore": card_data.get("lore")  # Can be None
        }
    
    @staticmethod
    def _parse_abilities(card_data: Dict[str, Any]) -> List:
        """Parse abilities from card data.
        
        Returns empty list for now - composable abilities are added separately.
        """
        # Composable abilities are now added via keyword parsing
        # and ability text parsing in a separate system
        return []
    
    @staticmethod
    def create_cards_from_database(database: List[Dict[str, Any]]) -> List[Card]:
        """Create a list of cards from database JSON data.
        
        Args:
            database: List of card data dictionaries from allCards.json
            
        Returns:
            List of successfully created Card objects (skips invalid cards)
        """
        cards = []
        for card_data in database:
            try:
                card = CardFactory.from_json(card_data)
                cards.append(card)
            except (KeyError, ValueError) as e:
                # Skip invalid cards but don't crash
                print(f"Warning: Failed to create card from data {card_data.get('name', 'Unknown')}: {e}")
                continue
        return cards
    
    @staticmethod
    def find_card_by_dreamborn_name(database: List[Dict[str, Any]], dreamborn_name: str) -> Optional[Dict[str, Any]]:
        """Find a card in the database by its Dreamborn nickname (fullName).
        
        Args:
            database: List of card data dictionaries from allCards.json
            dreamborn_name: The card name from Dreamborn format (e.g., "HeiHei - Protective Rooster")
            
        Returns:
            Card data dictionary if found, None otherwise
        """
        for card_data in database:
            if card_data.get('fullName') == dreamborn_name:
                return card_data
        return None
