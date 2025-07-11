"""Player model for Lorcana simulation."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import Counter

from ..cards.base_card import Card, CardColor
from ..cards.character_card import CharacterCard
from ..cards.item_card import ItemCard


@dataclass
class Player:
    """Represents a player in a Lorcana game."""
    name: str
    
    # Game Zones
    hand: List[Card] = field(default_factory=list)
    deck: List[Card] = field(default_factory=list)  # Remaining cards
    discard_pile: List[Card] = field(default_factory=list)
    inkwell: List[Card] = field(default_factory=list)  # Cards used as ink
    
    # Characters and Items in play
    characters: List[CharacterCard] = field(default_factory=list)
    items: List[ItemCard] = field(default_factory=list)
    
    # Game Resources
    lore: int = 0
    
    # Game State Tracking
    has_played_ink_this_turn: bool = False
    
    @property
    def available_ink(self) -> int:
        """Total ink available this turn."""
        return len(self.inkwell)
    
    @property
    def ink_by_color(self) -> Dict[CardColor, int]:
        """Available ink by color."""
        ink_colors = Counter()
        for card in self.inkwell:
            ink_colors[card.color] += 1
        return dict(ink_colors)
    
    @property
    def hand_size(self) -> int:
        """Number of cards in hand."""
        return len(self.hand)
    
    @property
    def deck_size(self) -> int:
        """Number of cards remaining in deck."""
        return len(self.deck)
    
    @property
    def characters_in_play(self) -> int:
        """Number of characters in play."""
        return len(self.characters)
    
    @property
    def items_in_play(self) -> int:
        """Number of items in play."""
        return len(self.items)
    
    def can_afford(self, card: Card) -> bool:
        """Check if player can afford to play a card."""
        if self.available_ink < card.cost:
            return False
        
        # TODO: Add color requirement checking
        # For now, assume any ink can pay for any card
        return True
    
    def can_play_ink(self) -> bool:
        """Check if player can play a card as ink this turn."""
        return not self.has_played_ink_this_turn
    
    def draw_card(self) -> Optional[Card]:
        """Draw a card from deck to hand."""
        if self.deck:
            card = self.deck.pop(0)
            self.hand.append(card)
            return card
        return None
    
    def draw_cards(self, count: int) -> List[Card]:
        """Draw multiple cards from deck."""
        drawn = []
        for _ in range(count):
            card = self.draw_card()
            if card:
                drawn.append(card)
            else:
                break
        return drawn
    
    def play_ink(self, card: Card) -> bool:
        """Play a card as ink (once per turn)."""
        if not self.can_play_ink():
            return False
        
        if not card.can_be_inked():
            return False
        
        if card in self.hand:
            self.hand.remove(card)
            self.inkwell.append(card)
            self.has_played_ink_this_turn = True
            return True
        
        return False
    
    def play_character(self, card: CharacterCard) -> bool:
        """Play a character card."""
        if not self.can_afford(card):
            return False
        
        if card in self.hand:
            self.hand.remove(card)
            self.characters.append(card)
            # TODO: Pay ink cost
            return True
        
        return False
    
    def play_item(self, card: ItemCard) -> bool:
        """Play an item card."""
        if not self.can_afford(card):
            return False
        
        if card in self.hand:
            self.hand.remove(card)
            self.items.append(card)
            # TODO: Pay ink cost
            return True
        
        return False
    
    def discard_card(self, card: Card) -> bool:
        """Discard a card from hand."""
        if card in self.hand:
            self.hand.remove(card)
            self.discard_pile.append(card)
            return True
        return False
    
    def banish_character(self, character: CharacterCard) -> bool:
        """Remove a character from play (send to discard)."""
        if character in self.characters:
            self.characters.remove(character)
            self.discard_pile.append(character)
            return True
        return False
    
    def ready_all_characters(self) -> None:
        """Ready all exerted characters (start of turn)."""
        for character in self.characters:
            character.ready()
    
    def get_ready_characters(self) -> List[CharacterCard]:
        """Get all ready (non-exerted) characters."""
        return [char for char in self.characters if not char.exerted]
    
    def get_exerted_characters(self) -> List[CharacterCard]:
        """Get all exerted characters."""
        return [char for char in self.characters if char.exerted]
    
    def get_characters_that_can_quest(self) -> List[CharacterCard]:
        """Get all characters that can quest."""
        return [char for char in self.characters if char.can_quest()]
    
    def get_characters_that_can_challenge(self) -> List[CharacterCard]:
        """Get all characters that can challenge."""
        return [char for char in self.characters if char.can_challenge()]
    
    def quest_with_character(self, character: CharacterCard) -> int:
        """Quest with a character, returning lore gained."""
        if not character.can_quest():
            return 0
        
        if character not in self.characters:
            return 0
        
        character.exert()
        lore_gained = character.current_lore
        self.lore += lore_gained
        return lore_gained
    
    def challenge_character(self, attacking_character: CharacterCard, defending_character: CharacterCard) -> bool:
        """Challenge another character."""
        if not attacking_character.can_challenge():
            return False
        
        if attacking_character not in self.characters:
            return False
        
        # Execute the challenge
        attacking_character.exert()
        
        # Deal damage
        attacking_character.deal_damage(defending_character.current_strength)
        defending_character.deal_damage(attacking_character.current_strength)
        
        return True
    
    def start_turn(self) -> None:
        """Perform start-of-turn actions."""
        self.ready_all_characters()
        self.has_played_ink_this_turn = False
    
    def get_game_summary(self) -> Dict[str, any]:
        """Get a summary of the player's current state."""
        return {
            "name": self.name,
            "lore": self.lore,
            "hand_size": self.hand_size,
            "deck_size": self.deck_size,
            "available_ink": self.available_ink,
            "characters_in_play": self.characters_in_play,
            "ready_characters": len(self.get_ready_characters()),
            "exerted_characters": len(self.get_exerted_characters()),
            "items_in_play": self.items_in_play,
        }
    
    def __str__(self) -> str:
        """String representation of the player."""
        return f"{self.name} ({self.lore} lore, {self.hand_size} cards in hand, {self.available_ink} ink)"