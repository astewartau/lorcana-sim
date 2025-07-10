# Card Model Implementation Plan

## Overview

This document outlines the comprehensive implementation plan for the Card model in the Lorcana simulation. Based on analysis of the lorcana-json data structure, this plan covers all card types, properties, and ability systems that need to be represented.

## Card Type Hierarchy

### Base Card Class
All cards inherit from a base `Card` class with universal properties:

```python
class Card:
    # Core Identity
    id: int                    # Unique identifier
    name: str                  # Character/card name
    version: str               # Version subtitle
    full_name: str             # Complete name (name + version)
    
    # Game Properties
    cost: int                  # Ink cost to play
    color: CardColor           # Ink color enum
    inkwell: bool              # Can be used as ink
    
    # Metadata
    rarity: Rarity             # Common, Uncommon, Rare, Super Rare, Legendary
    set_code: str              # Set identifier
    number: int                # Card number in set
    story: str                 # Disney property
    
    # Abilities & Text
    abilities: List[Ability]   # All abilities on the card
    flavor_text: str           # Thematic text (optional)
    full_text: str             # Complete card text
    
    # Visual
    images: CardImages         # Art URLs
    artists: List[str]         # Artist names
```

### Specialized Card Types

#### Character Cards
```python
class CharacterCard(Card):
    # Combat Stats
    strength: int              # Attack value (⚔)
    willpower: int             # Health/defense (⚡)
    lore: int                  # Lore value when questing (◊)
    
    # Character Classification
    subtypes: List[str]        # Character types and roles
    
    # State (runtime)
    damage: int = 0            # Current damage taken
    exerted: bool = False      # Whether character is exerted
    location: Optional[str] = None  # Current location (if any)
```

#### Action Cards
```python
class ActionCard(Card):
    # Action Type
    is_song: bool              # Whether this is a song
    
    # Song-specific properties
    singer_cost: Optional[int] # Cost reduction for singers (if song)
```

#### Item Cards
```python
class ItemCard(Card):
    # Items may have ongoing effects or be single-use
    is_permanent: bool         # Whether item stays in play
    
    # State (runtime)
    attached_to: Optional[str] = None  # Character this is attached to
```

#### Location Cards
```python
class LocationCard(Card):
    # Location Properties
    move_cost: int             # Cost to move characters here
    willpower: int             # Location durability
    lore: Optional[int] = None # Lore value (some locations provide lore)
    
    # State (runtime)
    damage: int = 0            # Current damage to location
    characters: List[str] = [] # Characters at this location
```

## Ability System

### Ability Base Class
```python
class Ability:
    name: str                  # Ability name (e.g., "VOICELESS")
    type: AbilityType          # static, triggered, activated, keyword
    effect: str                # Effect description
    full_text: str             # Complete ability text
    
    # Execution
    def can_activate(self, game_state: GameState) -> bool: ...
    def execute(self, game_state: GameState, targets: List[Target]) -> None: ...
```

### Ability Types

#### 1. Keyword Abilities
Pre-defined abilities with standardized rules:

```python
class KeywordAbility(Ability):
    keyword: str               # Keyword name
    value: Optional[int] = None # Numeric value (e.g., Singer 5)
    
    # Keyword Categories:
    # Movement: Shift, Rush, Evasive
    # Protection: Bodyguard, Ward, Resist
    # Combat: Challenger, Reckless
    # Support: Support, Singer, Sing Together
    # Special: Vanish, Universal Shift
```

#### 2. Triggered Abilities
Abilities that activate on specific game events:

```python
class TriggeredAbility(Ability):
    trigger: TriggerCondition  # When this ability triggers
    
    # Trigger types:
    # - "When you play this character"
    # - "Whenever this character quests"
    # - "When this character is challenged"
    # - "During your turn, whenever..."
```

#### 3. Static Abilities
Continuous effects that are always active:

```python
class StaticAbility(Ability):
    # These modify game rules or provide constant bonuses
    # Examples:
    # - "This character gets +1 strength"
    # - "Characters can't be challenged while here"
    # - "Your other [type] characters get +1 lore"
```

#### 4. Activated Abilities
Abilities that require manual activation and costs:

```python
class ActivatedAbility(Ability):
    costs: List[Cost]          # Required costs to activate
    
    # Cost types:
    # - Exert (⟳): Tap the character
    # - Ink costs: Pay ink
    # - Other costs: Discard cards, etc.
```

## Supporting Enums and Classes

### Enums
```python
class CardColor(Enum):
    AMBER = "Amber"
    AMETHYST = "Amethyst"
    EMERALD = "Emerald"
    RUBY = "Ruby"
    SAPPHIRE = "Sapphire"
    STEEL = "Steel"

class Rarity(Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    SUPER_RARE = "Super Rare"
    LEGENDARY = "Legendary"

class AbilityType(Enum):
    KEYWORD = "keyword"
    TRIGGERED = "triggered"
    STATIC = "static"
    ACTIVATED = "activated"
```

