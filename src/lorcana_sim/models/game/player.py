"""Player model for Lorcana simulation."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from collections import Counter

from ..cards.base_card import Card, CardColor
from ..cards.character_card import CharacterCard
from ..cards.action_card import ActionCard
from ..cards.item_card import ItemCard


@dataclass
class Player:
    """Represents a player in a Lorcana game with complete state tracking."""
    name: str
    
    # Card Zones
    hand: List[Card] = field(default_factory=list)
    deck: List[Card] = field(default_factory=list)
    discard_pile: List[Card] = field(default_factory=list)
    inkwell: List[Card] = field(default_factory=list)
    
    # In-Play Zones
    characters_in_play: List[CharacterCard] = field(default_factory=list)
    items_in_play: List[ItemCard] = field(default_factory=list)
    
    # Resources
    lore: int = 0
    
    
    @property
    def total_ink(self) -> int:
        """Total ink available (size of inkwell)."""
        return len(self.inkwell)
    
    @property
    def available_ink(self) -> int:
        """Ink available to spend this turn."""
        return sum(1 for card in self.inkwell if not card.exerted)
    
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
    
    def can_afford(self, card: Card) -> bool:
        """Check if player can afford to play a card."""
        return self.available_ink >= card.cost
    
    def can_afford_with_colors(self, card: Card, required_colors: Dict[CardColor, int] = None) -> bool:
        """Check if player can afford card with color requirements."""
        if not self.can_afford(card):
            return False
        
        if required_colors:
            available_colors = self.ink_by_color
            for color, required_amount in required_colors.items():
                if available_colors.get(color, 0) < required_amount:
                    return False
        
        return True
    
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
        """Play a card as ink."""
        if not card.can_be_inked() or card not in self.hand:
            return False
        
        self.hand.remove(card)
        self.inkwell.append(card)
        return True
    
    def play_character(self, character: CharacterCard, ink_cost: int) -> bool:
        """Play a character card."""
        if character not in self.hand or not self.can_afford(character):
            return False
        
        self.hand.remove(character)
        # Set the controller when the character is played
        character.controller = self
        self.characters_in_play.append(character)
        exerted = self.spend_ink(ink_cost)
        return len(exerted) == ink_cost
    
    def play_action(self, action: ActionCard, ink_cost: int) -> bool:
        """Play an action card."""
        if action not in self.hand or not self.can_afford(action):
            return False
        
        self.hand.remove(action)
        self.discard_pile.append(action)
        exerted = self.spend_ink(ink_cost)
        return len(exerted) == ink_cost
    
    def play_item(self, item: ItemCard, ink_cost: int) -> bool:
        """Play an item card."""
        if item not in self.hand or not self.can_afford(item):
            return False
        
        self.hand.remove(item)
        self.items_in_play.append(item)
        exerted = self.spend_ink(ink_cost)
        return len(exerted) == ink_cost
    
    def spend_ink(self, amount: int) -> List[Card]:
        """Spend ink for playing cards/abilities.
        
        Returns:
            List of cards that were exerted as ink.
        """
        available_cards = [card for card in self.inkwell if not card.exerted]
        if len(available_cards) < amount:
            return []
        
        # Exert the first X available cards
        exerted_cards = []
        for card in available_cards[:amount]:
            card.exerted = True
            exerted_cards.append(card)
        
        return exerted_cards
    
    def reset_turn_state(self) -> None:
        """Reset state at start of turn."""
        pass  # Ink readying is now handled by ReadyInk effect
    
    def gain_lore(self, amount: int) -> None:
        """Gain lore points."""
        self.lore += amount
    
    def discard_card(self, card: Card) -> bool:
        """Discard a card from hand."""
        if card in self.hand:
            self.hand.remove(card)
            self.discard_pile.append(card)
            return True
        return False
    
    def banish_character(self, character: CharacterCard) -> bool:
        """Remove a character from play (send to discard)."""
        if character in self.characters_in_play:
            self.characters_in_play.remove(character)
            self.discard_pile.append(character)
            return True
        return False
    
    def ready_all_characters(self) -> None:
        """Ready all exerted characters (start of turn).
        
        Note: Ink cards are readied separately using ReadyInk effect.
        """
        for character in self.characters_in_play:
            character.ready()
    
    def get_ready_characters(self) -> List[CharacterCard]:
        """Get all ready (unexerted) characters."""
        return [char for char in self.characters_in_play if not char.exerted]
    
    def get_characters_with_ability(self, ability_keyword: str) -> List[CharacterCard]:
        """Get characters with specific keyword ability."""
        result = []
        for character in self.characters_in_play:
            for ability in character.abilities:
                if hasattr(ability, 'keyword') and ability.keyword == ability_keyword:
                    result.append(character)
                    break
        return result
    
    def has_singer_for_cost(self, required_cost: int) -> List[CharacterCard]:
        """Get singers that can sing songs of given cost."""
        singers = []
        for character in self.get_ready_characters():
            for ability in character.abilities:
                if (hasattr(ability, 'keyword') and 
                    ability.keyword == 'Singer' and
                    hasattr(ability, 'get_effective_sing_cost') and
                    ability.get_effective_sing_cost() >= required_cost):
                    singers.append(character)
                    break
        return singers
    
    def start_turn(self) -> None:
        """Perform start-of-turn actions."""
        self.ready_all_characters()
        self.reset_turn_state()
    
    def sing_song(self, singer: 'CharacterCard', song: 'ActionCard') -> bool:
        """Have a character sing a song (exert character, discard song)."""
        # Validate that singer is ready and belongs to this player
        if singer not in self.characters_in_play or singer.exerted:
            return False
            
        # Validate that song is in hand
        if song not in self.hand:
            return False
            
        # Exert the singer
        singer.exerted = True
        
        # Remove song from hand and put in discard
        self.hand.remove(song)
        self.discard_pile.append(song)
        
        return True
    
    def return_to_hand(self, card: Card) -> bool:
        """Return a card from play to hand."""
        # Remove from characters in play
        if hasattr(card, 'strength') and card in self.characters_in_play:
            self.characters_in_play.remove(card)
            self.hand.append(card)
            return True
        
        # Remove from items in play
        if card in self.items_in_play:
            self.items_in_play.remove(card)
            self.hand.append(card)
            return True
        
        # Card wasn't in play
        return False
    
    def get_game_summary(self) -> Dict[str, any]:
        """Get a summary of the player's current state."""
        return {
            "name": self.name,
            "lore": self.lore,
            "hand_size": self.hand_size,
            "deck_size": self.deck_size,
            "available_ink": self.available_ink,
            "characters_in_play": len(self.characters_in_play),
            "ready_characters": len(self.get_ready_characters()),
            "items_in_play": len(self.items_in_play),
        }
    
    def __str__(self) -> str:
        """String representation of the player."""
        return f"{self.name} ({self.lore} lore, {self.hand_size} cards in hand, {self.available_ink} ink)"
    
    def __repr__(self) -> str:
        """Use the same representation as __str__ for cleaner output in collections."""
        return self.__str__()