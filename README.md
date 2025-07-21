# Lorcana Sim - Disney Card Game Simulation Engine

A comprehensive simulation engine for the Disney Lorcana trading card game, featuring sophisticated game mechanics, ability systems, and message-driven architecture.

## Overview

This project implements a complete digital representation of Disney Lorcana, including:
- **Card Management**: Characters, Actions, Items, and Locations with abilities
- **Game Flow**: Turn phases, ink management, questing, and combat
- **Ability System**: 90+ composable effects supporting triggered, static, and activated abilities
- **Event-Driven Architecture**: Message-based communication for UI integration
- **Zone Management**: Proper handling of deck, hand, play, discard, and ink zones

## Core Game Flow

### Turn Structure
Each player's turn follows these phases:
1. **Ready Phase**: Untap characters and ink
2. **Set Phase**: Prepare for the turn (currently minimal)
3. **Draw Phase**: Draw one card (skip on first turn)
4. **Play Phase**: Play cards, quest, challenge, and take actions

### Information Flow: Moves → Effects → Events → Messages

The game processes player actions through a sophisticated pipeline:

```
Player Move → Effect (ActionQueue) → Game Event → UI Message
     ↓             ↓                      ↓           ↓
  PlayMove    PlayCharacterEffect    CHARACTER_PLAYED  "Ashley played Elsa"
```

#### 1. Move Layer (Player Intent)
Players express intentions through type-safe move objects:
- `PlayMove(card)` - "I want to play this card"
- `QuestMove(character)` - "I want to quest with this character"
- `ChallengeMove(attacker, defender)` - "I want to challenge"
- `InkMove(card)` - "I want to ink this card"

#### 2. Effect Layer (Game Mechanics)
Moves are converted to effects that modify game state:
- `PlayCharacterEffect` - Places character in play
- `QuestEffect` - Generates lore from questing
- `ChallengeEffect` - Applies combat damage
- `DrawCardsEffect` - Draws cards from deck

#### 3. Event Layer (Ability Triggers)
Effects emit events that abilities can respond to:
- `GameEvent.CHARACTER_PLAYED` - When a character enters play
- `GameEvent.CHARACTER_QUESTS` - When a character quests
- `GameEvent.CARD_DRAWN` - When a card is drawn

#### 4. Message Layer (UI Communication)
Events are converted to structured messages for display:
- `StepExecutedMessage` - "Something happened in the game"
- `ActionRequiredMessage` - "Player needs to make a decision"
- `ChoiceRequiredMessage` - "Player must choose between options"

## Engine Architecture

### Three-Engine System

The game uses specialized engines for different concerns:

#### GameEngine (Orchestrator)
- Coordinates between other engines
- Provides unified API for external systems
- Handles initialization and configuration

#### ExecutionEngine (Game Logic)
- Processes moves and converts them to effects
- Manages action validation and execution
- Handles reactive conditions (like banishment)

#### MessageEngine (Communication)
- Generates messages for UI consumption
- Manages message flow and timing
- Creates structured event data

### ActionQueue System

The heart of the execution system is a priority-based action queue:

```python
class ActionQueue:
    # Priority levels determine execution order:
    IMMEDIATE   # Replacement effects (must happen first)
    HIGH        # Triggered abilities, conditional effects
    NORMAL      # Player actions
    LOW         # Delayed effects
    CLEANUP     # End-of-phase cleanup
```

**Key Principle: "One Effect Per Call"**
- `next_message()` processes exactly ONE effect from the queue
- Effects may trigger abilities that queue MORE effects
- New effects wait for subsequent `next_message()` calls
- This prevents infinite loops and ensures predictable game flow

## Ability System

### Composable Ability Framework

Abilities are built using a fluent interface:

```python
ability = ComposableAbility()
    .when(when_enters_play())
    .and_condition(player_has_character_with_trait("Illusion"))
    .target(SELF.player)
    .effect(DrawCards(1))
```

### Ability Types

#### Triggered Abilities
Respond to game events:
- "When this character is played, draw a card"
- "When you draw a card, ready this character"

#### Static Abilities
Always active while conditions are met:
- "Characters with cost 2 or less can't challenge"
- "Your characters cost 1 less ink to play"

#### Activated Abilities
Manually triggered by players:
- "Pay 2 ink: Deal 1 damage to chosen character"

### Zone-Based Activation

Abilities can be active in different zones:
- `ActivationZone.PLAY` - While character is in play (default)
- `ActivationZone.HAND` - While card is in hand
- `ActivationZone.DISCARD` - While card is in discard pile

### Ability Registration and Triggering

