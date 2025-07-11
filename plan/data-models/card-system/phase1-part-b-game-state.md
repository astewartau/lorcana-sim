# Phase 1 Part B: Game State Foundation

## Overview

**Purpose**: Implement the core game state management system that tracks turn progression, player resources, card zones, and provides the foundation for ability execution and move validation.

**Dependency**: Part A (Card Infrastructure) must be complete. Part B provides the game state foundation required for Part C (Ability System).

**Current Status After Part A**:
- ✅ Card models (Character, Action, Item, Location)
- ✅ Basic ability parsing structure
- ❌ Game state tracking (turns, phases, lore)
- ❌ Player state management (zones, resources)
- ❌ Move validation system
- ❌ Game rule enforcement

## Implementation Plan

### B1: Core Game State Model 🔥 HIGH PRIORITY

Implement the fundamental game state structure that tracks all game elements.

**Files to Create:**
- `src/lorcana_sim/models/game/game_state.py`
- `src/lorcana_sim/models/game/phase.py`
- `src/lorcana_sim/models/game/__init__.py`

**Game State Implementation:**
```python
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum

class Phase(Enum):
    """Lorcana turn phases"""
    READY = "ready"      # Ready step (ready all cards)
    SET = "set"          # Set step (draw card, play ink)
    MAIN = "main"        # Main phase (play cards, quest, challenge)

class GameAction(Enum):
    """Possible player actions"""
    PLAY_INK = "play_ink"
    PLAY_CHARACTER = "play_character"
    PLAY_ACTION = "play_action"
    PLAY_ITEM = "play_item"
    QUEST_CHARACTER = "quest_character"
    CHALLENGE_CHARACTER = "challenge_character"
    SING_SONG = "sing_song"
    ACTIVATE_ABILITY = "activate_ability"
    PASS_TURN = "pass_turn"

@dataclass
class GameState:
    """Tracks the complete state of a Lorcana game"""
    # Players and Turn Management
    players: List['Player']
    current_player_index: int = 0
    turn_number: int = 1
    current_phase: Phase = Phase.READY
    
    # Turn State Tracking
    ink_played_this_turn: bool = False
    actions_this_turn: List[GameAction] = field(default_factory=list)
    
    # Global Game Elements
    locations_in_play: List['LocationCard'] = field(default_factory=list)
    
    # Game Rules State
    first_turn_draw_skipped: bool = False  # Track if first player skipped draw
    
    @property
    def current_player(self) -> 'Player':
        """Get the currently active player"""
        return self.players[self.current_player_index]
    
    @property
    def opponent(self) -> 'Player':
        """Get the opponent (assumes 2-player game)"""
        opponent_index = 1 - self.current_player_index
        return self.players[opponent_index]
    
    def is_game_over(self) -> Tuple[bool, Optional['Player']]:
        """Check if game is over and return winner if any"""
        for player in self.players:
            if player.lore >= 20:
                return True, player
        return False, None
    
    def advance_phase(self) -> None:
        """Advance to the next phase"""
        if self.current_phase == Phase.READY:
            self.current_phase = Phase.SET
        elif self.current_phase == Phase.SET:
            self.current_phase = Phase.MAIN
        elif self.current_phase == Phase.MAIN:
            # End turn, move to next player
            self.end_turn()
    
    def end_turn(self) -> None:
        """End current player's turn and start next player's turn"""
        # Reset turn state
        self.ink_played_this_turn = False
        self.actions_this_turn.clear()
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # If back to first player, increment turn number
        if self.current_player_index == 0:
            self.turn_number += 1
        
        # Start ready phase for new player
        self.current_phase = Phase.READY
        self.ready_step()
    
    def ready_step(self) -> None:
        """Execute the ready step (ready all cards)"""
        current_player = self.current_player
        
        # Ready all characters
        for character in current_player.characters_in_play:
            character.ready()
        
        # Ready all items
        for item in current_player.items_in_play:
            if hasattr(item, 'exerted'):
                item.exerted = False
    
    def set_step(self) -> None:
        """Execute the set step (draw card, play ink)"""
        current_player = self.current_player
        
        # Draw card (skip on first turn for first player)
        should_draw = not (self.turn_number == 1 and 
                          self.current_player_index == 0 and 
                          not self.first_turn_draw_skipped)
        
        if should_draw:
            current_player.draw_card()
        elif self.turn_number == 1 and self.current_player_index == 0:
            self.first_turn_draw_skipped = True
    
    def can_play_ink(self) -> bool:
        """Check if current player can play ink"""
        return not self.ink_played_this_turn and self.current_phase == Phase.SET
    
    def can_perform_action(self, action: GameAction) -> bool:
        """Check if current player can perform the given action"""
        if self.current_phase == Phase.MAIN:
            return action in [
                GameAction.PLAY_CHARACTER,
                GameAction.PLAY_ACTION, 
                GameAction.PLAY_ITEM,
                GameAction.QUEST_CHARACTER,
                GameAction.CHALLENGE_CHARACTER,
                GameAction.SING_SONG,
                GameAction.ACTIVATE_ABILITY,
                GameAction.PASS_TURN
            ]
        elif self.current_phase == Phase.SET:
            return action in [GameAction.PLAY_INK, GameAction.PASS_TURN]
        elif self.current_phase == Phase.READY:
            return action == GameAction.PASS_TURN
        
        return False
```

