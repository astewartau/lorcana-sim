# Phase 1: Core Data Models - Implementation Plan

## Overview

This document provides a detailed implementation plan for Phase 1 of the Lorcana simulation project: creating the fundamental data structures that represent game elements. This phase translates the data model designs into working code that will serve as the foundation for all game simulation logic.

**Important Note**: This plan is designed to be flexible and will evolve as we interact with the data and deepen our understanding of the Lorcana game system. Initial implementations should prioritize getting the basic structure working, with refinements coming through iterative development.

## Current Status

- ✅ **Data Parsing**: Lorcana-JSON and Dreamborn parsers implemented for analysis
- ❌ **Object Models**: Core game objects not yet implemented
- ❌ **Game State**: No game simulation objects exist yet

The existing parsers serve as excellent research tools but don't create the objects needed for game simulation.

## Phase 1 Objectives

Create the core object model that represents:
1. **Cards** - All card types with their properties and abilities
2. **Decks** - Collections of cards with game rules
3. **Players** - Game participants with their resources and zones
4. **Game State** - The current state of an active game

## Implementation Structure

### Part A: Basic Card Infrastructure

#### A1: Base Card Classes
Create the fundamental card class hierarchy that all cards inherit from.

**Files to Create:**
- `src/models/cards/base_card.py`
- `src/models/cards/__init__.py`

**Key Classes:**
```python
@dataclass
class Card:
    """Base class for all Lorcana cards"""
    # Core Identity
    id: int                    # From lorcana-json "id" field
    name: str                  # From "name" field
    version: Optional[str]     # From "version" field (may be None)
    full_name: str             # From "fullName" field
    
    # Game Properties
    cost: int                  # From "cost" field
    color: CardColor           # From "color" field (enum)
    inkwell: bool              # From "inkwell" field
    
    # Metadata
    rarity: Rarity             # From "rarity" field (enum)
    set_code: str              # From "setCode" field
    number: int                # From "number" field
    story: str                 # From "story" field
    
    # Abilities & Text
    abilities: List[Ability] = field(default_factory=list)   # Parsed from "abilities" array
    flavor_text: Optional[str] = None # From "flavorText" field
    full_text: str = ""        # From "fullText" field
    
    # Visual (optional for simulation)
    artists: List[str] = field(default_factory=list)         # From "artists" array
    
    def __post_init__(self) -> None:
        """Validate card data after creation"""
        if self.cost < 0:
            raise ValueError(f"Card cost cannot be negative: {self.cost}")
        if not self.name:
            raise ValueError("Card name cannot be empty")
        if not self.full_name:
            self.full_name = f"{self.name} - {self.version}" if self.version else self.name
    
    @property
    def card_type(self) -> str:
        """Get the card type (implemented by subclasses)"""
        class_name = self.__class__.__name__
        if class_name == "Card":
            return "Card"
        return class_name.replace("Card", "")
    
    def can_be_inked(self) -> bool:
        """Check if this card can be played as ink"""
        return self.inkwell
```

**Key Enums:**
```python
class CardColor(Enum):
    AMBER = "Amber"
    AMETHYST = "Amethyst" 
    EMERALD = "Emerald"
    RUBY = "Ruby"
    SAPPHIRE = "Sapphire"
    STEEL = "Steel"
    # Handle multi-color cards like "Amber-Steel"

class Rarity(Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    SUPER_RARE = "Super Rare"
    LEGENDARY = "Legendary"
    SPECIAL = "Special"       # Found in data
    ENCHANTED = "Enchanted"   # Found in data
```

#### A2: Specialized Card Types
Implement the four main card types with their unique properties.

**Files to Create:**
- `src/models/cards/character_card.py`
- `src/models/cards/action_card.py`
- `src/models/cards/item_card.py`
- `src/models/cards/location_card.py`

