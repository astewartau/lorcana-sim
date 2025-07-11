# Data Models Overview

This section covers the design of data structures that represent Lorcana game elements. These models form the foundation for all game simulation logic.

## Purpose

The data models define how we represent:
- **Cards** - All card types (Characters, Actions, Items, Locations) with their properties and abilities
- **Abilities** - The flexible system for card effects and keywords  
- **Game Objects** - Decks, players, and game state structures

## Key Design Principles

1. **Faithful Representation** - Models accurately reflect the real Lorcana game
2. **Extensibility** - Easy to add new cards and mechanics as sets are released
3. **Type Safety** - Clear interfaces and validation to prevent invalid states
4. **Performance** - Efficient for running thousands of game simulations

## Documents in This Section

- **[card-system/](card-system/)** - Complete card system design and implementation
  - **[card-system/README.md](card-system/README.md)** - Comprehensive card model architecture
  - **[card-system/phase1-core-models.md](card-system/phase1-core-models.md)** - Step-by-step implementation plan

## Related Sections

- **[../PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)** - High-level project goals and context

This design serves as the blueprint for Phase 1-3 of the implementation, establishing the object model that all game logic will build upon.