### B2: Enhanced Player Model 🔥 HIGH PRIORITY

Expand the Player model to properly track all game zones and provide game state queries.

**Files to Enhance:**
- `src/lorcana_sim/models/game/player.py`

**Enhanced Player Implementation:**
```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from collections import Counter
from ..cards.base_card import Card, CardColor
from ..cards.character_card import CharacterCard
from ..cards.action_card import ActionCard
from ..cards.item_card import ItemCard

@dataclass
class Player:
    """Represents a player in a Lorcana game with complete state tracking"""
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
    
    # Turn State
    ink_used_this_turn: int = 0
    
    @property
    def total_ink(self) -> int:
        """Total ink available (size of inkwell)"""
        return len(self.inkwell)
    
    @property
    def available_ink(self) -> int:
        """Ink available to spend this turn"""
        return self.total_ink - self.ink_used_this_turn
    
    @property
    def ink_by_color(self) -> Dict[CardColor, int]:
        """Available ink by color"""
        ink_colors = Counter()
        for card in self.inkwell:
            ink_colors[card.color] += 1
        return dict(ink_colors)
    
    @property
    def hand_size(self) -> int:
        """Number of cards in hand"""
        return len(self.hand)
    
    @property
    def deck_size(self) -> int:
        """Number of cards remaining in deck"""
        return len(self.deck)
    
    def can_afford(self, card: Card) -> bool:
        """Check if player can afford to play a card"""
        return self.available_ink >= card.cost
    
    def can_afford_with_colors(self, card: Card, required_colors: Dict[CardColor, int] = None) -> bool:
        """Check if player can afford card with color requirements"""
        if not self.can_afford(card):
            return False
        
        if required_colors:
            available_colors = self.ink_by_color
            for color, required_amount in required_colors.items():
                if available_colors.get(color, 0) < required_amount:
                    return False
        
        return True
    
    def draw_card(self) -> Optional[Card]:
        """Draw a card from deck to hand"""
        if self.deck:
            card = self.deck.pop(0)
            self.hand.append(card)
            return card
        return None
    
    def draw_cards(self, count: int) -> List[Card]:
        """Draw multiple cards from deck"""
        drawn = []
        for _ in range(count):
            card = self.draw_card()
            if card:
                drawn.append(card)
            else:
                break
        return drawn
    
    def play_ink(self, card: Card) -> bool:
        """Play a card as ink"""
        if not card.can_be_inked() or card not in self.hand:
            return False
        
        self.hand.remove(card)
        self.inkwell.append(card)
        return True
    
    def play_character(self, character: CharacterCard, ink_cost: int) -> bool:
        """Play a character card"""
        if character not in self.hand or not self.can_afford(character):
            return False
        
        self.hand.remove(character)
        self.characters_in_play.append(character)
        self.spend_ink(ink_cost)
        return True
    
    def play_action(self, action: ActionCard, ink_cost: int) -> bool:
        """Play an action card"""
        if action not in self.hand or not self.can_afford(action):
            return False
        
        self.hand.remove(action)
        self.discard_pile.append(action)
        self.spend_ink(ink_cost)
        return True
    
    def play_item(self, item: ItemCard, ink_cost: int) -> bool:
        """Play an item card"""
        if item not in self.hand or not self.can_afford(item):
            return False
        
        self.hand.remove(item)
        self.items_in_play.append(item)
        self.spend_ink(ink_cost)
        return True
    
    def spend_ink(self, amount: int) -> bool:
        """Spend ink for playing cards/abilities"""
        if self.available_ink >= amount:
            self.ink_used_this_turn += amount
            return True
        return False
    
    def reset_turn_state(self) -> None:
        """Reset state at start of turn"""
        self.ink_used_this_turn = 0
    
    def gain_lore(self, amount: int) -> None:
        """Gain lore points"""
        self.lore += amount
    
    def get_ready_characters(self) -> List[CharacterCard]:
        """Get all ready (unexerted) characters"""
        return [char for char in self.characters_in_play if not char.exerted]
    
    def get_characters_with_ability(self, ability_keyword: str) -> List[CharacterCard]:
        """Get characters with specific keyword ability"""
        result = []
        for character in self.characters_in_play:
            for ability in character.abilities:
                if hasattr(ability, 'keyword') and ability.keyword == ability_keyword:
                    result.append(character)
                    break
        return result
    
    def has_singer_for_cost(self, required_cost: int) -> List[CharacterCard]:
        """Get singers that can sing songs of given cost"""
        singers = []
        for character in self.get_ready_characters():
            for ability in character.abilities:
                if (hasattr(ability, 'keyword') and 
                    ability.keyword == 'Singer' and
                    ability.get_effective_sing_cost() >= required_cost):
                    singers.append(character)
                    break
        return singers
```

