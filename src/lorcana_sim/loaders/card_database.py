"""Card database for loading and matching cards from the all-cards JSON."""

import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import CardColor, Rarity


@dataclass
class CardData:
    """Raw card data from the database."""
    id: int
    name: str
    version: str
    full_name: str
    cost: int
    color: str
    rarity: str
    type: str
    inkwell: bool
    set_code: str
    number: int
    story: str
    abilities: List[dict]
    # Character-specific
    strength: Optional[int] = None
    willpower: Optional[int] = None
    lore: Optional[int] = None
    subtypes: Optional[List[str]] = None


class CardDatabase:
    """Database for loading and matching cards."""
    
    def __init__(self, cards_json_path: str):
        self.cards_json_path = Path(cards_json_path)
        self.cards_by_name: Dict[str, CardData] = {}
        self.cards_by_full_name: Dict[str, CardData] = {}
        self._load_cards()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison by removing special characters and converting to lowercase."""
        # Remove special characters (keep only letters, numbers, spaces, and hyphens)
        normalized = re.sub(r"[^\w\s\-]", "", name)
        # Convert to lowercase and strip extra whitespace
        return normalized.lower().strip()
    
    def _load_cards(self):
        """Load all cards from the JSON file."""
        with open(self.cards_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for card_data in data.get('cards', []):
            card = self._parse_card_data(card_data)
            
            # Index by normalized name formats for matching
            self.cards_by_name[self._normalize_name(card.name)] = card
            self.cards_by_full_name[self._normalize_name(card.full_name)] = card
            
            # Also index by nickname format (Name - Version)
            nickname = f"{card.name} - {card.version}"
            self.cards_by_full_name[self._normalize_name(nickname)] = card
    
    def _parse_card_data(self, data: dict) -> CardData:
        """Parse raw JSON data into CardData."""
        return CardData(
            id=data.get('id', 0),
            name=data.get('name', ''),
            version=data.get('version', ''),
            full_name=data.get('fullName', ''),
            cost=data.get('cost', 0),
            color=data.get('color', 'Amber'),
            rarity=data.get('rarity', 'Common'),
            type=data.get('type', 'Character'),
            inkwell=data.get('inkwell', True),
            set_code=data.get('setCode', '1'),
            number=data.get('number', 1),
            story=data.get('story', ''),
            abilities=data.get('abilities', []),
            strength=data.get('strength'),
            willpower=data.get('willpower'),
            lore=data.get('lore'),
            subtypes=data.get('subtypes', [])
        )
    
    def find_card(self, nickname: str) -> Optional[CardData]:
        """Find a card by nickname (normalized match, case insensitive, ignoring special characters)."""
        nickname_normalized = self._normalize_name(nickname)
        
        # Try exact full name match first
        if nickname_normalized in self.cards_by_full_name:
            return self.cards_by_full_name[nickname_normalized]
        
        # Try name only match
        if nickname_normalized in self.cards_by_name:
            return self.cards_by_name[nickname_normalized]
        
        # Try partial matches
        for full_name, card in self.cards_by_full_name.items():
            if nickname_normalized in full_name or full_name in nickname_normalized:
                return card
        
        return None
    
    def create_card_object(self, card_data: CardData, unique_id: int) -> object:
        """Create a game card object from CardData."""
        # Map color string to enum
        color_map = {
            'amber': CardColor.AMBER,
            'amethyst': CardColor.AMETHYST,
            'emerald': CardColor.EMERALD,
            'ruby': CardColor.RUBY,
            'sapphire': CardColor.SAPPHIRE,
            'steel': CardColor.STEEL
        }
        color = color_map.get(card_data.color.lower(), CardColor.AMBER)
        
        # Map rarity string to enum
        rarity_map = {
            'common': Rarity.COMMON,
            'uncommon': Rarity.UNCOMMON,
            'rare': Rarity.RARE,
            'super rare': Rarity.SUPER_RARE,
            'legendary': Rarity.LEGENDARY,
            'enchanted': Rarity.ENCHANTED
        }
        rarity = rarity_map.get(card_data.rarity.lower(), Rarity.COMMON)
        
        # Create appropriate card type
        if card_data.type.lower() == 'character':
            card = CharacterCard(
                id=unique_id,
                name=card_data.name,
                version=card_data.version,
                full_name=card_data.full_name,
                cost=card_data.cost,
                color=color,
                inkwell=card_data.inkwell,
                rarity=rarity,
                set_code=card_data.set_code,
                number=card_data.number,
                story=card_data.story,
                abilities=[],  # We'll handle abilities separately
                strength=card_data.strength if card_data.strength is not None else 1,
                willpower=card_data.willpower if card_data.willpower is not None else 1,
                lore=card_data.lore if card_data.lore is not None else 1,
                subtypes=card_data.subtypes or []
            )
            
            # Add keyword abilities if they exist
            card.composable_abilities = self._create_keyword_abilities(card, card_data.abilities)
            return card
            
        elif card_data.type.lower() == 'action':
            # Check if it's a song
            is_song = any('sing this song' in ability.get('effect', '').lower() 
                         for ability in card_data.abilities)
            
            # Create simple ability for songs
            abilities = []
            if is_song:
                class SimpleAbility:
                    def __init__(self, effect_text):
                        self.effect = effect_text
                
                for ability in card_data.abilities:
                    if 'sing this song' in ability.get('effect', '').lower():
                        abilities.append(SimpleAbility(ability['effect']))
            
            return ActionCard(
                id=unique_id,
                name=card_data.name,
                version=card_data.version,
                full_name=card_data.full_name,
                cost=card_data.cost,
                color=color,
                inkwell=card_data.inkwell,
                rarity=rarity,
                set_code=card_data.set_code,
                number=card_data.number,
                story=card_data.story,
                abilities=abilities
            )
        
        else:  # Item or other
            return ActionCard(  # Use ActionCard as fallback for items
                id=unique_id,
                name=card_data.name,
                version=card_data.version,
                full_name=card_data.full_name,
                cost=card_data.cost,
                color=color,
                inkwell=card_data.inkwell,
                rarity=rarity,
                set_code=card_data.set_code,
                number=card_data.number,
                story=card_data.story,
                abilities=[]
            )
    
    def _create_keyword_abilities(self, character, abilities_data: List[dict]) -> List:
        """Create keyword abilities for a character based on ability data."""
        from ..models.abilities.composable.keyword_abilities import (
            create_rush_ability, create_singer_ability, create_resist_ability,
            create_support_ability, create_evasive_ability, create_bodyguard_ability,
            create_challenger_ability, create_ward_ability, create_reckless_ability,
            create_vanish_ability, create_shift_ability, create_sing_together_ability
        )
        import re
        
        keyword_abilities = []
        
        for ability in abilities_data:
            ability_type = ability.get('type', '').lower()
            keyword = ability.get('keyword', '').lower()
            name = ability.get('name', '').lower()
            effect = ability.get('effect', '').lower()
            full_text = ability.get('fullText', '').lower()
            
            # Handle keyword abilities using the 'keyword' field if available
            if ability_type == 'keyword' and keyword:
                if keyword == 'challenger':
                    # Extract challenger value
                    value = ability.get('keywordValueNumber')
                    if value is None:
                        # Try to extract from keywordValue like "+3"
                        keyword_value = ability.get('keywordValue', '')
                        match = re.search(r'[+]?(\d+)', keyword_value)
                        value = int(match.group(1)) if match else 1
                    keyword_abilities.append(create_challenger_ability(value, character))
                    
                elif keyword == 'rush':
                    keyword_abilities.append(create_rush_ability(character))
                    
                elif keyword == 'evasive':
                    keyword_abilities.append(create_evasive_ability(character))
                    
                elif keyword == 'bodyguard':
                    keyword_abilities.append(create_bodyguard_ability(character))
                    
                elif keyword == 'ward':
                    keyword_abilities.append(create_ward_ability(character))
                    
                elif keyword == 'singer':
                    value = ability.get('keywordValueNumber', 4)
                    keyword_abilities.append(create_singer_ability(value, character))
                    
                elif keyword == 'resist':
                    value = ability.get('keywordValueNumber', 1)
                    keyword_abilities.append(create_resist_ability(value, character))
                    
                elif keyword == 'shift':
                    value = ability.get('keywordValueNumber', 1)
                    keyword_abilities.append(create_shift_ability(value, character))
                    
                elif keyword == 'reckless':
                    keyword_abilities.append(create_reckless_ability(character))
                    
                elif keyword == 'vanish':
                    keyword_abilities.append(create_vanish_ability(character))
                    
                elif keyword in ['sing together', 'singtogether']:
                    value = ability.get('keywordValueNumber', 4)
                    keyword_abilities.append(create_sing_together_ability(value, character))
                    
                elif keyword == 'support':
                    keyword_abilities.append(create_support_ability(character))
            
            # Only process abilities with proper keyword field to avoid false positives
            # Effect text can contain phrases like "grants Evasive" which doesn't mean the card has Evasive
            else:
                # Skip abilities without proper keyword field - only use structured keyword data
                pass
        
        return keyword_abilities