**Character Cards:**
```python
@dataclass
class CharacterCard(Card):
    """Represents a character card"""
    # Combat Stats (from JSON)
    strength: int = 0          # From "strength" field
    willpower: int = 0         # From "willpower" field
    lore: int = 0              # From "lore" field
    
    # Character Classification
    subtypes: List[str] = field(default_factory=list)  # From "subtypes" array
    
    # Runtime State (not from JSON - game state)
    damage: int = 0            # Current damage taken
    exerted: bool = False      # Whether character is exerted
    location: Optional[str] = None  # Current location (if any)
    
    def __post_init__(self) -> None:
        """Validate character card data after creation"""
        super().__post_init__()
        if self.strength < 0:
            raise ValueError(f"Character strength cannot be negative: {self.strength}")
        if self.willpower < 0:
            raise ValueError(f"Character willpower cannot be negative: {self.willpower}")
        if self.lore < 0:
            raise ValueError(f"Character lore cannot be negative: {self.lore}")
    
    @property
    def is_alive(self) -> bool:
        """Check if character is still alive (damage < willpower)"""
        return self.damage < self.willpower
    
    @property
    def current_strength(self) -> int:
        """Get current strength (may be modified by abilities)"""
        return self.strength
    
    @property
    def current_willpower(self) -> int:
        """Get current willpower (may be modified by abilities)"""
        return self.willpower
    
    @property
    def current_lore(self) -> int:
        """Get current lore value (may be modified by abilities)"""
        return self.lore
    
    def deal_damage(self, amount: int) -> None:
        """Deal damage to this character"""
        if amount < 0:
            raise ValueError("Damage amount cannot be negative")
        self.damage += amount
    
    def exert(self) -> None:
        """Exert this character"""
        self.exerted = True
    
    def ready(self) -> None:
        """Ready this character"""
        self.exerted = False
    
    def can_quest(self) -> bool:
        """Check if this character can quest"""
        return not self.exerted and self.is_alive
    
    def has_subtype(self, subtype: str) -> bool:
        """Check if this character has a specific subtype"""
        return subtype in self.subtypes
    
    def get_origin_type(self) -> Optional[str]:
        """Get the origin type (Storyborn, Dreamborn, Floodborn)"""
        origin_types = {"Storyborn", "Dreamborn", "Floodborn"}
        for subtype in self.subtypes:
            if subtype in origin_types:
                return subtype
        return None
```

**Action Cards:**
```python
@dataclass 
class ActionCard(Card):
    """Represents an action card (includes songs)"""
    # Action effects (derived from abilities)
    effects: List[str] = field(default_factory=list)
    
    @property
    def is_song(self) -> bool:
        """Check if this action is a song (has singer cost reduction)"""
        for ability in self.abilities:
            if "sing this song" in ability.effect.lower():
                return True
        return False
    
    @property
    def singer_cost_reduction(self) -> Optional[int]:
        """Get the cost reduction for singers (if this is a song)"""
        if not self.is_song:
            return None
        
        # Parse from ability text like "cost 2 or more can sing..."
        for ability in self.abilities:
            effect_text = ability.effect.lower()
            if "cost" in effect_text and "sing" in effect_text:
                words = effect_text.split()
                for i, word in enumerate(words):
                    if word == "cost" and i + 1 < len(words):
                        try:
                            return int(words[i + 1])
                        except ValueError:
                            continue
        return None
    
    def can_be_sung_by_character(self, character_strength: int) -> bool:
        """Check if a character with given strength can sing this song"""
        if not self.is_song:
            return False
        required_strength = self.singer_cost_reduction
        if required_strength is None:
            return False
        return character_strength >= required_strength
    
    def get_effective_cost(self, is_being_sung: bool = False) -> int:
        """Get the effective cost to play this action"""
        if is_being_sung and self.is_song:
            reduction = self.singer_cost_reduction or 0
            return max(0, self.cost - reduction)
        return self.cost
```