### B3: Move Validation System 🔥 HIGH PRIORITY

Create a comprehensive system for validating possible moves and game actions.

**Files to Create:**
- `src/lorcana_sim/engine/move_validator.py`
- `src/lorcana_sim/engine/__init__.py`

**Move Validation Implementation:**
```python
from typing import List, Tuple, Optional, Dict, Any
from ..models.game.game_state import GameState, GameAction, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card

class MoveValidator:
    """Validates possible moves and game actions"""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
    
    def get_all_legal_actions(self) -> List[Tuple[GameAction, Dict[str, Any]]]:
        """Get all legal actions for current player in current phase"""
        legal_actions = []
        current_player = self.game_state.current_player
        phase = self.game_state.current_phase
        
        if phase == Phase.READY:
            legal_actions.append((GameAction.PASS_TURN, {}))
        
        elif phase == Phase.SET:
            # Play ink (once per turn)
            if self.game_state.can_play_ink():
                ink_cards = self.get_playable_ink_cards()
                for card in ink_cards:
                    legal_actions.append((GameAction.PLAY_INK, {'card': card}))
            
            legal_actions.append((GameAction.PASS_TURN, {}))
        
        elif phase == Phase.MAIN:
            # Play characters
            characters = self.get_playable_characters()
            for character in characters:
                legal_actions.append((GameAction.PLAY_CHARACTER, {'card': character}))
            
            # Play actions
            actions = self.get_playable_actions()
            for action in actions:
                legal_actions.append((GameAction.PLAY_ACTION, {'card': action}))
            
            # Play items
            items = self.get_playable_items()
            for item in items:
                legal_actions.append((GameAction.PLAY_ITEM, {'card': item}))
            
            # Quest with characters
            questing = self.get_characters_that_can_quest()
            for character in questing:
                legal_actions.append((GameAction.QUEST_CHARACTER, {'character': character}))
            
            # Challenge with characters
            challenges = self.get_possible_challenges()
            for attacker, defender in challenges:
                legal_actions.append((GameAction.CHALLENGE_CHARACTER, {
                    'attacker': attacker, 
                    'defender': defender
                }))
            
            # Sing songs
            songs = self.get_singable_songs()
            for song, singer in songs:
                legal_actions.append((GameAction.SING_SONG, {
                    'song': song,
                    'singer': singer
                }))
            
            legal_actions.append((GameAction.PASS_TURN, {}))
        
        return legal_actions
    
    def get_playable_ink_cards(self) -> List[Card]:
        """Get cards that can be played as ink"""
        current_player = self.game_state.current_player
        return [card for card in current_player.hand if card.can_be_inked()]
    
    def get_playable_characters(self) -> List[CharacterCard]:
        """Get character cards that can be played"""
        current_player = self.game_state.current_player
        playable = []
        
        for card in current_player.hand:
            if isinstance(card, CharacterCard) and current_player.can_afford(card):
                playable.append(card)
        
        return playable
    
    def get_playable_actions(self) -> List[ActionCard]:
        """Get action cards that can be played"""
        current_player = self.game_state.current_player
        playable = []
        
        for card in current_player.hand:
            if isinstance(card, ActionCard) and current_player.can_afford(card):
                playable.append(card)
        
        return playable
    
    def get_playable_items(self) -> List[ItemCard]:
        """Get item cards that can be played"""
        current_player = self.game_state.current_player
        playable = []
        
        for card in current_player.hand:
            if isinstance(card, ItemCard) and current_player.can_afford(card):
                playable.append(card)
        
        return playable
    
    def get_characters_that_can_quest(self) -> List[CharacterCard]:
        """Get characters that can quest this turn"""
        current_player = self.game_state.current_player
        return [char for char in current_player.characters_in_play if char.can_quest()]
    
    def get_possible_challenges(self) -> List[Tuple[CharacterCard, CharacterCard]]:
        """Get all possible (attacker, defender) challenge pairs"""
        current_player = self.game_state.current_player
        opponent = self.game_state.opponent
        
        challenges = []
        ready_attackers = current_player.get_ready_characters()
        possible_defenders = opponent.characters_in_play
        
        for attacker in ready_attackers:
            for defender in possible_defenders:
                if self.can_challenge(attacker, defender):
                    challenges.append((attacker, defender))
        
        return challenges
    
    def can_challenge(self, attacker: CharacterCard, defender: CharacterCard) -> bool:
        """Check if attacker can challenge defender"""
        # Basic challenge rules
        if attacker.exerted or not attacker.is_alive:
            return False
        
        if not defender.is_alive:
            return False
        
        # Check Evasive ability
        defender_has_evasive = any(
            hasattr(ability, 'keyword') and ability.keyword == 'Evasive'
            for ability in defender.abilities
        )
        
        if defender_has_evasive:
            attacker_has_evasive = any(
                hasattr(ability, 'keyword') and ability.keyword == 'Evasive'
                for ability in attacker.abilities
            )
            if not attacker_has_evasive:
                return False
        
        # Check Bodyguard rules
        opponent = self.game_state.opponent
        bodyguard_characters = opponent.get_characters_with_ability('Bodyguard')
        
        if bodyguard_characters and defender not in bodyguard_characters:
            # Must challenge bodyguard first
            return False
        
        return True
    
    def get_singable_songs(self) -> List[Tuple[ActionCard, CharacterCard]]:
        """Get (song, singer) pairs for songs that can be sung"""
        current_player = self.game_state.current_player
        singable = []
        
        for card in current_player.hand:
            if isinstance(card, ActionCard) and card.is_song:
                required_cost = card.singer_cost_reduction
                if required_cost is not None:
                    singers = current_player.has_singer_for_cost(required_cost)
                    for singer in singers:
                        singable.append((card, singer))
        
        return singable
    
    def validate_action(self, action: GameAction, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if a specific action with parameters is legal"""
        legal_actions = self.get_all_legal_actions()
        
        for legal_action, legal_params in legal_actions:
            if action == legal_action:
                # Check if parameters match
                if self._parameters_match(parameters, legal_params):
                    return True, "Action is legal"
        
        return False, f"Action {action} with parameters {parameters} is not legal"
    
    def _parameters_match(self, given: Dict[str, Any], legal: Dict[str, Any]) -> bool:
        """Check if given parameters match legal parameters"""
        for key, value in given.items():
            if key not in legal or legal[key] != value:
                return False
        return True
```

