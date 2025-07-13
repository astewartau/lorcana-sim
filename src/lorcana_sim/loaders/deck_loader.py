"""Deck loader that combines dreamborn parser with card database."""

import random
from typing import List, Tuple
from pathlib import Path

from .dreamborn_parser import DreambornParser
from .card_database import CardDatabase
from ..models.game.player import Player


class DeckLoader:
    """Loads decks from dreamborn format and creates game-ready card objects."""
    
    def __init__(self, cards_json_path: str):
        self.card_db = CardDatabase(cards_json_path)
        self._unique_id_counter = 10000  # Start high to avoid conflicts
    
    def load_deck_from_file(self, deck_file_path: str, player_name: str) -> Player:
        """Load a deck from dreamborn format and create a Player with that deck."""
        parser = DreambornParser(deck_file_path)
        deck_info = parser.get_deck_info()
        
        print(f"📦 Loading deck for {player_name}:")
        print(f"   Total cards: {deck_info.total_cards}")
        print(f"   Unique cards: {deck_info.unique_cards}")
        
        # Create card objects
        deck_cards = []
        found_cards = 0
        missing_cards = []
        
        for deck_card in deck_info.cards:
            card_data = self.card_db.find_card(deck_card.nickname)
            
            if card_data:
                # Create the specified number of copies
                for _ in range(deck_card.quantity):
                    card_obj = self.card_db.create_card_object(card_data, self._get_unique_id())
                    deck_cards.append(card_obj)
                    found_cards += 1
            else:
                missing_cards.append(f"{deck_card.nickname} (x{deck_card.quantity})")
        
        if missing_cards:
            print(f"   ⚠️  Missing cards ({len(missing_cards)}): {', '.join(missing_cards[:5])}")
            if len(missing_cards) > 5:
                print(f"      ... and {len(missing_cards) - 5} more")
        
        print(f"   ✅ Successfully loaded: {found_cards}/{deck_info.total_cards} cards")
        
        # Shuffle the deck
        random.shuffle(deck_cards)
        
        # Create player
        player = Player(player_name)
        player.deck = deck_cards
        
        # Deal starting hand (7 cards)
        for _ in range(7):
            if player.deck:
                player.hand.append(player.deck.pop(0))
        
        print(f"   🃏 {player_name} starting hand: {len(player.hand)} cards, deck: {len(player.deck)} cards")
        return player
    
    def _get_unique_id(self) -> int:
        """Get a unique ID for card objects."""
        self._unique_id_counter += 1
        return self._unique_id_counter
    
    def load_two_decks(self, deck1_path: str, deck2_path: str, 
                      player1_name: str = "Player 1", player2_name: str = "Player 2") -> Tuple[Player, Player]:
        """Load two decks and return two players ready to play."""
        print("🎴 Loading decks for game...")
        print()
        
        player1 = self.load_deck_from_file(deck1_path, player1_name)
        print()
        player2 = self.load_deck_from_file(deck2_path, player2_name)
        print()
        
        return player1, player2
    
    def get_deck_summary(self, deck_file_path: str) -> dict:
        """Get a summary of what's in a deck file."""
        parser = DreambornParser(deck_file_path)
        deck_info = parser.get_deck_info()
        
        summary = {
            'total_cards': deck_info.total_cards,
            'unique_cards': deck_info.unique_cards,
            'found_cards': 0,
            'missing_cards': [],
            'characters': [],
            'actions': [],
            'items': []
        }
        
        for deck_card in deck_info.cards:
            card_data = self.card_db.find_card(deck_card.nickname)
            
            if card_data:
                summary['found_cards'] += deck_card.quantity
                
                card_info = {
                    'name': card_data.full_name,
                    'cost': card_data.cost,
                    'quantity': deck_card.quantity,
                    'abilities': [ab.get('name', '') for ab in card_data.abilities]
                }
                
                if card_data.type.lower() == 'character':
                    card_info['stats'] = f"{card_data.strength}/{card_data.willpower}"
                    card_info['lore'] = card_data.lore
                    summary['characters'].append(card_info)
                elif card_data.type.lower() == 'action':
                    summary['actions'].append(card_info)
                else:
                    summary['items'].append(card_info)
            else:
                summary['missing_cards'].append(f"{deck_card.nickname} (x{deck_card.quantity})")
        
        return summary