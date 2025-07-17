"""Collection loader for CSV format collections."""

import csv
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from .card_database import CardDatabase
from ..models.game.player import Player


@dataclass
class CollectionCard:
    """A card in a collection with quantities."""
    normal_count: int
    foil_count: int
    name: str
    set_code: str
    card_number: str
    color: str
    rarity: str
    price: str
    foil_price: str


class CollectionLoader:
    """Loads collections from CSV format and maps to card database."""
    
    def __init__(self, cards_json_path: str):
        self.card_db = CardDatabase(cards_json_path)
        self._unique_id_counter = 20000  # Start high to avoid conflicts
    
    def load_collection_from_csv(self, csv_path: str) -> List[object]:
        """Load collection from CSV and return list of card objects."""
        collection_cards = self._parse_csv(csv_path)
        card_objects = []
        found_cards = 0
        missing_cards = []
        
        print(f"📦 Loading collection from {Path(csv_path).name}:")
        print(f"   Unique cards in CSV: {len(collection_cards)}")
        
        for collection_card in collection_cards:
            card_data = self.card_db.find_card(collection_card.name)
            
            if card_data:
                # Create card objects for both normal and foil copies
                total_copies = collection_card.normal_count + collection_card.foil_count
                for _ in range(total_copies):
                    card_obj = self.card_db.create_card_object(card_data, self._get_unique_id())
                    card_objects.append(card_obj)
                    found_cards += 1
            else:
                missing_cards.append(f"{collection_card.name} (x{collection_card.normal_count + collection_card.foil_count})")
        
        if missing_cards:
            print(f"   ⚠️  Missing cards ({len(missing_cards)}): {', '.join(missing_cards[:5])}")
            if len(missing_cards) > 5:
                print(f"      ... and {len(missing_cards) - 5} more")
        
        total_cards = sum(card.normal_count + card.foil_count for card in collection_cards)
        print(f"   ✅ Successfully loaded: {found_cards}/{total_cards} cards")
        
        return card_objects
    
    def _parse_csv(self, csv_path: str) -> List[CollectionCard]:
        """Parse CSV file into CollectionCard objects."""
        cards = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                card = CollectionCard(
                    normal_count=int(row.get('Normal', 0)),
                    foil_count=int(row.get('Foil', 0)),
                    name=row.get('Name', '').strip('"'),
                    set_code=row.get('Set', ''),
                    card_number=row.get('Card Number', ''),
                    color=row.get('Color', ''),
                    rarity=row.get('Rarity', ''),
                    price=row.get('Price', ''),
                    foil_price=row.get('Foil Price', '')
                )
                cards.append(card)
        
        return cards
    
    def _get_unique_id(self) -> int:
        """Get a unique ID for card objects."""
        self._unique_id_counter += 1
        return self._unique_id_counter
    
    def get_collection_summary(self, csv_path: str) -> dict:
        """Get a summary of what's in the collection."""
        collection_cards = self._parse_csv(csv_path)
        
        summary = {
            'total_cards': 0,
            'unique_cards': len(collection_cards),
            'found_cards': 0,
            'missing_cards': [],
            'by_color': {},
            'by_rarity': {},
            'by_type': {}
        }
        
        for collection_card in collection_cards:
            total_count = collection_card.normal_count + collection_card.foil_count
            summary['total_cards'] += total_count
            
            card_data = self.card_db.find_card(collection_card.name)
            
            if card_data:
                summary['found_cards'] += total_count
                
                # Count by color
                color = card_data.color
                if color not in summary['by_color']:
                    summary['by_color'][color] = 0
                summary['by_color'][color] += total_count
                
                # Count by rarity
                rarity = card_data.rarity
                if rarity not in summary['by_rarity']:
                    summary['by_rarity'][rarity] = 0
                summary['by_rarity'][rarity] += total_count
                
                # Count by type
                card_type = card_data.type
                if card_type not in summary['by_type']:
                    summary['by_type'][card_type] = 0
                summary['by_type'][card_type] += total_count
            else:
                summary['missing_cards'].append(f"{collection_card.name} (x{total_count})")
        
        return summary