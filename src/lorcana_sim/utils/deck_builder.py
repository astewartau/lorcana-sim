"""Deck building utilities for Lorcana simulation."""

import random
from typing import List, Dict, Optional, Set
from collections import defaultdict, Counter

from ..models.cards.base_card import Card, CardColor
from ..models.cards.character_card import CharacterCard
from ..models.cards.card_factory import CardFactory
from ..models.game.deck import Deck


class DeckBuilder:
    """Utility class for building Lorcana decks with various strategies."""
    
    def __init__(self, card_database: List[Dict]):
        """Initialize with a card database."""
        self.card_database = card_database
        self._cards_cache = None
        self._cards_by_color = None
        self._cards_by_cost = None
        self._cards_by_type = None
    
    @property
    def cards(self) -> List[Card]:
        """Get all valid cards from the database."""
        if self._cards_cache is None:
            self._cards_cache = []
            for card_data in self.card_database:
                try:
                    card = CardFactory.from_json(card_data)
                    self._cards_cache.append(card)
                except Exception:
                    continue
        return self._cards_cache
    
    @property
    def cards_by_color(self) -> Dict[CardColor, List[Card]]:
        """Get cards organized by color."""
        if self._cards_by_color is None:
            self._cards_by_color = defaultdict(list)
            for card in self.cards:
                self._cards_by_color[card.color].append(card)
        return self._cards_by_color
    
    @property
    def cards_by_cost(self) -> Dict[int, List[Card]]:
        """Get cards organized by cost."""
        if self._cards_by_cost is None:
            self._cards_by_cost = defaultdict(list)
            for card in self.cards:
                self._cards_by_cost[card.cost].append(card)
        return self._cards_by_cost
    
    @property
    def cards_by_type(self) -> Dict[str, List[Card]]:
        """Get cards organized by type."""
        if self._cards_by_type is None:
            self._cards_by_type = defaultdict(list)
            for card in self.cards:
                self._cards_by_type[card.card_type].append(card)
        return self._cards_by_type
    
    def build_random_deck(self, deck_name: str = "Random Deck", seed: Optional[int] = None) -> Optional[Deck]:
        """Build a completely random legal deck."""
        if seed is not None:
            random.seed(seed)
        
        if len(self.cards) < 15:
            return None
        
        # Select 15 random unique cards
        selected_cards = random.sample(self.cards, 15)
        
        deck = Deck(deck_name)
        for card in selected_cards:
            deck.add_card(card, 4)
        
        return deck
    
    def build_mono_color_deck(self, color: CardColor, deck_name: Optional[str] = None, 
                             seed: Optional[int] = None) -> Optional[Deck]:
        """Build a deck focusing on a single color."""
        if seed is not None:
            random.seed(seed)
        
        if deck_name is None:
            deck_name = f"{color.value} Deck"
        
        available_cards = self.cards_by_color.get(color, [])
        if len(available_cards) < 15:
            return None
        
        # Select cards with preference for characters and good curve
        selected_cards = self._select_balanced_cards(available_cards, 15)
        
        deck = Deck(deck_name)
        for card in selected_cards:
            deck.add_card(card, 4)
        
        return deck
    
    def build_aggro_deck(self, primary_color: CardColor, deck_name: Optional[str] = None,
                        seed: Optional[int] = None) -> Optional[Deck]:
        """Build an aggressive deck focused on low-cost characters."""
        if seed is not None:
            random.seed(seed)
        
        if deck_name is None:
            deck_name = f"{primary_color.value} Aggro"
        
        # Focus on low-cost characters and efficient spells
        available_cards = self.cards_by_color.get(primary_color, [])
        
        # Prefer low-cost cards
        low_cost_cards = [c for c in available_cards if c.cost <= 3]
        mid_cost_cards = [c for c in available_cards if 4 <= c.cost <= 6]
        
        if len(low_cost_cards) < 8:
            return None
        
        deck = Deck(deck_name)
        
        # Build with aggressive curve: lots of 1-3 cost, some 4-6 cost
        selected_low = random.sample(low_cost_cards, min(10, len(low_cost_cards)))
        selected_mid = random.sample(mid_cost_cards, min(5, len(mid_cost_cards)))
        
        # Add cards with varying quantities for realistic distribution
        for i, card in enumerate(selected_low):
            quantity = 4 if i < 5 else 3  # Core vs support
            deck.add_card(card, quantity)
        
        for card in selected_mid:
            deck.add_card(card, 2)  # Fewer high-cost cards
        
        # Fill to 60 if needed
        self._fill_deck_to_60(deck, available_cards)
        
        return deck
    
    def build_control_deck(self, primary_color: CardColor, deck_name: Optional[str] = None,
                          seed: Optional[int] = None) -> Optional[Deck]:
        """Build a control deck focused on high-value cards and card advantage."""
        if seed is not None:
            random.seed(seed)
        
        if deck_name is None:
            deck_name = f"{primary_color.value} Control"
        
        available_cards = self.cards_by_color.get(primary_color, [])
        
        # Prefer higher-cost, high-value cards
        low_cost_cards = [c for c in available_cards if c.cost <= 3]
        high_cost_cards = [c for c in available_cards if c.cost >= 5]
        
        if len(high_cost_cards) < 5:
            return None
        
        deck = Deck(deck_name)
        
        # Control curve: some early game, focus on late game
        selected_low = random.sample(low_cost_cards, min(5, len(low_cost_cards)))
        selected_high = random.sample(high_cost_cards, min(8, len(high_cost_cards)))
        
        # Add fewer copies of high-cost cards
        for card in selected_low:
            deck.add_card(card, 3)
        
        for i, card in enumerate(selected_high):
            quantity = 3 if i < 3 else 2  # Fewer copies of expensive cards
            deck.add_card(card, quantity)
        
        # Fill to 60
        self._fill_deck_to_60(deck, available_cards)
        
        return deck
    
    def build_character_tribal_deck(self, subtype: str, deck_name: Optional[str] = None,
                                   seed: Optional[int] = None) -> Optional[Deck]:
        """Build a deck focused on a specific character subtype."""
        if seed is not None:
            random.seed(seed)
        
        if deck_name is None:
            deck_name = f"{subtype} Tribal"
        
        # Find characters with the specified subtype
        tribal_characters = []
        for card in self.cards:
            if isinstance(card, CharacterCard) and card.has_subtype(subtype):
                tribal_characters.append(card)
        
        if len(tribal_characters) < 8:
            return None
        
        deck = Deck(deck_name)
        
        # Add tribal characters
        selected_tribal = random.sample(tribal_characters, min(12, len(tribal_characters)))
        for i, card in enumerate(selected_tribal):
            quantity = 4 if i < 6 else 3
            deck.add_card(card, quantity)
        
        # Fill with support cards of compatible colors
        used_colors = set(card.color for card in selected_tribal)
        support_cards = [c for c in self.cards if c.color in used_colors and c not in selected_tribal]
        
        if support_cards:
            remaining_slots = 60 - deck.total_cards
            if remaining_slots > 0:
                support_selection = random.sample(support_cards, min(remaining_slots // 2, len(support_cards)))
                for card in support_selection:
                    deck.add_card(card, 2)
        
        # Fill to 60
        self._fill_deck_to_60(deck, self.cards)
        
        return deck
    
    def build_balanced_deck(self, primary_colors: List[CardColor], deck_name: Optional[str] = None,
                           seed: Optional[int] = None) -> Optional[Deck]:
        """Build a balanced deck with good curve and color distribution."""
        if seed is not None:
            random.seed(seed)
        
        if deck_name is None:
            color_names = "-".join([c.value for c in primary_colors])
            deck_name = f"{color_names} Balanced"
        
        # Get cards from primary colors
        available_cards = []
        for color in primary_colors:
            available_cards.extend(self.cards_by_color.get(color, []))
        
        if len(available_cards) < 15:
            return None
        
        # Build with good curve distribution
        deck = Deck(deck_name)
        
        # Target distribution: 20% low (1-2), 40% mid (3-5), 30% high (6+), 10% very high (8+)
        low_cost = [c for c in available_cards if c.cost <= 2]
        mid_cost = [c for c in available_cards if 3 <= c.cost <= 5]
        high_cost = [c for c in available_cards if 6 <= c.cost <= 7]
        very_high_cost = [c for c in available_cards if c.cost >= 8]
        
        # Select cards based on curve
        selections = [
            (low_cost, 3, 4),      # 3 cards, 4 copies each = 12 cards
            (mid_cost, 6, 4),      # 6 cards, 4 copies each = 24 cards  
            (high_cost, 4, 3),     # 4 cards, 3 copies each = 12 cards
            (very_high_cost, 2, 2) # 2 cards, 2 copies each = 4 cards
        ]
        
        for card_pool, num_cards, copies in selections:
            if len(card_pool) >= num_cards:
                selected = random.sample(card_pool, num_cards)
                for card in selected:
                    deck.add_card(card, copies)
        
        # Fill remaining slots
        self._fill_deck_to_60(deck, available_cards)
        
        return deck
    
    def _select_balanced_cards(self, available_cards: List[Card], count: int) -> List[Card]:
        """Select cards with balanced cost distribution."""
        if len(available_cards) <= count:
            return available_cards[:count]
        
        # Try to get a good curve
        by_cost = defaultdict(list)
        for card in available_cards:
            by_cost[card.cost].append(card)
        
        selected = []
        costs = sorted(by_cost.keys())
        
        # Distribute selection across different costs
        per_cost = max(1, count // len(costs))
        
        for cost in costs:
            if len(selected) >= count:
                break
            
            available_at_cost = by_cost[cost]
            take = min(per_cost, len(available_at_cost), count - len(selected))
            selected.extend(random.sample(available_at_cost, take))
        
        # Fill remaining slots randomly
        while len(selected) < count:
            remaining = [c for c in available_cards if c not in selected]
            if not remaining:
                break
            selected.append(random.choice(remaining))
        
        return selected[:count]
    
    def _fill_deck_to_60(self, deck: Deck, available_cards: List[Card]) -> None:
        """Fill a deck to exactly 60 cards."""
        while deck.total_cards < 60:
            # Try to add more copies of existing cards first
            added = False
            for deck_card in deck.cards:
                if deck_card.quantity < 4 and deck.total_cards < 60:
                    deck_card.quantity += 1
                    added = True
                    break
            
            if not added:
                # Add new cards if we can't increase existing ones
                used_ids = {dc.card.id for dc in deck.cards}
                unused_cards = [c for c in available_cards if c.id not in used_ids]
                
                if unused_cards:
                    new_card = random.choice(unused_cards)
                    remaining_slots = 60 - deck.total_cards
                    quantity = min(4, remaining_slots)
                    deck.add_card(new_card, quantity)
                else:
                    break  # Can't add more cards
    
    def get_statistics(self) -> Dict:
        """Get statistics about the card database."""
        stats = {
            "total_cards": len(self.cards),
            "by_color": {color.value: len(cards) for color, cards in self.cards_by_color.items()},
            "by_type": {card_type: len(cards) for card_type, cards in self.cards_by_type.items()},
            "by_cost": {cost: len(cards) for cost, cards in self.cards_by_cost.items()},
            "cost_range": (min(self.cards_by_cost.keys()), max(self.cards_by_cost.keys())) if self.cards_by_cost else (0, 0)
        }
        return stats