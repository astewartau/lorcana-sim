# 3. Testing Strategy

> **Prerequisites**: Read [README.md](README.md), [1-enumeration.md](1-enumeration.md), and [2-roadmap.md](2-roadmap.md) first

## Overview

This document outlines the comprehensive testing strategy for Lorcana abilities, focusing on integration with the game state system and ensuring abilities work correctly in actual gameplay scenarios.

## Current Test Coverage Status

### Unit Tests (`test_keyword_abilities.py`)
- ✅ **Registry System**: Tests that keywords are properly registered and can be created
- ✅ **Singer Ability**: Tests cost calculation, song compatibility, and passive nature
- ✅ **Evasive Ability**: Tests challenge restrictions and passive nature
- ✅ **Bodyguard Ability**: Tests targeting rules and passive nature

### Integration Tests (`test_abilities_game_integration.py`)
- ✅ **Singer Integration** (3 tests)
  - Singer enables song singing as a legal move
  - Singer value restricts which songs can be sung
  - Exerted singers cannot sing
  
- ✅ **Evasive Integration** (3 tests)
  - Evasive prevents challenges from non-evasive characters
  - Evasive characters can challenge other evasive characters
  - Mixed board states with evasive and non-evasive targets
  
- ✅ **Bodyguard Integration** (4 tests)
  - Bodyguard must be challenged before other characters
  - Multiple bodyguards can each be challenged
  - No bodyguard allows normal challenge targeting
  - Damaged (but alive) bodyguards still protect
  
- ✅ **Ability Interactions** (2 tests)
  - Evasive + Bodyguard combination
  - Singer + Quest interaction (both use exertion)
  
- ✅ **Edge Cases** (3 tests)
  - Empty board state
  - All characters exerted
  - Dead characters properly removed

## Testing Patterns Established

### 1. Game State Setup Pattern
```python
def setup_game_with_characters(player1_characters, player2_characters):
    # Creates a game in MAIN phase with characters already in play
    # Provides ink for both players
    # Returns game, validator, and engine
```

### 2. Legal Move Validation Pattern
```python
# Get all legal actions
legal_actions = validator.get_all_legal_actions()

# Filter for specific action types
sing_actions = [action for action, params in legal_actions 
                if action == GameAction.SING_SONG]
```

### 3. Ability Effect Verification Pattern
- Tests verify that abilities modify the available legal moves
- Tests check that game state changes correctly after actions
- Tests ensure abilities interact properly with each other

## Testing Strategy for New Abilities

### For Each New Keyword Ability

1. **Unit Tests** (in `test_keyword_abilities.py`):
   - Ability creation and basic properties
   - Ability-specific calculations and logic
   - Passive nature verification

2. **Integration Tests** (in `test_abilities_game_integration.py`):
   - Ability affects legal moves correctly
   - Ability interacts with game state properly
   - Edge cases (exerted characters, empty boards, etc.)
   - Interactions with other abilities

### Test Categories by Ability Type

#### Keywords (Standardized Testing)
- **Combat Keywords** (Evasive, Bodyguard, Rush, Resist, Challenger):
  - Challenge targeting rules
  - Combat timing effects
  - Damage modification
  
- **Resource Keywords** (Singer, Support, Ward):
  - Resource calculation effects
  - Cost modifications
  - Protection mechanics
  
- **Deck Manipulation Keywords** (Shift, Vanish):
  - Card movement between zones
  - Alternative play costs
  - Triggering conditions

#### Named Abilities (Pattern-Based Testing)
- **Triggered Abilities**:
  - Event detection and triggering
  - Timing and priority
  - Target validation
  
- **Static Abilities**:
  - Continuous effect application
  - Conditional effects
  - Stacking with other static effects
  
- **Activated Abilities**:
  - Cost payment and validation
  - Target selection
  - Effect execution

## Coverage Metrics

*Current implementation status detailed in [README.md](README.md)*

- **Implemented Keywords**: 8/14 (57.1%)
- **Unit Test Coverage**: 100% of implemented abilities
- **Integration Test Coverage**: 100% of implemented abilities
- **Total Tests**: 254 (all passing)
  - 69 integration tests for abilities
  - 69 unit tests for abilities
  - 3 registry tests for abilities
  - 113 other system tests

## Quality Assurance Standards

### Every Ability Must Have
1. **Unit Tests**: Verify ability logic in isolation
2. **Integration Tests**: Verify ability works with game state
3. **Edge Case Tests**: Handle empty boards, exerted characters, dead characters
4. **Interaction Tests**: Verify compatibility with other abilities

### Test Quality Metrics
- **Comprehensive**: Tests cover all ability mechanics
- **Realistic**: Tests use actual game scenarios
- **Robust**: Tests handle edge cases and error conditions
- **Maintainable**: Tests are clear and well-documented

## Future Testing Expansion

### Next Priorities (as abilities are implemented)
1. **Challenger Keyword**: Combat strength modification
2. **Reckless Keyword**: Forced challenge behavior
3. **Sing Together Keyword**: Team song mechanics
4. **Vanish Keyword**: Defensive targeting mechanics

### Long-term Testing Goals
1. **Complex Interactions**: Multi-ability combinations
2. **Performance Testing**: Large board states with many abilities
3. **Edge Case Discovery**: Unusual game states and interactions
4. **Regression Testing**: Ensure new abilities don't break existing ones

## Testing Tools and Utilities

### Helper Functions
- `create_character_with_ability()`: Creates test characters with specific abilities
- `create_song_card()`: Creates test songs for Singer testing
- `setup_game_with_characters()`: Creates game states for testing

### Validation Patterns
- Legal move validation via `MoveValidator`
- Game state changes via `GameEngine`
- Ability interactions via combined testing

This testing strategy ensures that every ability is thoroughly tested both in isolation and in realistic game scenarios, providing confidence that the ability system works correctly as it grows to encompass all 1,222 unique abilities.