1. **Initialization Registration**: All abilities from all cards register at game start
2. **Zone Validation**: At trigger time, check if source card is in valid zone
3. **Event Filtering**: Abilities only receive events they're registered for
4. **Trigger Evaluation**: Check if event matches ability's trigger conditions
5. **Effect Queuing**: If triggered, queue effects with appropriate priority

## Event System

### Event Types
Core game events that abilities can respond to:
- `CHARACTER_PLAYED`, `CHARACTER_QUESTS`, `CHARACTER_CHALLENGES`
- `CARD_DRAWN`, `INK_PLAYED`, `LORE_GAINED`
- `CHARACTER_BANISHED`, `DAMAGE_DEALT`, `TURN_ENDED`

### Event Context
Events carry rich context for ability evaluation:
```python
EventContext(
    event_type=GameEvent.CHARACTER_PLAYED,
    source=character,
    target=None,
    player=current_player,
    game_state=game_state,
    additional_data={'phase': current_phase}
)
```

### Two-Stage Ability Execution

When an ability triggers:
1. **Trigger Notification**: "✨ Treasure Guardian triggered UNTOLD TREASURE"
2. **Effect Execution**: "📚 Ashley drew Helga Sinclair"

This provides clear visibility into when and why abilities activate.

## Game State Management

### Zone Management
Cards move between zones with proper tracking:
- **Deck** → **Hand** (drawing)
- **Hand** → **Play** (playing characters)
- **Hand** → **Ink Well** (inking)
- **Play** → **Discard** (banishment)

### Reactive Conditions
The system automatically checks for state-based effects:
- **Banishment**: Characters with willpower ≤ 0
- **Win Conditions**: Players reaching 20 lore
- **Phase Transitions**: Automatic progression through turn phases

### Cost Modification
Dynamic cost modification system:
- Base costs from card definitions
- Ability-based modifications (e.g., "costs 1 less")
- Situational modifiers

## Testing and Examples

### Test Coverage
- **Unit Tests**: Individual components and effects
- **Integration Tests**: Multi-component interactions
- **Ability Tests**: All named abilities with realistic scenarios
- **Game Flow Tests**: Complete turn cycles and game scenarios

### Example Applications
- `full_game_example.py` - Complete automated game with strategic AI
- `combat_example.py` - Focused combat scenarios
- `deck_builder.py` - Deck construction and analysis tools

## Architecture Principles

### Message-Driven Design
- **One Message Per Call**: Each `next_message()` returns exactly one message
- **Structured Data**: Messages include rich context for UI consumption
- **Event Sourcing**: Game state changes flow through explicit events

### Separation of Concerns
- **Game Logic** (ExecutionEngine): Rules, validation, state changes
- **Communication** (MessageEngine): UI interaction, message formatting
- **Coordination** (GameEngine): Engine management, API facade

### Extensibility
- **Effect System**: Easy to add new card mechanics
- **Ability Framework**: Composable abilities for complex interactions
- **Event System**: Ability registration and triggering
- **Priority System**: Proper timing and interaction resolution

## Recent Improvements

### Phase 1-5 Refactoring (Completed)
- **Unified Queue System**: Single ActionQueue replaces multiple queue systems
- **Direct Move→Effect Conversion**: Eliminated intermediate Action/Step layers
- **String-Based Action Types**: Simplified from complex enum systems
- **Conditional Effects Integration**: Proper evaluation and queuing
- **Message Queue Elimination**: On-demand message generation

### Current Capabilities
- ✅ Complete game flow from setup to victory
- ✅ All core mechanics (ink, questing, combat, abilities)
- ✅ 40+ named abilities with complex interactions
- ✅ Zone-aware ability system
- ✅ Event-driven architecture with message visibility
- ✅ Strategic AI for automated gameplay

### Active Development
- Individual ink card ready messages
- Ability trigger visibility improvements
- Enhanced combat and challenge mechanics
- Performance optimizations

## Getting Started

```python
# Load a deck and start a game
from lorcana_sim.loaders.deck_loader import DeckLoader
from lorcana_sim.engine.game_engine import GameEngine
from lorcana_sim.models.game.game_state import GameState

# Load decks
deck1 = DeckLoader.load_deck("amethyst-steel.json")
deck2 = DeckLoader.load_deck("tace.json")

# Create game
game_state = GameState(decks=[deck1, deck2])
engine = GameEngine(game_state)

# Play the game
while not engine.is_game_over():
    message = engine.next_message()
    # Handle message and make moves
```

See `examples/full_game_example.py` for a complete implementation.

## Contributing

The codebase follows clean architecture principles with comprehensive testing. See the `TODO_*.md` files for current development priorities and architectural decisions.