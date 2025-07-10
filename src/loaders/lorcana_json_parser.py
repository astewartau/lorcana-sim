"""
Lorcana JSON Parser with enumeration capabilities.

This module provides comprehensive parsing and analysis of lorcana-json format data,
including enumeration of all card components for validation and testing purposes.
"""

import json
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CardStatistics:
    """Statistics about the card database"""
    total_cards: int
    cards_by_type: Dict[str, int]
    cards_by_color: Dict[str, int]
    cards_by_rarity: Dict[str, int]
    cards_by_set: Dict[str, int]
    cards_by_story: Dict[str, int]
    inkable_cards: int
    non_inkable_cards: int


@dataclass
class AbilityStatistics:
    """Statistics about abilities in the database"""
    total_abilities: int
    abilities_by_type: Dict[str, int]
    keyword_abilities: Dict[str, int]
    unique_ability_names: Set[str]
    unique_keywords: Set[str]


@dataclass
class CharacterStatistics:
    """Statistics specific to character cards"""
    total_characters: int
    strength_distribution: Dict[int, int]
    willpower_distribution: Dict[int, int]
    lore_distribution: Dict[int, int]
    cost_distribution: Dict[int, int]
    all_subtypes: Set[str]
    subtypes_frequency: Dict[str, int]


class LorcanaJsonParser:
    """Parser for lorcana-json format with comprehensive enumeration capabilities"""
    
    def __init__(self, json_file_path: str):
        """Initialize parser with path to lorcana-json file"""
        self.json_file_path = Path(json_file_path)
        self.data: Dict[str, Any] = {}
        self.cards: List[Dict[str, Any]] = []
        self.sets: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        
        self._load_data()
    
    def _load_data(self) -> None:
        """Load and parse the JSON data"""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.cards = self.data.get('cards', [])
        self.sets = self.data.get('sets', {})
        self.metadata = self.data.get('metadata', {})
    
    def get_card_statistics(self) -> CardStatistics:
        """Get comprehensive statistics about cards"""
        type_count = Counter()
        color_count = Counter()
        rarity_count = Counter()
        set_count = Counter()
        story_count = Counter()
        inkable_count = 0
        
        for card in self.cards:
            # Card type
            card_type = card.get('type', 'Unknown')
            type_count[card_type] += 1
            
            # Color
            color = card.get('color', 'Unknown')
            color_count[color] += 1
            
            # Rarity
            rarity = card.get('rarity', 'Unknown')
            rarity_count[rarity] += 1
            
            # Set
            set_code = card.get('setCode', 'Unknown')
            set_count[set_code] += 1
            
            # Story
            story = card.get('story', 'Unknown')
            story_count[story] += 1
            
            # Inkwell
            if card.get('inkwell', False):
                inkable_count += 1
        
        return CardStatistics(
            total_cards=len(self.cards),
            cards_by_type=dict(type_count),
            cards_by_color=dict(color_count),
            cards_by_rarity=dict(rarity_count),
            cards_by_set=dict(set_count),
            cards_by_story=dict(story_count),
            inkable_cards=inkable_count,
            non_inkable_cards=len(self.cards) - inkable_count
        )
    
    def get_ability_statistics(self) -> AbilityStatistics:
        """Get comprehensive statistics about abilities"""
        ability_type_count = Counter()
        keyword_count = Counter()
        ability_names = set()
        keywords = set()
        total_abilities = 0
        
        for card in self.cards:
            abilities = card.get('abilities', [])
            total_abilities += len(abilities)
            
            for ability in abilities:
                # Ability type
                ability_type = ability.get('type', 'Unknown')
                ability_type_count[ability_type] += 1
                
                # Ability name
                ability_name = ability.get('name', '')
                if ability_name:
                    ability_names.add(ability_name)
                
                # Keywords
                if ability_type == 'keyword':
                    keyword = ability.get('keyword', '')
                    if keyword:
                        keywords.add(keyword)
                        keyword_count[keyword] += 1
        
        return AbilityStatistics(
            total_abilities=total_abilities,
            abilities_by_type=dict(ability_type_count),
            keyword_abilities=dict(keyword_count),
            unique_ability_names=ability_names,
            unique_keywords=keywords
        )
    
    def get_character_statistics(self) -> CharacterStatistics:
        """Get statistics specific to character cards"""
        character_cards = [card for card in self.cards if card.get('type') == 'Character']
        
        strength_dist = Counter()
        willpower_dist = Counter()
        lore_dist = Counter()
        cost_dist = Counter()
        all_subtypes = set()
        subtype_freq = Counter()
        
        for card in character_cards:
            # Combat stats
            strength = card.get('strength', 0)
            strength_dist[strength] += 1
            
            willpower = card.get('willpower', 0)
            willpower_dist[willpower] += 1
            
            lore = card.get('lore', 0)
            lore_dist[lore] += 1
            
            cost = card.get('cost', 0)
            cost_dist[cost] += 1
            
            # Subtypes
            subtypes = card.get('subtypes', [])
            for subtype in subtypes:
                all_subtypes.add(subtype)
                subtype_freq[subtype] += 1
        
        return CharacterStatistics(
            total_characters=len(character_cards),
            strength_distribution=dict(strength_dist),
            willpower_distribution=dict(willpower_dist),
            lore_distribution=dict(lore_dist),
            cost_distribution=dict(cost_dist),
            all_subtypes=all_subtypes,
            subtypes_frequency=dict(subtype_freq)
        )
    
    def enumerate_all_fields(self) -> Dict[str, Set[str]]:
        """Enumerate all possible field values across all cards"""
        field_values = defaultdict(set)
        
        for card in self.cards:
            self._extract_field_values(card, field_values, prefix="")
        
        # Convert sets to sorted lists for better display
        return {field: sorted(values) if all(isinstance(v, str) for v in values) else values 
                for field, values in field_values.items()}
    
    def _extract_field_values(self, obj: Any, field_values: Dict[str, Set[str]], prefix: str) -> None:
        """Recursively extract all field values from nested objects"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, (str, int, float, bool)):
                    field_values[current_key].add(str(value))
                elif isinstance(value, list):
                    if value and isinstance(value[0], (str, int, float)):
                        for item in value:
                            field_values[current_key].add(str(item))
                    elif value and isinstance(value[0], dict):
                        for item in value:
                            self._extract_field_values(item, field_values, current_key)
                elif isinstance(value, dict):
                    self._extract_field_values(value, field_values, current_key)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_field_values(item, field_values, prefix)
    
    def get_unique_ability_types(self) -> List[str]:
        """Get all unique ability types"""
        ability_types = set()
        for card in self.cards:
            for ability in card.get('abilities', []):
                ability_types.add(ability.get('type', 'Unknown'))
        return sorted(ability_types)
    
    def get_unique_keywords(self) -> List[str]:
        """Get all unique keyword abilities"""
        keywords = set()
        for card in self.cards:
            for ability in card.get('abilities', []):
                if ability.get('type') == 'keyword':
                    keyword = ability.get('keyword', '')
                    if keyword:
                        keywords.add(keyword)
        return sorted(keywords)
    
    def get_unique_card_types(self) -> List[str]:
        """Get all unique card types"""
        return sorted(set(card.get('type', 'Unknown') for card in self.cards))
    
    def get_unique_colors(self) -> List[str]:
        """Get all unique card colors"""
        return sorted(set(card.get('color', 'Unknown') for card in self.cards))
    
    def get_unique_rarities(self) -> List[str]:
        """Get all unique rarities"""
        return sorted(set(card.get('rarity', 'Unknown') for card in self.cards))
    
    def get_unique_subtypes(self) -> List[str]:
        """Get all unique character subtypes"""
        subtypes = set()
        for card in self.cards:
            if card.get('type') == 'Character':
                for subtype in card.get('subtypes', []):
                    subtypes.add(subtype)
        return sorted(subtypes)
    
    def get_unique_stories(self) -> List[str]:
        """Get all unique Disney stories represented"""
        return sorted(set(card.get('story', 'Unknown') for card in self.cards))
    
    def find_cards_by_type(self, card_type: str) -> List[Dict[str, Any]]:
        """Find all cards of a specific type"""
        return [card for card in self.cards if card.get('type') == card_type]
    
    def find_cards_by_ability_type(self, ability_type: str) -> List[Dict[str, Any]]:
        """Find all cards with abilities of a specific type"""
        matching_cards = []
        for card in self.cards:
            for ability in card.get('abilities', []):
                if ability.get('type') == ability_type:
                    matching_cards.append(card)
                    break
        return matching_cards
    
    def find_cards_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Find all cards with a specific keyword ability"""
        matching_cards = []
        for card in self.cards:
            for ability in card.get('abilities', []):
                if (ability.get('type') == 'keyword' and 
                    ability.get('keyword') == keyword):
                    matching_cards.append(card)
                    break
        return matching_cards
    
    def get_card_by_id(self, card_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific card by ID"""
        for card in self.cards:
            if card.get('id') == card_id:
                return card
        return None
    
    def get_cards_by_ids(self, card_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple cards by their IDs"""
        result = []
        for card_id in card_ids:
            card = self.get_card_by_id(card_id)
            if card:
                result.append(card)
        return result
    
    def get_ability_examples(self, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Get example cards for each ability type"""
        examples = defaultdict(list)
        
        for card in self.cards:
            for ability in card.get('abilities', []):
                ability_type = ability.get('type', 'Unknown')
                if len(examples[ability_type]) < limit:
                    examples[ability_type].append({
                        'card_name': card.get('fullName', 'Unknown'),
                        'card_id': card.get('id'),
                        'ability': ability
                    })
        
        return dict(examples)
    
    def validate_data_completeness(self) -> Dict[str, Any]:
        """Validate that all expected fields are present and check for anomalies"""
        issues = {
            'missing_required_fields': [],
            'cards_with_no_abilities': [],
            'cards_with_unusual_stats': [],
            'unknown_ability_types': set(),
            'unknown_card_types': set()
        }
        
        expected_card_fields = {'id', 'name', 'type', 'cost', 'color', 'rarity', 'setCode'}
        
        for card in self.cards:
            card_id = card.get('id', 'Unknown')
            
            # Check required fields
            missing_fields = expected_card_fields - set(card.keys())
            if missing_fields:
                issues['missing_required_fields'].append({
                    'card_id': card_id,
                    'missing_fields': list(missing_fields)
                })
            
            # Check for cards with no abilities
            if not card.get('abilities'):
                issues['cards_with_no_abilities'].append(card_id)
            
            # Check for unusual stats
            if card.get('type') == 'Character':
                strength = card.get('strength', 0)
                willpower = card.get('willpower', 0)
                if strength > 10 or willpower > 15:
                    issues['cards_with_unusual_stats'].append({
                        'card_id': card_id,
                        'strength': strength,
                        'willpower': willpower
                    })
            
            # Check for unknown ability types
            for ability in card.get('abilities', []):
                ability_type = ability.get('type')
                if ability_type not in {'keyword', 'triggered', 'static', 'activated'}:
                    issues['unknown_ability_types'].add(ability_type)
            
            # Check for unknown card types
            card_type = card.get('type')
            if card_type not in {'Character', 'Action', 'Item', 'Location'}:
                issues['unknown_card_types'].add(card_type)
        
        return issues