**Item Cards:**
```python
@dataclass
class ItemCard(Card):
    """Represents an item card"""
    # Runtime State
    attached_to: Optional[str] = None  # Character this is attached to (if any)
    
    @property
    def is_permanent(self) -> bool:
        """Check if item stays in play (vs single-use)"""
        # Determine from ability text - items with ongoing effects typically stay in play
        for ability in self.abilities:
            effect_text = ability.effect.lower()
            if any(keyword in effect_text for keyword in ["while", "as long as", "whenever", "during"]):
                return True
        return True  # Default to permanent
    
    @property
    def is_attachment(self) -> bool:
        """Check if this item attaches to characters"""
        for ability in self.abilities:
            effect_text = ability.effect.lower()
            if any(keyword in effect_text for keyword in ["attach", "equipped", "bearer"]):
                return True
        return False
    
    def attach_to_character(self, character_name: str) -> None:
        """Attach this item to a character"""
        if not self.is_attachment:
            raise ValueError(f"Item {self.full_name} cannot be attached to characters")
        self.attached_to = character_name
    
    def is_attached(self) -> bool:
        """Check if this item is currently attached to a character"""
        return self.attached_to is not None
```

**Location Cards:**
```python
@dataclass
class LocationCard(Card):
    """Represents a location card"""
    # Location Properties (from JSON)
    move_cost: int = 0         # From "moveCost" field
    willpower: int = 0         # From "willpower" field  
    lore: Optional[int] = None # From "lore" field (some locations provide lore)
    
    # Runtime State
    damage: int = 0            # Current damage to location
    characters: List[str] = field(default_factory=list)  # Character names at this location
    
    def __post_init__(self) -> None:
        """Validate location card data after creation"""
        super().__post_init__()
        if self.move_cost < 0:
            raise ValueError(f"Location move cost cannot be negative: {self.move_cost}")
        if self.willpower < 0:
            raise ValueError(f"Location willpower cannot be negative: {self.willpower}")
    
    @property
    def is_destroyed(self) -> bool:
        """Check if location is destroyed (damage >= willpower)"""
        return self.damage >= self.willpower
    
    @property
    def provides_lore(self) -> bool:
        """Check if this location provides lore when quested at"""
        return self.lore is not None and self.lore > 0
    
    def deal_damage(self, amount: int) -> None:
        """Deal damage to this location"""
        if amount < 0:
            raise ValueError("Damage amount cannot be negative")
        self.damage += amount
    
    def add_character(self, character_name: str) -> None:
        """Add a character to this location"""
        if character_name not in self.characters:
            self.characters.append(character_name)
    
    def remove_character(self, character_name: str) -> None:
        """Remove a character from this location"""
        if character_name in self.characters:
            self.characters.remove(character_name)
    
    def can_move_character_here(self, player_available_ink: int) -> bool:
        """Check if a player can afford to move a character here"""
        return player_available_ink >= self.move_cost
```

#### A3: Card Factory and Loading
Create the system to convert JSON data into card objects.

**Files to Create:**
- `src/models/cards/card_factory.py`

