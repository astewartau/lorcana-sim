# Abilities System Overview

## 📚 Documentation Navigation

**Read these files in order**:

1. **[README.md](README.md)** ← *You are here* - Overview and current status
2. **[1-enumeration.md](1-enumeration.md)** - Complete catalog of all 1,222 abilities
3. **[2-roadmap.md](2-roadmap.md)** - Implementation strategy and phases
4. **[3-testing.md](3-testing.md)** - Testing approach and coverage

## 🎯 Current Status

**Total Abilities**: 1,222 unique abilities across 1,933 cards

### ✅ Implemented & Tested (8/14 keywords)
- **Singer** (21 cards) - Cost reduction for songs ✅
- **Evasive** (116 cards) - Challenge restrictions ✅  
- **Bodyguard** (56 cards) - Challenge targeting rules ✅
- **Shift** (189 cards) - Alternative play costs ✅
- **Support** (45 cards) - Quest-triggered lore bonus ✅
- **Ward** (44 cards) - Targeting protection ✅
- **Rush** (38 cards) - Immediate challenge capability ✅
- **Resist** (33 cards) - Damage reduction ✅

**Keywords Progress**: 8/14 implemented (57.1%)  
**Card Coverage**: ~630/1,933 cards have implemented abilities (~32.6%)

## 🧠 Understanding Abilities vs Keywords

### Keywords ARE Abilities
**Keywords are a special subset of abilities** that:
- Have **standardized names** (Evasive, Singer, Shift, etc.)
- Appear on **multiple cards** with the same mechanics
- Have **consistent rules** across all cards
- Are part of the **official Lorcana rules**

### Named Abilities
**The other ~1,200 abilities** are:
- **Unique named abilities** (like "OHANA", "BOLT STARE", "DRAGON FIRE")
- Often appear on **only 1-3 cards** each
- Have **card-specific effects**

### Why Keywords First?
**Return on Investment**:
- **Shift**: 1 implementation → 189 cards! 🔥
- **Evasive**: 1 implementation → 116 cards ✅ 
- **Singer**: 1 implementation → 21 cards ✅
- **Average**: ~44 cards per keyword

vs. **Named Abilities**: ~1.3 cards per ability on average

## 🏗️ System Architecture

The ability system is built on top of:
- **[Game State Foundation](../card-system/phase1-part-b-game-state.md)** - Required foundation for abilities
- **[Card Models](../card-system/phase1-core-models.md)** - Core card models and architecture
- **[Phase 1 Part C Plan](../card-system/phase1-part-c-abilities.md)** - Original abilities implementation plan

## 🎯 Current Test Coverage

- **Unit Tests**: 69 tests (keyword registry, mechanics)
- **Integration Tests**: 69 tests (game state integration)
- **Registry Tests**: 3 tests (keyword registry system)
- **Total**: 254 tests passing (all existing + 138 ability tests)

## 🚀 Next Steps

### ❌ **Remaining Keywords to Implement (6/14)**
1. **Challenger** (31 cards) - Combat strength modifier
2. **Reckless** (14 cards) - Forced challenge behavior
3. **Sing Together** (16 cards) - Team song mechanics
4. **Vanish** (7 cards) - Defensive targeting mechanic
5. **Puppy Shift** (1 card) - Specialized shift for Puppy characters
6. **Universal Shift** (1 card) - Universal shift mechanic

### 🎯 **Priority Order**
1. **High Priority**: Challenger, Reckless (core combat mechanics)
2. **Medium Priority**: Sing Together, Vanish (utility mechanics)
3. **Low Priority**: Puppy Shift, Universal Shift (specialized variants)

This abilities system provides the foundation for implementing all Lorcana card mechanics, from simple keywords that affect hundreds of cards to unique named abilities that make individual cards special.