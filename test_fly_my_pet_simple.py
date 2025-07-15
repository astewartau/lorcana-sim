#!/usr/bin/env python3
"""
Simple test to verify FLY, MY PET! fix works in full game.
"""

import subprocess
import sys

def test_fly_my_pet_in_game():
    """Run the full game and check for FLY, MY PET! messages."""
    print("Running full game example to test FLY, MY PET! ability...")
    
    # Run the game and capture output
    result = subprocess.run([sys.executable, "examples/full_game_example.py"], 
                          capture_output=True, text=True, timeout=30)
    
    output = result.stdout
    
    # Look for signs that FLY, MY PET! triggered correctly
    fly_my_pet_triggered = "Triggered composable ability: FLY, MY PET!" in output
    card_draw_after_banish = False
    
    lines = output.split('\n')
    for i, line in enumerate(lines):
        # Look for Diablo being banished followed by a card draw
        if "Diablo" in line and "banished" in line:
            # Check next few lines for card draw indication
            for j in range(i+1, min(i+5, len(lines))):
                if "Drew" in lines[j] or "draw" in lines[j].lower():
                    card_draw_after_banish = True
                    print(f"Found Diablo banishment: {line}")
                    print(f"Followed by draw: {lines[j]}")
                    break
            break
    
    print(f"FLY, MY PET! triggered: {fly_my_pet_triggered}")
    print(f"Card draw after Diablo banish: {card_draw_after_banish}")
    
    if fly_my_pet_triggered:
        print("✅ SUCCESS: FLY, MY PET! ability is now triggering!")
        return True
    else:
        print("❌ FAILURE: FLY, MY PET! still not triggering")
        return False

if __name__ == "__main__":
    test_fly_my_pet_in_game()