**Key Implementation:**
```python
class CardFactory:
    """Factory for creating card objects from JSON data"""
    
    @staticmethod
    def from_json(card_data: dict) -> Card:
        """Create appropriate card type from lorcana-json data"""
        card_type = card_data.get("type")
        
        # Parse common fields first
        common_fields = CardFactory._parse_common_fields(card_data)
        
        if card_type == "Character":
            return CharacterCard(**common_fields, **CardFactory._parse_character_fields(card_data))
        elif card_type == "Action":
            return ActionCard(**common_fields, **CardFactory._parse_action_fields(card_data))
        elif card_type == "Item":
            return ItemCard(**common_fields, **CardFactory._parse_item_fields(card_data))
        elif card_type == "Location":
            return LocationCard(**common_fields, **CardFactory._parse_location_fields(card_data))
        else:
            raise ValueError(f"Unknown card type: {card_type}")
    
    @staticmethod
    def _parse_common_fields(card_data: dict) -> dict:
        """Parse fields common to all card types"""
        # Handle color - could be single color or multi-color like "Amber-Steel"
        color_str = card_data.get("color", "")
        try:
            color = CardColor(color_str)
        except ValueError:
            # Handle multi-color cards by taking the first color for now
            if "-" in color_str:
                first_color = color_str.split("-")[0]
                color = CardColor(first_color)
            else:
                raise ValueError(f"Unknown card color: {color_str}")
        
        return {
            'id': card_data['id'],
            'name': card_data['name'],
            'version': card_data.get('version'),
            'full_name': card_data['fullName'],
            'cost': card_data['cost'],
            'color': color,
            'inkwell': card_data['inkwell'],
            'rarity': Rarity(card_data['rarity']),
            'set_code': card_data['setCode'],
            'number': card_data['number'],
            'story': card_data['story'],
            'abilities': CardFactory._parse_abilities(card_data.get('abilities', [])),
            'flavor_text': card_data.get('flavorText'),
            'full_text': card_data.get('fullText', ''),
            'artists': card_data.get('artists', [])
        }
    
    @staticmethod
    def _parse_character_fields(card_data: dict) -> dict:
        """Parse fields specific to character cards"""
        return {
            'strength': card_data.get('strength', 0),
            'willpower': card_data.get('willpower', 0),
            'lore': card_data.get('lore', 0),
            'subtypes': card_data.get('subtypes', [])
        }
    
    @staticmethod
    def _parse_action_fields(card_data: dict) -> dict:
        """Parse fields specific to action cards"""
        # Extract effects from abilities
        effects = []
        for ability in card_data.get('abilities', []):
            if ability.get('effect'):
                effects.append(ability['effect'])
        return {'effects': effects}
    
    @staticmethod
    def _parse_item_fields(card_data: dict) -> dict:
        """Parse fields specific to item cards"""
        return {}  # Items don't have special fields beyond the base card
    
    @staticmethod
    def _parse_location_fields(card_data: dict) -> dict:
        """Parse fields specific to location cards"""
        return {
            'move_cost': card_data.get('moveCost', 0),
            'willpower': card_data.get('willpower', 0),
            'lore': card_data.get('lore')  # Can be None
        }
    
    @staticmethod
    def _parse_abilities(abilities_data: List[dict]) -> List[Ability]:
        """Parse abilities from JSON structure"""
        abilities = []
        
        for ability_data in abilities_data:
            ability_type_str = ability_data.get('type', '')
            name = ability_data.get('name', '')
            effect = ability_data.get('effect', '')
            full_text = ability_data.get('fullText', effect)
            
            if ability_type_str == 'keyword':
                keyword = ability_data.get('keyword', '')
                value = ability_data.get('value')  # For abilities like "Singer 5"
                abilities.append(KeywordAbility(
                    name=name,
                    type=AbilityType.KEYWORD,
                    effect=effect,
                    full_text=full_text,
                    keyword=keyword,
                    value=value
                ))
            elif ability_type_str == 'triggered':
                abilities.append(TriggeredAbility(
                    name=name,
                    type=AbilityType.TRIGGERED,
                    effect=effect,
                    full_text=full_text,
                    trigger_condition=effect  # Store as string for now
                ))
            elif ability_type_str == 'static':
                abilities.append(StaticAbility(
                    name=name,
                    type=AbilityType.STATIC,
                    effect=effect,
                    full_text=full_text
                ))
            elif ability_type_str == 'activated':
                abilities.append(ActivatedAbility(
                    name=name,
                    type=AbilityType.ACTIVATED,
                    effect=effect,
                    full_text=full_text,
                    costs=[]  # TODO: Parse costs from text
                ))
            else:
                # Create a generic ability for unknown types
                abilities.append(Ability(
                    name=name,
                    type=AbilityType.STATIC,  # Default fallback
                    effect=effect,
                    full_text=full_text
                ))
        
        return abilities
```

### Part B: Ability System Foundation

#### B1: Basic Ability Classes
Start with a simple ability system that can be expanded later.

**Files to Create:**
- `src/models/abilities/base_ability.py`
- `src/models/abilities/__init__.py`

**Initial Implementation:**
```python
@dataclass
class Ability:
    """Base class for all card abilities"""
    name: str                  # From "name" field in JSON
    type: AbilityType          # From "type" field
    effect: str                # From "effect" field
    full_text: str             # From "fullText" field
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Check if this ability can be activated (override in subclasses)"""
        return False
    
    def execute(self, game_state: 'GameState', targets: List['Target']) -> None:
        """Execute this ability (override in subclasses)"""
        raise NotImplementedError("Ability execution not implemented")

class AbilityType(Enum):
    KEYWORD = "keyword"
    TRIGGERED = "triggered" 
    STATIC = "static"
    ACTIVATED = "activated"

# Simple subclasses for now
@dataclass
class KeywordAbility(Ability):
    """Keyword abilities like Shift, Evasive, etc."""
    keyword: str
    value: Optional[int] = None  # For abilities like "Singer 5"

@dataclass
class StaticAbility(Ability):
    """Always-active abilities"""
    pass

@dataclass
class TriggeredAbility(Ability):
    """Abilities that trigger on events"""
    trigger_condition: str  # TODO: Make this more structured later

@dataclass
class ActivatedAbility(Ability):
    """Abilities that require activation and costs"""
    costs: List[str] = field(default_factory=list)  # TODO: Structure this later
```

