# Lorcana Simulation - Code Quality Improvement TODO

## Executive Summary

This document outlines code quality issues identified in the Lorcana card game simulation codebase and provides a prioritized roadmap for improvements. The analysis reveals significant code duplication, over-engineering, inconsistent patterns, and separation of concerns issues that impact maintainability and development velocity.

## Critical Issues (High Priority)

### 1. Code Duplication - Ability System
**Problem**: 41+ named ability files with similar patterns
- **Files**: `src/lorcana_sim/models/abilities/composable/named_abilities/`
- **Issue**: Standard Python imports and simple decorator pattern perceived as duplication
- **Impact**: Minimal - this is normal Python code structure

**Resolution**:
- [x] ~~Delete incorrect `static/loyal.py` implementation~~ ✓ Deleted (used wrong approach)
- [x] ~~Evaluate abstraction needs~~ ✓ Decided against - current pattern is clean and flexible
- [x] ~~Keep current simple pattern~~ ✓ The 3-4 line "boilerplate" is just standard Python
- [x] ~~No refactoring needed~~ ✓ Use editor snippets if desired for new abilities

### 2. Test Infrastructure Duplication
**Problem**: Repeated setup patterns across 10+ test files
- **Files**: `tests/named_abilities/*/test_*.py`
- **Issue**: Identical setup methods and character creation logic
- **Impact**: Test maintenance overhead, inconsistent test patterns

**Solution**:
- [x] ~~Create `BaseNamedAbilityTest` class with common setup~~ ✓ Created in `tests/helpers/`
- [x] ~~Extract `create_test_character()` to test utilities~~ ✓ Added to `tests/helpers/character_helpers.py`
- [x] ~~Standardize ability registration testing patterns~~ ✓ All test files use `add_named_ability()` helper
- [x] ~~Create test helper module in `tests/helpers/`~~ ✓ Complete with base class and helper functions

**Results**: Eliminated 200+ lines of duplicate setup code across 10+ test files. All named ability tests now use consistent patterns and centralized test utilities.

### 3. Engine Architecture Over-Engineering
**Problem**: Excessive abstraction in game engine system
- **Files**: `src/lorcana_sim/engine/stepped_game_engine.py` (1500+ lines)
- **Issue**: Complex message queue system, multiple engine variants
- **Impact**: Difficult to understand, maintain, and extend

**Solution**:
- [ ] Consolidate `GameEngine` and `SteppedGameEngine` into single implementation
- [ ] Remove unnecessary message queue abstractions
- [ ] Simplify event handling system
- [ ] Extract UI-specific concerns from engine core

## Major Issues (Medium Priority)

### 4. Separation of Concerns Violations
**Problem**: Classes with multiple responsibilities
- **Files**: `src/lorcana_sim/models/game/game_state.py`, `src/lorcana_sim/engine/game_engine.py`
- **Issue**: GameState handles game logic, zone management, cost modifications
- **Impact**: Difficult to test, modify, and understand

**Solution**:
- [ ] Extract `ZoneManager` from GameState
- [ ] Create separate `TurnManager` for phase/turn logic
- [ ] Move cost modification logic to dedicated service
- [ ] Separate game rules from game state

### 5. Inconsistent Error Handling
**Problem**: Mixed error handling approaches throughout codebase
- **Files**: Multiple engine and model files
- **Issue**: Some functions throw exceptions, others return boolean/tuples
- **Impact**: Unpredictable error behavior, difficult debugging

**Solution**:
- [ ] Standardize on exception-based error handling
- [ ] Create custom exception hierarchy for game errors
- [ ] Add consistent error logging throughout
- [ ] Document error handling patterns

### 6. Builder Pattern Over-Usage
**Problem**: Unnecessary complexity in ability creation
- **Files**: `src/lorcana_sim/models/abilities/composable/composable_ability.py`
- **Issue**: `AbilityBuilder` and `TriggerBuilder` add complexity without clear benefit
- **Impact**: Harder to understand ability creation

**Solution**:
- [ ] Replace builders with simple factory functions
- [ ] Simplify ability creation API
- [ ] Remove unnecessary fluent interfaces
- [ ] Create clear ability construction patterns

## Minor Issues (Low Priority)

### 7. Example Code Duplication
**Problem**: Repeated utility functions across example files
- **Files**: `examples/demo_deck_analysis.py`, `examples/simple_deck_builder.py`
- **Issue**: Duplicate formatting and analysis functions
- **Impact**: Maintenance overhead for example code