### B4: Game Rules Engine 🔥 HIGH PRIORITY

Implement core game rules and state transitions.

**Files to Create:**
- `src/lorcana_sim/engine/game_engine.py`

**Game Engine Implementation:**
```python
from typing import Dict, Any, Tuple, Optional
from ..models.game.game_state import GameState, GameAction, Phase
from ..models.cards.character_card import CharacterCard
from ..models.cards.action_card import ActionCard
from ..models.cards.item_card import ItemCard
from ..models.cards.base_card import Card
from .move_validator import MoveValidator

class GameEngine:
    """Executes game actions and manages state transitions"""
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.validator = MoveValidator(game_state)
    
    def execute_action(self, action: GameAction, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a game action and update state"""
        # Validate action first
        is_valid, message = self.validator.validate_action(action, parameters)
        if not is_valid:
            return False, message
        
        # Execute the action
        try:
            if action == GameAction.PLAY_INK:
                return self._execute_play_ink(parameters['card'])
            elif action == GameAction.PLAY_CHARACTER:
                return self._execute_play_character(parameters['card'])
            elif action == GameAction.PLAY_ACTION:
                return self._execute_play_action(parameters['card'])
            elif action == GameAction.PLAY_ITEM:
                return self._execute_play_item(parameters['card'])
            elif action == GameAction.QUEST_CHARACTER:
                return self._execute_quest_character(parameters['character'])
            elif action == GameAction.CHALLENGE_CHARACTER:
                return self._execute_challenge(parameters['attacker'], parameters['defender'])
            elif action == GameAction.SING_SONG:
                return self._execute_sing_song(parameters['song'], parameters['singer'])
            elif action == GameAction.PASS_TURN:
                return self._execute_pass_turn()
            else:
                return False, f"Unknown action: {action}"
        
        except Exception as e:
            return False, f"Error executing action: {str(e)}"
    
    def _execute_play_ink(self, card: Card) -> Tuple[bool, str]:
        """Execute playing a card as ink"""
        current_player = self.game_state.current_player
        
        if current_player.play_ink(card):
            self.game_state.ink_played_this_turn = True
            self.game_state.actions_this_turn.append(GameAction.PLAY_INK)
            return True, f"Played {card.name} as ink"
        
        return False, "Failed to play ink"
    
    def _execute_play_character(self, character: CharacterCard) -> Tuple[bool, str]:
        """Execute playing a character card"""
        current_player = self.game_state.current_player
        
        if current_player.play_character(character, character.cost):
            self.game_state.actions_this_turn.append(GameAction.PLAY_CHARACTER)
            return True, f"Played character {character.name}"
        
        return False, "Failed to play character"
    
    def _execute_play_action(self, action: ActionCard) -> Tuple[bool, str]:
        """Execute playing an action card"""
        current_player = self.game_state.current_player
        
        if current_player.play_action(action, action.cost):
            self.game_state.actions_this_turn.append(GameAction.PLAY_ACTION)
            # TODO: Execute action's effects
            return True, f"Played action {action.name}"
        
        return False, "Failed to play action"
    
    def _execute_play_item(self, item: ItemCard) -> Tuple[bool, str]:
        """Execute playing an item card"""
        current_player = self.game_state.current_player
        
        if current_player.play_item(item, item.cost):
            self.game_state.actions_this_turn.append(GameAction.PLAY_ITEM)
            return True, f"Played item {item.name}"
        
        return False, "Failed to play item"
    
    def _execute_quest_character(self, character: CharacterCard) -> Tuple[bool, str]:
        """Execute questing with a character"""
        if character.can_quest():
            character.exert()
            current_player = self.game_state.current_player
            current_player.gain_lore(character.current_lore)
            self.game_state.actions_this_turn.append(GameAction.QUEST_CHARACTER)
            return True, f"{character.name} quested for {character.current_lore} lore"
        
        return False, "Character cannot quest"
    
    def _execute_challenge(self, attacker: CharacterCard, defender: CharacterCard) -> Tuple[bool, str]:
        """Execute a challenge between characters"""
        if not self.validator.can_challenge(attacker, defender):
            return False, "Invalid challenge"
        
        # Exert attacker
        attacker.exert()
        
        # Deal damage
        attacker.deal_damage(defender.current_strength)
        defender.deal_damage(attacker.current_strength)
        
        # Remove destroyed characters
        current_player = self.game_state.current_player
        opponent = self.game_state.opponent
        
        if not attacker.is_alive:
            current_player.characters_in_play.remove(attacker)
            current_player.discard_pile.append(attacker)
        
        if not defender.is_alive:
            opponent.characters_in_play.remove(defender)
            opponent.discard_pile.append(defender)
        
        self.game_state.actions_this_turn.append(GameAction.CHALLENGE_CHARACTER)
        return True, f"{attacker.name} challenged {defender.name}"
    
    def _execute_sing_song(self, song: ActionCard, singer: CharacterCard) -> Tuple[bool, str]:
        """Execute singing a song"""
        current_player = self.game_state.current_player
        
        # Remove song from hand, add to discard
        if song in current_player.hand:
            current_player.hand.remove(song)
            current_player.discard_pile.append(song)
            
            # Exert the singer
            singer.exert()
            
            self.game_state.actions_this_turn.append(GameAction.SING_SONG)
            # TODO: Execute song's effects
            return True, f"{singer.name} sang {song.name}"
        
        return False, "Failed to sing song"
    
    def _execute_pass_turn(self) -> Tuple[bool, str]:
        """Execute passing the turn"""
        if self.game_state.current_phase == Phase.MAIN:
            self.game_state.advance_phase()
            return True, "Turn ended"
        else:
            self.game_state.advance_phase()
            return True, f"Advanced to {self.game_state.current_phase.value} phase"
```

## Implementation Priority

### Phase 1 (Immediate - Required for Part C):
1. **B1: Core Game State Model** - Foundation for everything
2. **B2: Enhanced Player Model** - Resource and zone tracking
3. **B3: Move Validation System** - Legal action determination
4. **B4: Game Rules Engine** - Action execution

### Phase 2 (Next - After basic abilities work):
5. Enhanced challenge rules with all keyword interactions
6. Location mechanics integration
7. Advanced timing and priority systems
8. Game initialization and deck loading

## Success Criteria

After Part B completion:
- ✅ Complete game state tracking (turns, phases, lore, zones)
- ✅ All basic player actions work (play cards, quest, challenge)
- ✅ Move validation correctly identifies legal actions
- ✅ Game rules properly enforced (ink costs, exertion, damage)
- ✅ Foundation exists for ability execution in Part C
- ✅ Turn progression and win conditions function

This provides the essential game state foundation that Part C (abilities) requires to implement meaningful ability effects and interactions.