### Part C: Game Structure Objects

#### C1: Deck Model
Represent a collection of cards that follows Lorcana deck building rules.

**Files to Create:**
- `src/models/game/deck.py`

**Implementation:**
```python
@dataclass
class DeckCard:
    """A card in a deck with its quantity"""
    card: Card
    quantity: int

@dataclass
class Deck:
    """Represents a Lorcana deck"""
    name: str
    cards: List[DeckCard]
    
    @property
    def total_cards(self) -> int:
        """Total number of cards in deck"""
        return sum(deck_card.quantity for deck_card in self.cards)
    
    @property
    def unique_cards(self) -> int:
        """Number of unique cards in deck"""
        return len(self.cards)
    
    def is_legal(self) -> Tuple[bool, List[str]]:
        """Check if deck is legal for play"""
        errors = []
        
        # Must have exactly 60 cards
        if self.total_cards != 60:
            errors.append(f"Deck must have 60 cards, has {self.total_cards}")
        
        # Max 4 of each card (except basic lands if they exist)
        for deck_card in self.cards:
            if deck_card.quantity > 4:
                errors.append(f"Too many copies of {deck_card.card.full_name}: {deck_card.quantity}")
        
        return len(errors) == 0, errors
    
    def shuffle(self) -> List[Card]:
        """Return a shuffled list of all cards in the deck"""
        import random
        all_cards = []
        for deck_card in self.cards:
            all_cards.extend([deck_card.card] * deck_card.quantity)
        random.shuffle(all_cards)
        return all_cards
    
    @classmethod
    def from_dreamborn(cls, dreamborn_data: dict, card_database: List[Card]) -> 'Deck':
        """Create deck from Dreamborn format using card database"""
        # TODO: Implement using the name-based matching we discovered
        pass
```

#### C2: Player Model
Represent a player's state and resources during a game.

**Files to Create:**
- `src/models/game/player.py`

**Implementation:**
```python
@dataclass
class Player:
    """Represents a player in a Lorcana game"""
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
    
    @property
    def available_ink(self) -> int:
        """Total ink available this turn"""
        return len(self.inkwell)
    
    @property
    def ink_by_color(self) -> Dict[CardColor, int]:
        """Available ink by color"""
        ink_colors = Counter()
        for card in self.inkwell:
            ink_colors[card.color] += 1
        return dict(ink_colors)
    
    def can_afford(self, card: Card) -> bool:
        """Check if player can afford to play a card"""
        return self.available_ink >= card.cost
        # TODO: Add color requirement checking
    
    def draw_card(self) -> Optional[Card]:
        """Draw a card from deck to hand"""
        if self.deck:
            card = self.deck.pop(0)
            self.hand.append(card)
            return card
        return None
    
    def play_ink(self, card: Card) -> bool:
        """Play a card as ink (once per turn)"""
        if not card.inkwell:
            return False
        if card in self.hand:
            self.hand.remove(card)
            self.inkwell.append(card)
            return True
        return False
```

#### C3: Game State Model
Represent the overall state of a game in progress.

**Files to Create:**
- `src/models/game/game_state.py`