**Solution**:
- [ ] Create `examples/common_utils.py` with shared functions
- [ ] Extract common deck analysis patterns
- [ ] Standardize example code structure
- [ ] Create example code style guide

### 8. Naming Convention Inconsistencies
**Problem**: Mixed naming patterns throughout codebase
- **Files**: Various files across the project
- **Issue**: Inconsistent use of snake_case vs camelCase
- **Impact**: Reduced code readability

**Solution**:
- [ ] Establish naming convention guidelines
- [ ] Run linting tools to identify inconsistencies
- [ ] Gradually refactor to consistent naming
- [ ] Add pre-commit hooks for naming consistency

## Refactoring Roadmap

### Phase 1: Foundation (Weeks 1-2)
1. **Extract Common Test Utilities**
   - Create `BaseNamedAbilityTest` class
   - Extract common test helper functions
   - Update all test files to use common patterns

2. **Simplify Ability Registration**
   - Create base ability classes
   - Implement registration decorator
   - Consolidate duplicate ability implementations

### Phase 2: Engine Simplification (Weeks 3-4)
1. **Consolidate Engine Architecture**
   - Merge GameEngine and SteppedGameEngine
   - Remove unnecessary message queue abstractions
   - Simplify event handling

2. **Extract Engine Concerns**
   - Separate UI formatting from engine logic
   - Create focused engine interfaces
   - Improve engine testability

### Phase 3: Architecture Cleanup (Weeks 5-6)
1. **Improve Separation of Concerns**
   - Extract managers from GameState
   - Create focused service classes
   - Improve class responsibilities

2. **Standardize Error Handling**
   - Implement consistent exception patterns
   - Add proper error logging
   - Create error handling documentation

### Phase 4: Polish (Weeks 7-8)
1. **Code Quality Improvements**
   - Fix naming inconsistencies
   - Improve code documentation
   - Add code style enforcement

2. **Example Code Cleanup**
   - Extract common example utilities
   - Standardize example patterns
   - Improve example documentation

## Implementation Guidelines

### Code Quality Standards
- **Maximum File Length**: 500 lines (current: some files >1500 lines)
- **Maximum Function Length**: 50 lines
- **Maximum Class Responsibilities**: Single responsibility principle
- **Test Coverage**: >80% for core game logic
- **Documentation**: All public methods documented

### Architecture Principles
- **Single Responsibility**: Each class should have one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Dependency Inversion**: Depend on abstractions, not concretions
- **Interface Segregation**: Many client-specific interfaces
- **Don't Repeat Yourself**: Eliminate code duplication

### Testing Strategy
- **Unit Tests**: All business logic methods
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete game scenarios
- **Test Utilities**: Shared test infrastructure
- **Mocking**: Mock external dependencies

## Success Metrics

### Code Quality Metrics
- [ ] Reduce code duplication by 60%
- [ ] Reduce average file length by 40%
- [ ] Increase test coverage to 85%
- [ ] Reduce cyclomatic complexity to <10 per method

### Development Velocity Metrics
- [ ] Reduce time to add new abilities by 50%
- [ ] Reduce test writing time by 40%
- [ ] Improve developer onboarding time
- [ ] Reduce bug regression rate

### Maintainability Metrics
- [ ] Improve code readability scores
- [ ] Reduce time to understand code sections
- [ ] Decrease modification impact radius
- [ ] Improve debugging efficiency

## Risk Mitigation

### Technical Risks
- **Breaking Changes**: Implement changes incrementally with backward compatibility
- **Performance Impact**: Profile before/after major refactoring
- **Test Regression**: Maintain existing test coverage during refactoring
- **API Changes**: Version APIs and provide migration guides

### Project Risks
- **Scope Creep**: Focus on identified issues, avoid feature additions
- **Time Overruns**: Prioritize high-impact changes first
- **Team Coordination**: Regular code reviews and pair programming
- **Knowledge Transfer**: Document architectural decisions

## Conclusion

This refactoring initiative will significantly improve code maintainability, reduce technical debt, and increase development velocity. The prioritized approach ensures that the most impactful changes are addressed first while maintaining system stability.

The success of this initiative depends on consistent application of the outlined principles and regular review of progress against the defined metrics.