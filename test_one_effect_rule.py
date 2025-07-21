#!/usr/bin/env python3
"""Test if we're violating the one effect per call rule."""

import sys
from examples.full_game_example import setup_game
from src.lorcana_sim.engine.game_engine import GameEngine, ExecutionMode

# Monkey patch to count effects
original_apply_methods = {}
effect_count_per_call = 0

def count_effect_apply(original_apply):
    def wrapper(self, target, context):
        global effect_count_per_call
        effect_count_per_call += 1
        print(f"  Effect #{effect_count_per_call}: {type(self).__name__}")
        return original_apply(self, target, context)
    return wrapper

# Patch all Effect classes
from src.lorcana_sim.models.abilities.composable.effects import Effect
original_effect_apply = Effect.apply

def patched_effect_apply(self, target, context):
    global effect_count_per_call
    effect_count_per_call += 1
    print(f"  Effect #{effect_count_per_call}: {type(self).__name__}")
    if hasattr(self, '_original_apply'):
        return self._original_apply(target, context)
    else:
        # For effects that don't override apply, just pass
        pass

# Monkey patch Effect.apply
Effect._original_apply = Effect.apply
Effect.apply = patched_effect_apply

def test_one_effect_rule():
    global effect_count_per_call
    
    game_state = setup_game()
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    engine.start_game()
    
    print("Testing one effect per call rule...")
    print("=" * 50)
    
    for i in range(10):  # Test first 10 calls
        effect_count_per_call = 0
        print(f"\nCall #{i+1}:")
        message = engine.next_message()
        print(f"  Message: {message.step if hasattr(message, 'step') else message}")
        print(f"  Effects processed: {effect_count_per_call}")
        
        if effect_count_per_call > 1:
            print(f"  ❌ VIOLATION: {effect_count_per_call} effects in one call!")
        elif effect_count_per_call == 1:
            print(f"  ✅ OK: Exactly 1 effect")
        else:
            print(f"  ℹ️  No effects (probably phase transition)")

if __name__ == "__main__":
    test_one_effect_rule()