**Implementation:**
```python
class Phase(Enum):
    READY = "ready"
    SET = "set" 
    DRAW = "draw"
    MAIN = "main"
    END = "end"

class GameAction(Enum):
    PLAY_INK = "play_ink"
    PLAY_CARD = "play_card"
    QUEST = "quest"
    CHALLENGE = "challenge"
    ACTIVATE_ABILITY = "activate_ability"
    PASS_TURN = "pass_turn"

@dataclass
class GameState:
    """Represents the current state of a Lorcana game"""
    # Players
    players: List[Player]
    active_player_index: int = 0
    
    # Turn/Phase tracking
    turn_number: int = 1
    current_phase: Phase = Phase.READY
    
    # Game Rules State
    first_turn_skip_draw: bool = True  # First player skips draw on turn 1
    ink_played_this_turn: bool = False
    
    # Locations in play (shared)
    locations: List[LocationCard] = field(default_factory=list)
    
    @property
    def active_player(self) -> Player:
        """Get the currently active player"""
        return self.players[self.active_player_index]
    
    @property
    def other_players(self) -> List[Player]:
        """Get all players except the active player"""
        return [p for i, p in enumerate(self.players) if i != self.active_player_index]
    
    def is_game_over(self) -> Tuple[bool, Optional[Player]]:
        """Check if game is over and who won"""
        for player in self.players:
            if player.lore >= 20:
                return True, player
        return False, None
    
    def get_legal_actions(self) -> List[Tuple[GameAction, Any]]:
        """Get all legal actions for the current player/phase"""
        # TODO: Implement based on current phase and game state
        return []
    
    def advance_phase(self) -> None:
        """Move to the next phase of the turn"""
        # TODO: Implement phase progression logic
        pass
```

## Implementation Strategy

### Step 1: Core Infrastructure (Week 1)
1. Set up the basic file structure in `src/models/`
2. Implement base Card class and enums
3. Create simple card factory that can parse basic fields
4. Add basic tests to verify card creation from JSON

### Step 2: Card Type Specialization (Week 1-2)
1. Implement the four specialized card classes
2. Add type-specific field parsing to the factory
3. Test with real cards from each type
4. Handle edge cases and missing fields gracefully

### Step 3: Basic Game Objects (Week 2)
1. Implement Deck class with validation
2. Implement Player class with basic operations
3. Implement GameState class structure
4. Create simple game initialization from deck files

### Step 4: Integration and Testing (Week 2-3)
1. Build a simple game loading system that combines everything
2. Create comprehensive tests with real card data
3. Add debugging and validation tools
4. Document any discoveries that require plan updates

## Testing Strategy

### Unit Tests
Each class should have tests that verify:
- Correct creation from JSON data
- Property calculations work correctly
- Validation catches invalid states
- Edge cases are handled gracefully

### Integration Tests
- Load complete decks and verify all cards parse correctly
- Create game states with real decks
- Test that game rules validation works
- Verify performance with large card databases

### Data Validation Tests
- Compare parsed objects with original JSON to catch mapping errors
- Test with cards that have unusual properties
- Validate that all cards in the database can be parsed

## Known Challenges and Adaptations

### Challenge 1: Multi-Color Cards
Some cards have colors like "Amber-Steel". Our enum needs to handle this.

**Solution**: Extend CardColor enum or use a list of colors.

### Challenge 2: Complex Ability Text
Ability parsing will be complex and may require natural language processing.

**Initial Solution**: Store as text, implement parsing incrementally for common patterns.

### Challenge 3: Missing or Inconsistent Data
Real data may have missing fields or inconsistent formatting.

**Solution**: Make most fields optional and provide sensible defaults.

### Challenge 4: Performance
Loading all 1900+ cards as objects may be slow.

**Solution**: Implement lazy loading and caching strategies.

## Evolution Plan

This plan will evolve as we learn more about:
1. **Data Quirks**: Unexpected formats or missing fields in the JSON
2. **Game Mechanics**: Complex interactions that require model changes
3. **Performance Needs**: Whether our object model is efficient enough
4. **Ability Complexity**: How complex the ability system needs to be

Each iteration should:
1. Implement the planned features
2. Test with real data
3. Document what we learned
4. Update the plan based on new understanding
5. Proceed to the next iteration

The goal is working software that can represent Lorcana cards and games, not perfect software. We'll refine as we go!

## Related Documentation

- **[../../PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md)** - High-level project goals and context
- **[README.md](README.md)** - Card system architecture being implemented
- **[../README.md](../README.md)** - Data models section overview

This implementation plan translates the card system architecture into actionable development steps for building the core data models.