### Supporting Classes
```python
class CardImages:
    full: str                  # Full resolution image URL
    thumbnail: str             # Thumbnail image URL
    foil_mask: str            # Foil effect mask URL

class Cost:
    type: CostType            # Exert, ink, etc.
    value: Optional[int] = None # Amount (for ink costs)

class Target:
    type: TargetType          # Character, player, etc.
    value: Any                # The actual target object
```

## Character Subtypes Classification

### Implementation Strategy
Character subtypes are stored as a list of strings, but we need to understand their categories for game logic:

```python
class CharacterSubtypes:
    # Origin Types (mutually exclusive)
    ORIGIN_TYPES = {"Storyborn", "Dreamborn", "Floodborn"}
    
    # Character Roles
    ROLES = {"Hero", "Villain", "Ally"}
    
    # Titles and Ranks
    TITLES = {"Princess", "Prince", "King", "Queen", "Captain"}
    
    # Specific Groups
    GROUPS = {"Pirate", "Musketeer", "Alien", "Fairy", "Deity", "Inventor"}
    
    @staticmethod
    def get_origin_type(subtypes: List[str]) -> Optional[str]:
        """Get the origin type from subtypes list"""
        return next((s for s in subtypes if s in CharacterSubtypes.ORIGIN_TYPES), None)
    
    @staticmethod
    def has_role(subtypes: List[str], role: str) -> bool:
        """Check if character has specific role"""
        return role in subtypes
```

## JSON Mapping Strategy

### Field Mapping
Map lorcana-json fields to our model:

```python
class CardFactory:
    @staticmethod
    def from_json(card_data: dict) -> Card:
        """Create appropriate card type from JSON data"""
        card_type = card_data.get("type")
        
        if card_type == "Character":
            return CharacterCard.from_json(card_data)
        elif card_type == "Action":
            return ActionCard.from_json(card_data)
        elif card_type == "Item":
            return ItemCard.from_json(card_data)
        elif card_type == "Location":
            return LocationCard.from_json(card_data)
        else:
            raise ValueError(f"Unknown card type: {card_type}")
    
    @staticmethod
    def parse_abilities(abilities_data: List[dict]) -> List[Ability]:
        """Parse abilities from JSON structure"""
        abilities = []
        for ability_data in abilities_data:
            ability_type = ability_data.get("type")
            
            if ability_type == "keyword":
                abilities.append(KeywordAbility.from_json(ability_data))
            elif ability_type == "triggered":
                abilities.append(TriggeredAbility.from_json(ability_data))
            elif ability_type == "static":
                abilities.append(StaticAbility.from_json(ability_data))
            elif ability_type == "activated":
                abilities.append(ActivatedAbility.from_json(ability_data))
        
        return abilities
```

## Implementation Phases

### Phase 1: Basic Structure
1. Create base Card class with universal properties
2. Implement specialized card type classes
3. Create basic enums and supporting classes
4. Add JSON parsing for core properties

### Phase 2: Ability System Foundation
1. Implement Ability base class
2. Create ability type subclasses
3. Add ability parsing from JSON
4. Implement basic ability execution framework

### Phase 3: Keyword Abilities
1. Enumerate all keyword abilities from lorcana-json
2. Implement each keyword's game mechanics
3. Add keyword parsing and validation
4. Test keyword interactions

### Phase 4: Complex Abilities
1. Implement triggered ability system
2. Add activated ability cost system
3. Create static ability effects
4. Handle ability timing and resolution

### Phase 5: Advanced Features
1. Add card state management (damage, exerted, etc.)
2. Implement location mechanics
3. Add shift and special mechanics
4. Create comprehensive validation

## Testing Strategy

### Unit Tests
- Test each card type creation from JSON
- Verify ability parsing accuracy
- Test card property validation
- Check enum conversions

### Integration Tests
- Test card loading from actual lorcana-json data
- Verify ability execution in game context
- Test card interactions and combinations

### Data Validation
- Compare parsed cards with original JSON
- Validate all fields are correctly mapped
- Check for missing or extra properties

## Enumeration Strategy

To ensure we implement all card components correctly, we need to:

1. **Create Card Database Query Tool**
   - Build a tool to query the lorcana-json data
   - Extract all unique values for each field
   - Generate comprehensive lists of all possible values

2. **Systematic Validation**
   - For each card type, verify all possible field values
   - For each ability type, catalog all variations
   - For each keyword, document the mechanics

3. **Completeness Checking**
   - Ensure all card types are handled
   - Verify all ability types are implemented
   - Check all keyword abilities are supported

This plan provides a comprehensive foundation for implementing the Card model that accurately represents all Lorcana card types and their complex ability systems.