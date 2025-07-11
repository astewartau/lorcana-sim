"""
Dreamborn format deck parser.

This module handles parsing deck lists in the Dreamborn format used by 
tools like Dreamborn.ink and Tabletop Simulator.
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DeckCard:
    """Represents a card in a deck with its quantity"""
    card_id: int
    nickname: str
    quantity: int


@dataclass
class DeckInfo:
    """Information about a deck"""
    total_cards: int
    unique_cards: int
    cards: List[DeckCard]
    card_ids: List[int]  # All card IDs including duplicates


class DreambornParser:
    """Parser for Dreamborn format deck lists"""
    
    def __init__(self, json_file_path: str):
        """Initialize parser with path to dreamborn format file"""
        self.json_file_path = Path(json_file_path)
        self.data: Dict = {}
        self.deck_info: Optional[DeckInfo] = None
        
        self._load_data()
    
    def _load_data(self) -> None:
        """Load and parse the JSON data"""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self._parse_deck()
    
    def _parse_deck(self) -> None:
        """Parse the deck from the Dreamborn format"""
        object_states = self.data.get('ObjectStates', [])
        
        if not object_states:
            raise ValueError("No ObjectStates found in Dreamborn format")
        
        # Find the deck object
        deck_object = None
        for obj in object_states:
            if obj.get('Name') == 'DeckCustom':
                deck_object = obj
                break
        
        if not deck_object:
            raise ValueError("No DeckCustom object found in Dreamborn format")
        
        # Extract card information
        contained_objects = deck_object.get('ContainedObjects', [])
        deck_ids = deck_object.get('DeckIDs', [])
        
        # Count card occurrences
        card_counts = {}
        card_nicknames = {}
        
        for i, card_obj in enumerate(contained_objects):
            card_id = card_obj.get('CardID')
            nickname = card_obj.get('Nickname', f'Card {card_id}')
            
            if card_id not in card_counts:
                card_counts[card_id] = 0
                card_nicknames[card_id] = nickname
            
            card_counts[card_id] += 1
        
        # Create deck cards list
        deck_cards = []
        for card_id, count in card_counts.items():
            deck_cards.append(DeckCard(
                card_id=card_id,
                nickname=card_nicknames[card_id],
                quantity=count
            ))
        
        # Sort by card ID for consistency
        deck_cards.sort(key=lambda x: x.card_id)
        
        self.deck_info = DeckInfo(
            total_cards=len(contained_objects),
            unique_cards=len(deck_cards),
            cards=deck_cards,
            card_ids=deck_ids
        )
    
    def get_deck_info(self) -> DeckInfo:
        """Get the parsed deck information"""
        if self.deck_info is None:
            raise ValueError("Deck not parsed yet")
        return self.deck_info
    
    def get_card_list(self) -> List[DeckCard]:
        """Get the list of cards in the deck"""
        return self.deck_info.cards if self.deck_info else []
    
    def get_card_ids(self) -> List[int]:
        """Get all card IDs in the deck (including duplicates)"""
        return self.deck_info.card_ids if self.deck_info else []
    
    def get_unique_card_ids(self) -> List[int]:
        """Get unique card IDs in the deck"""
        return [card.card_id for card in self.get_card_list()]
    
    def get_deck_summary(self) -> Dict:
        """Get a summary of the deck composition"""
        if not self.deck_info:
            return {}
        
        return {
            'total_cards': self.deck_info.total_cards,
            'unique_cards': self.deck_info.unique_cards,
            'cards_by_quantity': {
                card.nickname: card.quantity 
                for card in self.deck_info.cards
            }
        }
    
    def validate_deck_format(self) -> List[str]:
        """Validate the deck format and return any issues"""
        issues = []
        
        if not self.deck_info:
            issues.append("Deck not parsed")
            return issues
        
        # Check total cards (should be 60 for Lorcana)
        if self.deck_info.total_cards != 60:
            issues.append(f"Deck has {self.deck_info.total_cards} cards (expected 60)")
        
        # Check individual card limits (max 4 of each card)
        for card in self.deck_info.cards:
            if card.quantity > 4:
                issues.append(f"Card '{card.nickname}' has {card.quantity} copies (max 4)")
        
        return issues
    
    def export_simple_format(self) -> Dict[str, int]:
        """Export deck in simple format: {card_id: quantity}"""
        if not self.deck_info:
            return {}
        
        return {str(card.card_id): card.quantity for card in self.deck_info.cards}
    
    def export_card_names(self) -> Dict[str, int]:
        """Export deck with card names: {card_name: quantity}"""
        if not self.deck_info:
            return {}
        
        return {card.nickname: card.quantity for card in self.deck_info.cards}