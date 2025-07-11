"""Factory for creating card objects from JSON data."""

from typing import Dict, List, Any, Optional

from .base_card import Card, CardColor, Rarity
from .character_card import CharacterCard
from .action_card import ActionCard
from .item_card import ItemCard
from .location_card import LocationCard
from ..abilities.base_ability import (
    Ability,
    AbilityType,
    KeywordAbility,
    StaticAbility,
    TriggeredAbility,
    ActivatedAbility,
)


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
    def _parse_abilities(card_data: Dict[str, Any]) -> List[Ability]:
        """Parse abilities from both abilities and keywordAbilities arrays."""
        abilities = []
        
        # Parse structured abilities array
        abilities_data = card_data.get("abilities", [])
        for ability_data in abilities_data:
            ability_type_str = ability_data.get("type", "")
            name = ability_data.get("name", "")
            effect = ability_data.get("effect", "")
            full_text = ability_data.get("fullText", effect)
            
            if ability_type_str == "keyword":
                keyword = ability_data.get("keyword", "")
                # Extract value from keywordValueNumber (not value)
                value = ability_data.get("keywordValueNumber")
                abilities.append(KeywordAbility(
                    name=name or keyword,  # Use keyword as name if name is empty
                    type=AbilityType.KEYWORD,
                    effect=effect,
                    full_text=full_text,
                    keyword=keyword,
                    value=value
                ))
            elif ability_type_str == "triggered":
                abilities.append(TriggeredAbility(
                    name=name,
                    type=AbilityType.TRIGGERED,
                    effect=effect,
                    full_text=full_text,
                    trigger_condition=effect  # Store as string for now
                ))
            elif ability_type_str == "static":
                abilities.append(StaticAbility(
                    name=name,
                    type=AbilityType.STATIC,
                    effect=effect,
                    full_text=full_text
                ))
            elif ability_type_str == "activated":
                abilities.append(ActivatedAbility(
                    name=name,
                    type=AbilityType.ACTIVATED,
                    effect=effect,
                    full_text=full_text,
                    costs=[]  # TODO: Parse costs from text
                ))
            else:
                # Create a generic ability for unknown types
                abilities.append(Ability(
                    name=name,
                    type=AbilityType.STATIC,  # Default fallback
                    effect=effect,
                    full_text=full_text
                ))
        
        # Parse keywordAbilities array and merge with existing
        keyword_abilities_from_array = set(card_data.get("keywordAbilities", []))
        keywords_already_parsed = set()
        
        # Track which keywords already have structured data
        for ability in abilities:
            if hasattr(ability, 'keyword') and ability.keyword:
                keywords_already_parsed.add(ability.keyword)
        
        # Add missing keywords from keywordAbilities array
        missing_keywords = keyword_abilities_from_array - keywords_already_parsed
        for keyword_name in missing_keywords:
            abilities.append(KeywordAbility(
                name=keyword_name,
                type=AbilityType.KEYWORD,
                effect=f'{keyword_name} keyword ability',
                full_text='',
                keyword=keyword_name,
                value=None
            ))
        
        return abilities
    
    @staticmethod
    def find_card_by_dreamborn_name(card_database: List[Dict[str, Any]], dreamborn_name: str) -> Optional[Dict[str, Any]]:
        """Find card in database by Dreamborn deck name (not by numeric ID)."""
        # Dreamborn uses card names, not the numeric "id" field
        for card in card_database:
            if card.get("fullName") == dreamborn_name:
                return card
        return None
    
    @staticmethod
    def create_cards_from_database(card_database) -> List[Card]:
        """Create all cards from a lorcana-json database."""
        # Handle both file path string and list of card data
        if isinstance(card_database, str):
            from ...loaders.lorcana_json_parser import LorcanaJsonParser
            parser = LorcanaJsonParser(card_database)
            card_database = parser.cards
        cards = []
        errors = []
        skipped_empty_color = 0
        
        for card_data in card_database:
            try:
                # Skip cards with empty color (likely promotional/special variants)
                if not card_data.get("color", ""):
                    skipped_empty_color += 1
                    continue
                    
                card = CardFactory.from_json(card_data)
                cards.append(card)
            except Exception as e:
                errors.append(f"Error creating card {card_data.get('fullName', 'Unknown')}: {e}")
        
        if skipped_empty_color > 0:
            print(f"Skipped {skipped_empty_color} cards with empty color fields (likely promotional variants)")
        
        if errors:
            print(f"Encountered {len(errors)} errors while creating cards:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
        
        return cards