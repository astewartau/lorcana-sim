# Lorcana Simulation Project Overview

## Overview

This project aims to create a comprehensive Python-based simulation of the Lorcana Trading Card Game. The simulation will handle all game mechanics, rules enforcement, and provide both human-playable and AI-driven gameplay options. The initial implementation will be text-based, focusing on accurate game logic before any graphical interface.

## Background

### What is Lorcana?

Lorcana is a trading card game by Ravensburger featuring Disney characters. Players build 60-card decks and compete to be the first to gain 20 lore. The game involves:
- **Ink System**: Cards can be played as "ink" (resources) or as their actual card type
- **Characters**: Can quest for lore or challenge other characters
- **Actions/Items**: Provide various effects
- **Songs**: Special actions that can be "sung" by characters

### Data Sources

1. **lorcana-json**: A community-maintained repository containing comprehensive card data in JSON format, including:
   - Card stats (cost, power, willpower, lore value)
   - Abilities and effects
   - Card text and metadata
   - Set information

2. **Dreamborn Format**: A deck list format used by tools like Dreamborn.ink and Tabletop Simulator, containing:
   - Card IDs that map to specific cards
   - Quantity of each card
   - Metadata for deck visualization

## Implementation Phases

### Phase 1: Core Data Models

Create the fundamental data structures that represent game elements:

1. **Card Model**
   - Properties: name, cost, color, type, subtypes
   - Character-specific: power, willpower, lore value
   - Abilities: list of ability objects
   - Keywords: Evasive, Rush, Challenger, etc.
   - Inkable: whether the card can be used as ink

2. **Deck Model**
   - Card list with quantities
   - Validation (60 cards, max 4 of each non-location)
   - Shuffle and draw operations

3. **GameState Model**
   - Current turn/phase
   - Active player
   - Lore counters for each player
   - Stack for resolving effects

4. **Player Model**
   - Hand, deck, discard pile
   - Inkwell (available ink)
   - Characters in play (ready/exerted states)
   - Items in play

### Phase 2: Card Data Loading System

Implement loaders to work with existing card data formats:

1. **Lorcana-JSON Parser**
   - Read allCards.json structure
   - Parse card abilities into executable format
   - Handle different ability types (static, triggered, activated)
   - Map keywords to game mechanics

2. **Dreamborn Deck Loader**
   - Parse the Dreamborn JSON format
   - Map CardIDs to actual card data
   - Build complete deck objects

3. **Card Database**
   - Efficient lookup by ID, name, or other properties
   - Cache loaded cards for performance

### Phase 3: Effects and Abilities System

Create a flexible system for card abilities:

1. **Ability Types**
   - **Static**: Always active (e.g., "This character gets +1 strength")
   - **Triggered**: Activate on specific events (e.g., "When played, draw a card")
   - **Activated**: Require manual activation (e.g., "Exert → Deal 2 damage")
   - **Keywords**: Predefined abilities (Singer, Bodyguard, Evasive, etc.)

2. **Effect Resolution**
   - Timing system for triggered abilities
   - Stack-based resolution for multiple effects
   - Target validation
   - Cost payment verification

3. **Effect Templates**
   - Common effects (draw, damage, ready/exert, bounce)
   - Modular effect composition
   - Custom effect scripting for unique cards

### Phase 4: Game Rules Engine

Implement the complete ruleset:

1. **Turn Structure**
   - Ready Phase: Ready all exerted characters
   - Set Phase: Check for start-of-turn effects
   - Draw Phase: Draw a card (skip on first turn)
   - Main Phase: Play cards, activate abilities, quest, challenge
   - End Phase: Cleanup and pass turn

2. **Legal Moves Validation**
   - **Inking**: Once per turn, inkable cards only
   - **Playing Cards**: Sufficient ink, color requirements
   - **Questing**: Only ready characters, generate lore
   - **Challenging**: Banish characters with damage ≥ willpower
   - **Abilities**: Check costs and targets

3. **Special Rules**
   - Bodyguard enforcement
   - Singer cost reduction for songs
   - Location rules (move characters, can't be challenged)
   - Shift mechanic (play on top of same character)

### Phase 5: Game Loop and State Management

Build the main game flow:

1. **Game Initialization**
   - Deck shuffling and opening hands
   - Mulligan decisions
   - Turn order determination

2. **Action Processing**
   - Parse player input
   - Validate action legality
   - Update game state
   - Trigger relevant abilities

3. **Win Conditions**
   - Check for 20+ lore
   - Handle deck-out scenarios
   - Concession handling

### Phase 6: Text-Based User Interface

Create a clear, interactive text interface:

1. **Game Display**
   ```
   === Player 1 (14 lore) ===
   Ink: 5 available (2 Amber, 3 Steel)
   Hand: 4 cards
   
   Characters in Play:
   - Mickey Mouse - Brave Little Tailor (3/3) [READY]
   - Elsa - Snow Queen (4/5) [EXERTED]
   
   === Player 2 (17 lore) ===
   ...
   ```

2. **Action Menu**
   - List available actions
   - Card selection interface
   - Target selection
   - Confirmation prompts

3. **Information Display**
   - Card details on request
   - Game log/history
   - Current phase indicator

### Phase 7: AI Implementation

Develop computer opponents:

1. **Basic AI**
   - Random legal move selection
   - Simple heuristics (play biggest threat)

2. **Intermediate AI**
   - Board evaluation functions
   - Basic planning (save removal for threats)
   - Ink curve consideration

3. **Advanced AI (Future)**
   - Monte Carlo Tree Search
   - Machine learning integration
   - Deck-specific strategies

### Phase 8: Testing Framework

Ensure reliability and correctness:

1. **Unit Tests**
   - Card ability tests
   - Rule validation tests
   - State transition tests

2. **Integration Tests**
   - Full game scenarios
   - Edge case handling
   - Performance benchmarks

3. **Regression Tests**
   - Card interaction verification
   - Rule update validation

## Technical Architecture

### Project Structure
```
lorcana-sim/
├── src/
│   ├── models/          # Core game objects
│   ├── loaders/         # Data parsing modules
│   ├── engine/          # Game rules and logic
│   ├── effects/         # Ability system
│   ├── ui/              # User interface
│   └── ai/              # AI players
├── data/                # Card data cache
├── tests/               # Test suites
├── docs/                # Documentation
└── examples/            # Example decks and games
```

### Key Design Principles

1. **Separation of Concerns**: Clear boundaries between data, logic, and presentation
2. **Extensibility**: Easy to add new cards and mechanics
3. **Testability**: Comprehensive test coverage
4. **Performance**: Efficient for AI simulations

## Future Enhancements

- Multiplayer networking support
- Graphical user interface
- Deck building and collection management
- Tournament/format support
- Advanced AI with deck learning
- Rules variants and custom formats

## Development Priorities

1. **Minimum Viable Product**: Basic cards, core rules, text interface
2. **Full Card Support**: All abilities and edge cases
3. **AI Players**: Competent opponents for testing
4. **Polish**: UI improvements, performance optimization

## Related Documentation

### Data Models
- **[data-models/](data-models/)** - Data structure designs and implementation plans for all game components
- **[data-models/card-system/](data-models/card-system/)** - Complete card system design and implementation
  - **[data-models/card-system/README.md](data-models/card-system/README.md)** - Comprehensive card model architecture  
  - **[data-models/card-system/phase1-core-models.md](data-models/card-system/phase1-core-models.md)** - Step-by-step implementation plan

This overview provides a high-level roadmap for implementing a complete Lorcana simulation that can serve as a platform for playing, testing, and analyzing the game.