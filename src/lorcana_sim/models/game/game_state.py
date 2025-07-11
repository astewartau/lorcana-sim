"""Game state model for Lorcana simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Any

from .player import Player
from ..cards.location_card import LocationCard


class Phase(Enum):
    """Game phases in Lorcana."""
    READY = "ready"
    SET = "set"
    DRAW = "draw"
    MAIN = "main"
    END = "end"


class GameAction(Enum):
    """Possible game actions."""
    PLAY_INK = "play_ink"
    PLAY_CARD = "play_card"
    QUEST = "quest"
    CHALLENGE = "challenge"
    ACTIVATE_ABILITY = "activate_ability"
    PASS_TURN = "pass_turn"
    PASS_PHASE = "pass_phase"


@dataclass
class GameState:
    """Represents the current state of a Lorcana game."""
    
    # Players
    players: List[Player]
    active_player_index: int = 0
    
    # Turn/Phase tracking
    turn_number: int = 1
    current_phase: Phase = Phase.READY
    
    # Game Rules State
    first_turn_skip_draw: bool = True  # First player skips draw on turn 1
    
    # Locations in play (shared)
    locations: List[LocationCard] = field(default_factory=list)
    
    # Game over state
    winner: Optional[Player] = None
    game_over: bool = False
    
    def __post_init__(self) -> None:
        """Validate game state after creation."""
        if len(self.players) < 2:
            raise ValueError("Game must have at least 2 players")
        if self.active_player_index >= len(self.players):
            raise ValueError("Active player index out of range")
    
    @property
    def active_player(self) -> Player:
        """Get the currently active player."""
        return self.players[self.active_player_index]
    
    @property
    def other_players(self) -> List[Player]:
        """Get all players except the active player."""
        return [p for i, p in enumerate(self.players) if i != self.active_player_index]
    
    @property
    def is_first_turn(self) -> bool:
        """Check if this is the first turn of the game."""
        return self.turn_number == 1
    
    @property
    def should_skip_draw(self) -> bool:
        """Check if the current player should skip the draw phase."""
        return self.is_first_turn and self.first_turn_skip_draw and self.active_player_index == 0
    
    def is_game_over(self) -> Tuple[bool, Optional[Player]]:
        """Check if game is over and who won."""
        if self.game_over:
            return True, self.winner
        
        # Check for 20 lore win condition
        for player in self.players:
            if player.lore >= 20:
                self.game_over = True
                self.winner = player
                return True, player
        
        # Check for deck-out condition
        for player in self.players:
            if player.deck_size == 0 and player.hand_size == 0:
                # Player with no cards loses
                # Winner is the player with the most lore, or first other player if tied
                other_players = [p for p in self.players if p != player]
                winner = max(other_players, key=lambda p: p.lore)
                self.game_over = True
                self.winner = winner
                return True, winner
        
        return False, None
    
    def get_legal_actions(self) -> List[Tuple[GameAction, Any]]:
        """Get all legal actions for the current player/phase."""
        actions = []
        
        if self.current_phase == Phase.MAIN:
            # Can always pass turn from main phase
            actions.append((GameAction.PASS_TURN, None))
            
            # Can play ink if allowed
            if self.active_player.can_play_ink():
                inkable_cards = [card for card in self.active_player.hand if card.can_be_inked()]
                for card in inkable_cards:
                    actions.append((GameAction.PLAY_INK, card))
            
            # Can play cards if affordable
            playable_cards = [card for card in self.active_player.hand if self.active_player.can_afford(card)]
            for card in playable_cards:
                actions.append((GameAction.PLAY_CARD, card))
            
            # Can quest with ready characters
            questable_characters = self.active_player.get_characters_that_can_quest()
            for character in questable_characters:
                actions.append((GameAction.QUEST, character))
            
            # Can challenge with ready characters
            challengeable_characters = self.active_player.get_characters_that_can_challenge()
            if challengeable_characters:
                # Find valid targets (opponent characters)
                for opponent in self.other_players:
                    for target in opponent.characters:
                        if target.is_alive:
                            for attacker in challengeable_characters:
                                actions.append((GameAction.CHALLENGE, (attacker, target)))
        
        else:
            # Can pass phase from any other phase
            actions.append((GameAction.PASS_PHASE, None))
        
        return actions
    
    def advance_phase(self) -> None:
        """Move to the next phase of the turn."""
        if self.current_phase == Phase.READY:
            self.current_phase = Phase.SET
        elif self.current_phase == Phase.SET:
            self.current_phase = Phase.DRAW
        elif self.current_phase == Phase.DRAW:
            self.current_phase = Phase.MAIN
        elif self.current_phase == Phase.MAIN:
            self.current_phase = Phase.END
        elif self.current_phase == Phase.END:
            self._end_turn()
    
    def _end_turn(self) -> None:
        """End the current turn and move to the next player."""
        # Move to next player
        self.active_player_index = (self.active_player_index + 1) % len(self.players)
        
        # If we've cycled through all players, increment turn number
        if self.active_player_index == 0:
            self.turn_number += 1
        
        # Start new turn
        self.current_phase = Phase.READY
        self._start_turn()
    
    def _start_turn(self) -> None:
        """Start a new turn for the active player."""
        self.active_player.start_turn()
    
    def execute_phase(self) -> None:
        """Execute the current phase automatically."""
        if self.current_phase == Phase.READY:
            # Ready all characters
            self.active_player.ready_all_characters()
            
        elif self.current_phase == Phase.SET:
            # Check for start-of-turn effects
            # TODO: Implement triggered abilities
            pass
            
        elif self.current_phase == Phase.DRAW:
            # Draw a card (unless should skip)
            if not self.should_skip_draw:
                self.active_player.draw_card()
            
        elif self.current_phase == Phase.MAIN:
            # Main phase - player takes actions
            # This phase doesn't auto-advance
            return
            
        elif self.current_phase == Phase.END:
            # End phase cleanup
            # TODO: Implement end-of-turn effects
            pass
        
        # Auto-advance unless in main phase
        self.advance_phase()
    
    def execute_action(self, action: GameAction, target: Any = None) -> bool:
        """Execute a game action."""
        if action == GameAction.PASS_TURN:
            self.advance_phase()
            return True
            
        elif action == GameAction.PASS_PHASE:
            self.advance_phase()
            return True
            
        elif action == GameAction.PLAY_INK:
            if target and self.active_player.can_play_ink():
                return self.active_player.play_ink(target)
            
        elif action == GameAction.PLAY_CARD:
            if target:
                from ..cards.character_card import CharacterCard
                from ..cards.item_card import ItemCard
                from ..cards.action_card import ActionCard
                
                if isinstance(target, CharacterCard):
                    return self.active_player.play_character(target)
                elif isinstance(target, ItemCard):
                    return self.active_player.play_item(target)
                elif isinstance(target, ActionCard):
                    # TODO: Implement action card playing
                    return False
                    
        elif action == GameAction.QUEST:
            if target:
                lore_gained = self.active_player.quest_with_character(target)
                return lore_gained > 0
                
        elif action == GameAction.CHALLENGE:
            if target and isinstance(target, tuple) and len(target) == 2:
                attacker, defender = target
                return self.active_player.challenge_character(attacker, defender)
        
        return False
    
    def get_game_summary(self) -> dict:
        """Get a summary of the current game state."""
        return {
            "turn": self.turn_number,
            "phase": self.current_phase.value,
            "active_player": self.active_player.name,
            "players": [player.get_game_summary() for player in self.players],
            "locations": len(self.locations),
            "game_over": self.game_over,
            "winner": self.winner.name if self.winner else None,
        }
    
    def __str__(self) -> str:
        """String representation of the game state."""
        return f"Turn {self.turn_number} - {self.current_phase.value.title()} Phase - {self.active_player.name}'s turn"