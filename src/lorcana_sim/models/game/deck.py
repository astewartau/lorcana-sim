"""Deck model for Lorcana simulation."""

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from collections import Counter

from ..cards.base_card import Card
from ..cards.card_factory import CardFactory


@dataclass
class DeckCard:
    """A card in a deck with its quantity."""
    card: Card
    quantity: int
    
    def __post_init__(self) -> None:
        """Validate deck card."""
        if self.quantity <= 0:
            raise ValueError(f"Card quantity must be positive: {self.quantity}")
        if self.quantity > 4:
            raise ValueError(f"Cannot have more than 4 copies of a card: {self.quantity}")


@dataclass
class Deck:
    """Represents a Lorcana deck."""
    name: str
    cards: List[DeckCard] = field(default_factory=list)
    
    @property
    def total_cards(self) -> int:
        """Total number of cards in deck."""
        return sum(deck_card.quantity for deck_card in self.cards)
    
    @property
    def unique_cards(self) -> int:
        """Number of unique cards in deck."""
        return len(self.cards)
    
    def is_legal(self) -> Tuple[bool, List[str]]:
        """Check if deck is legal for play."""
        errors = []
        
        # Must have exactly 60 cards
        if self.total_cards != 60:
            errors.append(f"Deck must have 60 cards, has {self.total_cards}")
        
        # Max 4 of each card (this is already enforced by DeckCard)
        for deck_card in self.cards:
            if deck_card.quantity > 4:
                errors.append(f"Too many copies of {deck_card.card.full_name}: {deck_card.quantity}")
        
        # Check for duplicate cards (same ID)
        card_ids = [deck_card.card.id for deck_card in self.cards]
        duplicate_ids = [card_id for card_id, count in Counter(card_ids).items() if count > 1]
        if duplicate_ids:
            errors.append(f"Duplicate card IDs found: {duplicate_ids}")
        
        return len(errors) == 0, errors
    
    def shuffle(self) -> List[Card]:
        """Return a shuffled list of all cards in the deck."""
        all_cards = []
        for deck_card in self.cards:
            all_cards.extend([deck_card.card] * deck_card.quantity)
        random.shuffle(all_cards)
        return all_cards
    
    def get_color_distribution(self) -> Dict[str, int]:
        """Get the distribution of cards by color."""
        color_count = Counter()
        for deck_card in self.cards:
            color_count[deck_card.card.color.value] += deck_card.quantity
        return dict(color_count)
    
    def get_cost_curve(self) -> Dict[int, int]:
        """Get the distribution of cards by mana cost."""
        cost_count = Counter()
        for deck_card in self.cards:
            cost_count[deck_card.card.cost] += deck_card.quantity
        return dict(cost_count)
    
    def get_type_distribution(self) -> Dict[str, int]:
        """Get the distribution of cards by type."""
        type_count = Counter()
        for deck_card in self.cards:
            type_count[deck_card.card.card_type] += deck_card.quantity
        return dict(type_count)
    
    def add_card(self, card: Card, quantity: int = 1) -> None:
        """Add a card to the deck."""
        # Check if card already exists
        for deck_card in self.cards:
            if deck_card.card.id == card.id:
                new_quantity = deck_card.quantity + quantity
                if new_quantity > 4:
                    raise ValueError(f"Cannot add {quantity} copies - would exceed 4 copy limit")
                deck_card.quantity = new_quantity
                return
        
        # Add new card
        self.cards.append(DeckCard(card=card, quantity=quantity))
    
    def remove_card(self, card_id: int, quantity: int = 1) -> bool:
        """Remove a card from the deck. Returns True if card was found and removed."""
        for deck_card in self.cards:
            if deck_card.card.id == card_id:
                if deck_card.quantity <= quantity:
                    self.cards.remove(deck_card)
                else:
                    deck_card.quantity -= quantity
                return True
        return False
    
    def find_card(self, card_id: int) -> DeckCard | None:
        """Find a card in the deck by ID."""
        for deck_card in self.cards:
            if deck_card.card.id == card_id:
                return deck_card
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the deck composition."""
        return {
            "name": self.name,
            "total_cards": self.total_cards,
            "unique_cards": self.unique_cards,
            "color_distribution": self.get_color_distribution(),
            "cost_curve": self.get_cost_curve(),
            "type_distribution": self.get_type_distribution(),
        }
    
    @classmethod
    def from_dreamborn(cls, dreamborn_data: Dict[str, Any], card_database: List[Dict[str, Any]], name: str = "Untitled Deck") -> "Deck":
        """Create deck from Dreamborn format using card database."""
        from ...loaders.dreamborn_parser import DreambornParser
        
        # If dreamborn_data is a file path, load it
        if isinstance(dreamborn_data, str):
            parser = DreambornParser(dreamborn_data)
            deck_info = parser.get_deck_info()
        else:
            # Assume it's already parsed data
            # For now, we'll need to implement this based on the actual format
            raise NotImplementedError("Direct dreamborn data parsing not yet implemented")
        
        deck = cls(name=name)
        
        # Convert dreamborn cards to our card objects
        for dreamborn_card in deck_info.cards:
            # Find the card in the database by nickname (full name)
            card_data = CardFactory.find_card_by_dreamborn_name(card_database, dreamborn_card.nickname)
            if card_data:
                card = CardFactory.from_json(card_data)
                deck.add_card(card, dreamborn_card.quantity)
            else:
                print(f"Warning: Could not find card '{dreamborn_card.nickname}' in database")
        
        return deck
    
    def __str__(self) -> str:
        """String representation of the deck."""
        return f"Deck '{self.name}' ({self.total_cards} cards, {self.unique_cards} unique)"