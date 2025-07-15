"""Test the fixed WHAT DO WE DO NOW? ability to ensure it only triggers when Anna is in play."""

import sys
import os
sys.path.append('.')

from src.lorcana_sim.models.game.game_state import GameState, Phase
from src.lorcana_sim.engine.stepped_game_engine import SteppedGameEngine
from src.lorcana_sim.loaders.deck_loader import DeckLoader
from src.lorcana_sim.engine.game_moves import QuestMove, PassMove

def test_what_do_we_do_now_fix():
    """Test that WHAT DO WE DO NOW? only triggers when Anna is in play."""
    print("🧪 Testing WHAT DO WE DO NOW? trigger fix...")
    
    # Load decks
    loader = DeckLoader('data/all-cards/allCards.json')
    ashley, tace = loader.load_two_decks('data/decks/amethyst-steel.json', 'data/decks/tace.json', 'Ashley', 'Tace')
    
    # Find Elsa and Anna in Tace's deck
    elsa_cards = [card for card in tace.deck + tace.hand if hasattr(card, 'name') and 'Elsa' in card.name]
    anna_cards = [card for card in tace.deck + tace.hand if hasattr(card, 'name') and 'Anna' in card.name]
    
    print(f"📊 Found {len(elsa_cards)} Elsa cards and {len(anna_cards)} Anna cards in Tace's deck")
    
    if not elsa_cards:
        print("❌ No Elsa cards found - can't test WHAT DO WE DO NOW?")
        return
    
    # Set up a controlled test scenario
    game_state = GameState([ashley, tace])
    engine = SteppedGameEngine(game_state)
    engine.start_game()
    
    # Manually put Elsa in play for testing
    elsa = elsa_cards[0]
    tace.hand.clear()
    tace.hand.append(elsa)
    tace.inkwell = [card for card in tace.deck[:3]]  # Give some ink
    tace.deck = tace.deck[3:]
    
    # Play Elsa
    print(f"🎭 Manually putting {elsa.name} in play...")
    if tace.play_character(elsa, 0):  # Free play for testing
        elsa.ready()  # Make sure she can quest
        print(f"✅ {elsa.name} is now in play and ready")
        
        # Check abilities
        abilities = getattr(elsa, 'composable_abilities', [])
        what_do_we_do_now = None
        for ability in abilities:
            if hasattr(ability, 'name') and 'WHAT DO WE DO NOW' in ability.name:
                what_do_we_do_now = ability
                break
        
        if what_do_we_do_now:
            print(f"🎯 Found ability: {what_do_we_do_now.name}")
        
        # Test 1: Quest without Anna in play
        print("\\n🧪 Test 1: Questing WITHOUT Anna in play")
        print(f"Before quest - Tace lore: {tace.lore}")
        
        # Manually trigger quest for testing
        old_lore = tace.lore
        elsa.exert()
        
        # Simulate the quest event manually to see if ability triggers
        from src.lorcana_sim.engine.event_system import EventContext, GameEvent
        quest_context = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=elsa,
            player=tace,
            game_state=game_state
        )
        
        # Check if the trigger condition would be met
        if what_do_we_do_now and hasattr(what_do_we_do_now, 'trigger_condition'):
            trigger_result = what_do_we_do_now.trigger_condition(quest_context)
            print(f"Trigger condition result: {trigger_result}")
            if trigger_result:
                print("❌ FAILURE: Ability triggered without Anna in play!")
            else:
                print("✅ SUCCESS: Ability did NOT trigger without Anna in play")
        
        # Test 2: Add Anna and quest again
        if anna_cards:
            print("\\n🧪 Test 2: Questing WITH Anna in play")
            anna = anna_cards[0]
            tace.hand.append(anna)
            if tace.play_character(anna, 0):  # Free play for testing
                anna.ready()
                elsa.ready()  # Ready Elsa for another quest
                print(f"🎭 {anna.name} is now also in play")
                
                # Test trigger condition again
                if what_do_we_do_now and hasattr(what_do_we_do_now, 'trigger_condition'):
                    trigger_result = what_do_we_do_now.trigger_condition(quest_context)
                    print(f"Trigger condition result with Anna: {trigger_result}")
                    if trigger_result:
                        print("✅ SUCCESS: Ability WOULD trigger with Anna in play")
                    else:
                        print("❌ ISSUE: Ability did not trigger even with Anna in play")
        
    else:
        print("❌ Failed to put Elsa in play")

if __name__ == "__main__":
    test_what_do_we_do_now_fix()