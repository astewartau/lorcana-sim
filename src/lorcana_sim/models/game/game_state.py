"""Game state model for Lorcana simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Any, Dict

from .player import Player
from ..cards.location_card import LocationCard


class Phase(Enum):
    """Lorcana turn phases."""
    READY = "ready"      # Ready step (ready all exerted cards)
    SET = "set"          # Set step (resolve start-of-turn effects)
    DRAW = "draw"        # Draw step (draw a card)
    PLAY = "play"        # Play phase (ink, play cards, quest, challenge)


class GameAction(Enum):
    """Possible player actions."""
    PLAY_INK = "play_ink"
    PLAY_CHARACTER = "play_character"
    PLAY_ACTION = "play_action"
    PLAY_ITEM = "play_item"
    QUEST_CHARACTER = "quest_character"
    CHALLENGE_CHARACTER = "challenge_character"
    SING_SONG = "sing_song"
    ACTIVATE_ABILITY = "activate_ability"
    PROGRESS = "progress"       # Progress to next phase
    PASS_TURN = "pass_turn"      # Pass turn to opponent


class GameResult(Enum):
    """Possible game results."""
    ONGOING = "ongoing"
    LORE_VICTORY = "lore_victory"
    DECK_EXHAUSTION = "deck_exhaustion"  # Opponent runs out of cards
    STALEMATE = "stalemate"  # Both players unable to make progress


@dataclass
class GameState:
    """Tracks the complete state of a Lorcana game."""
    # Players and Turn Management
    players: List[Player]
    current_player_index: int = 0
    turn_number: int = 1
    current_phase: Phase = Phase.READY
    
    # Turn State Tracking
    ink_played_this_turn: bool = False
    actions_this_turn: List[GameAction] = field(default_factory=list)
    characters_acted_this_turn: List[int] = field(default_factory=list)  # Track character IDs that have acted
    
    # Global Game Elements
    locations_in_play: List[LocationCard] = field(default_factory=list)
    
    # Game Rules State
    first_turn_draw_skipped: bool = False  # Track if first player skipped draw
    
    # Game over state
    game_result: GameResult = GameResult.ONGOING
    winner: Optional[Player] = None
    game_over_data: Dict[str, Any] = field(default_factory=dict)
    
    # Stalemate detection
    consecutive_passes: int = 0  # Track consecutive pass actions
    max_consecutive_passes: int = 4  # Both players pass twice = stalemate
    
    # Last event tracking for inspection
    last_event: Optional[Dict[str, Any]] = None  # The most recent event that occurred
    
    # Zone management for conditional effects
    _zone_manager: Optional[Any] = None  # ZoneManager instance (lazy loaded)
    
    # Cost modification management
    _cost_modification_manager: Optional[Any] = None  # CostModificationManager instance (lazy loaded)
    
    def __post_init__(self) -> None:
        """Validate game state after creation."""
        if len(self.players) < 2:
            raise ValueError("Game must have at least 2 players")
        if self.current_player_index >= len(self.players):
            raise ValueError("Current player index out of range")
    
    @property
    def current_player(self) -> Player:
        """Get the currently active player."""
        return self.players[self.current_player_index]
    
    @property
    def opponent(self) -> Player:
        """Get the opponent (assumes 2-player game)."""
        opponent_index = 1 - self.current_player_index
        return self.players[opponent_index]
    
    def check_game_state(self) -> None:
        """Check and update game state for win/loss/draw conditions."""
        from ...engine.event_system import GameEvent
        
        if self.game_result != GameResult.ONGOING:
            return  # Game already over
        
        # Check lore victory (20 lore wins)
        for player in self.players:
            if player.lore >= 20:
                self.game_result = GameResult.LORE_VICTORY
                self.winner = player
                self.game_over_data = {
                    'event': GameEvent.GAME_ENDS,
                    'context': {
                        'result': 'lore_victory',
                        'winner_name': player.name,
                        'lore': player.lore
                    }
                }
                return
        
        # Check deck exhaustion (only after game has actually started)
        # Only check after turn 1 to avoid triggering on initialization
        if self.turn_number > 1:
            for player in self.players:
                if not player.deck and not player.hand:
                    # This player has no cards left
                    opponent = self.get_opponent(player)
                    self.game_result = GameResult.DECK_EXHAUSTION
                    self.winner = opponent
                    self.game_over_data = {
                        'event': GameEvent.GAME_ENDS,
                        'context': {
                            'result': 'deck_exhaustion',
                            'winner_name': opponent.name,
                            'loser_name': player.name
                        }
                    }
                    return
        
        # Check for stalemate (too many consecutive passes)
        if self.consecutive_passes >= self.max_consecutive_passes:
            self.game_result = GameResult.STALEMATE
            self.winner = None
            self.game_over_data = {
                'event': GameEvent.GAME_ENDS,
                'context': {
                    'result': 'stalemate',
                    'consecutive_passes': self.consecutive_passes
                }
            }
            return
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        self.check_game_state()
        return self.game_result != GameResult.ONGOING
    
    def get_game_result(self) -> Tuple[GameResult, Optional[Player], Dict[str, Any]]:
        """Get the current game result."""
        self.check_game_state()
        return self.game_result, self.winner, self.game_over_data
    
    def get_opponent(self, player: Player) -> Player:
        """Get the opponent of the given player (assumes 2-player game)."""
        for p in self.players:
            if p != player:
                return p
        raise ValueError("Opponent not found")
    
    def advance_phase(self) -> None:
        """Advance to the next phase."""
        if self.current_phase.value == 'ready':
            self.current_phase = Phase.SET
        elif self.current_phase.value == 'set':
            self.current_phase = Phase.DRAW
        elif self.current_phase.value == 'draw':
            self.current_phase = Phase.PLAY
        elif self.current_phase.value == 'play':
            # End turn, move to next player
            self.end_turn()
    
    def end_turn(self) -> None:
        """End current player's turn and start next player's turn."""
        # Reset turn state
        self.ink_played_this_turn = False
        self.actions_this_turn.clear()
        self.characters_acted_this_turn.clear()
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # If back to first player, increment turn number
        if self.current_player_index == 0:
            self.turn_number += 1
        
        # Update character dry status after turn changes (but not for current player - they'll update in ready phase)
        self._update_character_dry_status_except_current()
        
        # Start ready phase for new player (but don't execute ready_step yet)
        self.current_phase = Phase.READY
    
    def ready_step(self) -> List[Dict[str, Any]]:
        """Execute the ready step (ready all cards and start turn).
        
        Returns:
            List of event data for items that were readied.
        """
        from ...engine.event_system import GameEvent
        
        current_player = self.current_player
        readied_items = []
        
        # Get list of exerted characters before readying
        exerted_characters = [char for char in current_player.characters_in_play if char.exerted]
        
        # Update dry status for current player's characters (happens during ready phase)
        for char in current_player.characters_in_play:
            if char.turn_played is not None:
                # Ink dries at start of owner's next turn
                old_dry_status = char.is_dry
                char.is_dry = self.turn_number > char.turn_played
                # Track characters that just dried
                if not old_dry_status and char.is_dry and not char.exerted:
                    readied_items.append({
                        'event': GameEvent.CHARACTER_READIED,
                        'context': {
                            'character_name': char.name,
                            'reason': 'ink_dried'
                        }
                    })
            else:
                # Character wasn't played this game (already dry)
                char.is_dry = True
        
        # Start the turn (reset ink usage, ready characters)
        current_player.start_turn()
        
        # Track which characters were readied from exerted state
        for char in exerted_characters:
            readied_items.append({
                'event': GameEvent.CHARACTER_READIED,
                'context': {
                    'character_name': char.name,
                    'reason': 'ready_step'
                }
            })
        
        # Ready all items
        exerted_items = [item for item in current_player.items_in_play 
                        if hasattr(item, 'exerted') and item.exerted]
        for item in exerted_items:
            item.exerted = False
            readied_items.append({
                'event': GameEvent.CHARACTER_READIED,  # Using CHARACTER_READIED for items too
                'context': {
                    'item_name': item.name,
                    'item_type': 'item',
                    'reason': 'ready_step'
                }
            })
        
        return readied_items
    
    def set_last_event(self, event_type: str, **event_data) -> None:
        """Set the last event that occurred for inspection."""
        self.last_event = {
            'type': event_type,
            'turn': self.turn_number,
            'phase': self.current_phase.value,
            'timestamp': len(self.actions_this_turn),  # Simple event ordering
            **event_data
        }
    
    def get_last_event(self) -> Optional[Dict[str, Any]]:
        """Get the last event that occurred."""
        return self.last_event
    
    def clear_last_event(self) -> None:
        """Clear the last event."""
        self.last_event = None
    
    def set_step(self) -> None:
        """Execute the set step (resolve start-of-turn effects)."""
        # Handle any start-of-turn triggered abilities
        # TODO: Implement start-of-turn ability resolution here
        pass
    
    def draw_step(self) -> List[Dict[str, Any]]:
        """Execute the draw step (draw a card).
        
        Returns:
            List of event data for draw events that occurred.
        """
        from ...engine.event_system import GameEvent
        
        current_player = self.current_player
        draw_events = []
        
        # Draw card (skip on first turn for first player)
        should_draw = not (self.turn_number == 1 and 
                          self.current_player_index == 0 and 
                          not self.first_turn_draw_skipped)
        
        if should_draw:
            drawn_card = current_player.draw_card()
            if drawn_card:
                draw_events.append({
                    'event': GameEvent.CARD_DRAWN,
                    'context': {
                        'player_name': current_player.name,
                        'card_name': drawn_card.name
                    }
                })
            else:
                draw_events.append({
                    'event': GameEvent.CARD_DRAWN,
                    'context': {
                        'player_name': current_player.name,
                        'draw_failed': True,
                        'reason': 'empty_deck'
                    }
                })
        elif self.turn_number == 1 and self.current_player_index == 0:
            self.first_turn_draw_skipped = True
            draw_events.append({
                'event': GameEvent.DRAW_STEP,
                'context': {
                    'player_name': current_player.name,
                    'action': 'skipped',
                    'reason': 'first_turn'
                }
            })
        
        return draw_events
    
    # Zone Management Methods
    @property
    def zone_manager(self):
        """Get or create the zone manager instance."""
        if self._zone_manager is None:
            from ..abilities.composable.zone_manager import ZoneManager
            self._zone_manager = ZoneManager()
        return self._zone_manager
    
    def register_card_conditional_effects(self, card) -> None:
        """Register all conditional effects from a card with the zone manager."""
        if hasattr(card, 'conditional_effects'):
            for effect in card.conditional_effects:
                self.zone_manager.register_conditional_effect(effect)
    
    def unregister_card_conditional_effects(self, card) -> None:
        """Unregister all conditional effects from a card."""
        if hasattr(card, 'conditional_effects'):
            for effect in card.conditional_effects:
                self.zone_manager.unregister_conditional_effect(effect)
    
    def notify_card_zone_change(self, card, from_zone_name: Optional[str], to_zone_name: Optional[str]) -> List[Dict]:
        """Notify zone manager of card movement and return any events generated."""
        if not hasattr(card, 'conditional_effects') or not card.conditional_effects:
            return []
        
        # Convert zone names to ActivationZone enums
        from ..abilities.composable.conditional_effects import ActivationZone
        
        zone_map = {
            'hand': ActivationZone.HAND,
            'play': ActivationZone.PLAY,
            'discard': ActivationZone.DISCARD,
            'deck': ActivationZone.DECK,
            'ink_well': ActivationZone.INK_WELL
        }
        
        from_zone = zone_map.get(from_zone_name) if from_zone_name else None
        to_zone = zone_map.get(to_zone_name) if to_zone_name else None
        
        return self.zone_manager.handle_zone_transition(card, from_zone, to_zone, self)
    
    def evaluate_conditional_effects(self) -> List[Dict]:
        """Evaluate all conditional effects and return any events generated."""
        return self.zone_manager.evaluate_all_effects(self)
    
    # Cost Modification Methods
    @property
    def cost_modification_manager(self):
        """Get or create the cost modification manager instance."""
        if self._cost_modification_manager is None:
            from ..abilities.composable.cost_modification import CostModificationManager
            self._cost_modification_manager = CostModificationManager()
        return self._cost_modification_manager
    
    def get_modified_card_cost(self, card) -> int:
        """Get the modified cost for a card after all applicable cost modifiers."""
        return self.cost_modification_manager.get_modified_cost(card, self)
    
    def register_cost_modifier(self, modifier) -> None:
        """Register a cost modifier with the game state."""
        self.cost_modification_manager.register_cost_modifier(modifier)
    
    def unregister_cost_modifier(self, modifier) -> None:
        """Unregister a cost modifier from the game state."""
        self.cost_modification_manager.unregister_cost_modifier(modifier)
    
    def can_play_ink(self) -> bool:
        """Check if current player can play ink."""
        return not self.ink_played_this_turn and self.current_phase.value == 'play'
    
    def has_character_acted_this_turn(self, character_id: int) -> bool:
        """Check if a character has already acted this turn."""
        return character_id in self.characters_acted_this_turn
    
    def mark_character_acted(self, character_id: int) -> None:
        """Mark that a character has acted this turn."""
        if character_id not in self.characters_acted_this_turn:
            self.characters_acted_this_turn.append(character_id)
    
    def can_perform_action(self, action: GameAction) -> bool:
        """Check if current player can perform the given action."""
        # Game over - no actions allowed
        if self.is_game_over():
            return False
        
        # Use value comparison to avoid enum identity issues
        if self.current_phase.value == 'play':
            return action in [
                GameAction.PLAY_INK,
                GameAction.PLAY_CHARACTER,
                GameAction.PLAY_ACTION, 
                GameAction.PLAY_ITEM,
                GameAction.QUEST_CHARACTER,
                GameAction.CHALLENGE_CHARACTER,
                GameAction.SING_SONG,
                GameAction.ACTIVATE_ABILITY,
                GameAction.PROGRESS,
                GameAction.PASS_TURN
            ]
        elif self.current_phase.value in ['ready', 'set', 'draw']:
            return action in [GameAction.PROGRESS, GameAction.PASS_TURN]
        
        return False
    
    def record_action(self, action: GameAction) -> None:
        """Record an action for stalemate detection."""
        if action == GameAction.PASS_TURN:
            self.consecutive_passes += 1
        else:
            # Reset pass counter on any meaningful action
            self.consecutive_passes = 0
    
    def _update_character_dry_status(self) -> None:
        """Update dry status for all characters based on current turn."""
        for player in self.players:
            for char in player.characters_in_play:
                if char.turn_played is not None:
                    # Ink dries at start of owner's next turn
                    char.is_dry = self.turn_number > char.turn_played
                else:
                    # Character wasn't played this game (already dry)
                    char.is_dry = True
    
    def _update_character_dry_status_except_current(self) -> None:
        """Update dry status for all characters except current player (they update during ready phase)."""
        current_player = self.current_player
        for player in self.players:
            if player != current_player:
                for char in player.characters_in_play:
                    if char.turn_played is not None:
                        # Ink dries at start of owner's next turn, not just any turn
                        # Only update if this character belongs to a player whose turn just started
                        # Since this is called during end_turn, we should NOT update dry status here
                        # Dry status updates only happen during the character owner's ready phase
                        pass
                    else:
                        # Character wasn't played this game (already dry)
                        char.is_dry = True
    
    def __str__(self) -> str:
        """String representation of the game state."""
        return f"Turn {self.turn_number} - {self.current_phase.value.title()} Phase - {self.current_player.name}'s turn"