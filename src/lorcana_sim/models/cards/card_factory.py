"""Factory for creating card objects from JSON data."""

from typing import Dict, List, Any, Optional

from .base_card import Card, CardColor, Rarity
from .character_card import CharacterCard
from .action_card import ActionCard
from .item_card import ItemCard
from .location_card import LocationCard


class CardFactory:
    """Factory for creating card objects from lorcana-json data."""
    
    @staticmethod
    def from_json(card_data: Dict[str, Any]) -> Card:
        """Create appropriate card type from lorcana-json data."""
        card_type = card_data.get("type")
        
        # Parse common fields first
        common_fields = CardFactory._parse_common_fields(card_data)
        
        if card_type == "Character":
            character_fields = CardFactory._parse_character_fields(card_data)
            character = CharacterCard(**common_fields, **character_fields)
            # Add composable abilities after character creation
            CardFactory._add_composable_abilities(character, card_data)
            return character
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
            # Some cards may have missing color data, provide a default
            color_str = "Amber"
        
        # Handle multi-color cards by taking the first color
        if "-" in color_str:
            primary_color_str = color_str.split("-")[0]
        else:
            primary_color_str = color_str
        
        try:
            color = CardColor(primary_color_str)
        except ValueError:
            raise ValueError(f"Unknown card color: {color_str}")
        
        # Extract full image URL if available
        image_url = None
        if "images" in card_data and isinstance(card_data["images"], dict):
            image_url = card_data["images"].get("full")
        
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
            "flavor_text": card_data.get("flavorText"),
            "full_text": card_data.get("fullText", ""),
            "artists": card_data.get("artists", []),
            "image_url": image_url
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
    def _add_composable_abilities(character: CharacterCard, card_data: Dict[str, Any]) -> None:
        """Add composable abilities to a character card from JSON data."""
        # Lazy imports to avoid circular dependency
        try:
            from ..abilities.composable.named_abilities import NamedAbilityRegistry
            from ..abilities.composable.keyword_abilities import create_keyword_ability
        except ImportError:
            # If abilities aren't available, skip ability processing
            return
        
        # Process abilities from the abilities array
        for ability_data in card_data.get("abilities", []):
            ability_type = ability_data.get("type")
            
            if ability_type == "keyword":
                # Handle keyword abilities
                keyword = ability_data.get("keyword")
                if keyword:
                    try:
                        keyword_ability = create_keyword_ability(keyword, character, ability_data)
                        if keyword_ability:
                            character.add_composable_ability(keyword_ability)
                    except Exception as e:
                        print(f"Warning: Failed to create keyword ability {keyword} for {character.name}: {e}")
            
            elif ability_data.get("name"):
                # Handle named abilities
                ability_name = ability_data.get("name")
                try:
                    named_ability = NamedAbilityRegistry.create_ability(ability_name, character, ability_data)
                    if named_ability:
                        character.add_composable_ability(named_ability)
                        print(f"Added named ability {ability_name} to {character.name}")
                    else:
                        print(f"Named ability {ability_name} not implemented yet for {character.name}")
                except Exception as e:
                    print(f"Warning: Failed to create named ability {ability_name} for {character.name}: {e}")
        
        # Also process keyword abilities from keywordAbilities array for compatibility
        for keyword in card_data.get("keywordAbilities", []):
            try:
                keyword_ability = create_keyword_ability(keyword, character)
                if keyword_ability:
                    character.add_composable_ability(keyword_ability)
            except Exception as e:
                print(f"Warning: Failed to create keyword ability {keyword} for {character.name}: {e}")
    
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
