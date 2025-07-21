#!/usr/bin/env python3
"""Test script to determine if the choice system works for any abilities."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.game_engine import GameEngine, ExecutionMode
from src.lorcana_sim.engine.game_moves import PlayMove, ChoiceMove, PassMove
from src.lorcana_sim.engine.game_messages import MessageType, ChoiceRequiredMessage
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.horse_kick import create_horse_kick


def create_test_character(name, strength=2, willpower=2, cost=2):
    """Create a simple test character."""
    char = CharacterCard(
        id=hash(name) % 10000, name=name, version=None, full_name=name,
        cost=cost, color=CardColor.AMBER, inkwell=True, rarity=Rarity.COMMON,
        set_code='TEST', number=1, strength=strength, willpower=willpower, lore=1, story=''
    )
    return char


def test_horse_kick_choice():
    """Test if HORSE KICK ability generates choice messages when multiple targets exist."""
    print("=== Testing HORSE KICK Choice System ===")
    
    # Create players and game state
    player1 = Player('Player1')
    player2 = Player('Player2')
    game_state = GameState([player1, player2])
    
    # Create HORSE KICK character
    kick_char = create_test_character("Kick Character", strength=3, willpower=3, cost=4)
    kick_char.controller = player1
    
    # Add HORSE KICK ability
    ability_data = {'name': 'HORSE KICK', 'type': 'triggered'}
    horse_kick_ability = create_horse_kick(kick_char, ability_data)
    kick_char.composable_abilities = [horse_kick_ability]
    
    # Create multiple potential targets for both players
    target1 = create_test_character("Enemy Target 1", strength=3, willpower=3, cost=2)
    target1.controller = player2
    
    target2 = create_test_character("Enemy Target 2", strength=4, willpower=4, cost=3)
    target2.controller = player2
    
    friendly_target = create_test_character("Friendly Target", strength=2, willpower=2, cost=1)
    friendly_target.controller = player1
    
    # Set up game state
    player1.hand = [kick_char]
    player1.inkwell = [create_test_character(f"Ink {i}", cost=1) for i in range(5)]
    player2.characters_in_play = [target1, target2]
    player1.characters_in_play = [friendly_target]
    
    print(f"Setup complete:")
    print(f"  Player1 has {len(player1.hand)} cards in hand, {player1.total_ink} ink")
    print(f"  Player2 has {len(player2.characters_in_play)} characters in play")
    print(f"  Player1 has {len(player1.characters_in_play)} characters in play")
    print(f"  Total potential targets: {len(player1.characters_in_play) + len(player2.characters_in_play)}")
    
    # Create game engine
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    engine.start_game()
    
    # Progress to Player 1's play phase
    print("\nProgressing to Player 1 play phase...")
    messages_processed = 0
    found_play_phase = False
    
    for attempt in range(50):  # Increase limit for more thorough testing
        try:
            message = engine.next_message()
            messages_processed += 1
            
            if message.type == MessageType.ACTION_REQUIRED:
                if hasattr(message, 'phase') and message.phase and message.phase.name == 'PLAY' and message.player == player1:
                    print(f"Reached Player 1 play phase! (after {messages_processed} messages)")
                    found_play_phase = True
                    break
                else:
                    # Auto-pass through other phases
                    message = engine.next_message(PassMove())
                    messages_processed += 1
            elif message.type == MessageType.GAME_OVER:
                print("Game ended before reaching play phase")
                return False
                
        except Exception as e:
            print(f"Error progressing to play phase: {e}")
            return False
    
    if not found_play_phase:
        print("Could not reach Player 1 play phase")
        return False
    
    # Play the HORSE KICK character
    print("\nPlaying HORSE KICK character...")
    try:
        play_move = PlayMove(kick_char)
        message = engine.next_message(play_move)
        print(f"Play result: {message.type}")
        
        if message.type != MessageType.STEP_EXECUTED:
            print(f"Failed to play character: {message}")
            return False
        
        print("Character played successfully!")
        
        # Look for choice messages or ability triggers
        choice_found = False
        ability_triggered = False
        
        for i in range(10):
            try:
                message = engine.next_message()
                print(f"Message {i+1}: {message.type}")
                
                if isinstance(message, ChoiceRequiredMessage):
                    print("*** CHOICE REQUIRED! ***")
                    print(f"Choice ID: {message.choice.choice_id}")
                    print(f"Player: {message.choice.player.name}")
                    print(f"Ability: {message.choice.ability_name}")
                    print(f"Prompt: {message.choice.prompt}")
                    print(f"Choice type: {message.choice.choice_type}")
                    print(f"Options ({len(message.choice.options)}):")
                    for j, opt in enumerate(message.choice.options):
                        print(f"  {j}. {opt.id}: {opt.description}")
                    
                    choice_found = True
                    
                    # Make a choice - pick the first option
                    if message.choice.options:
                        selected_option = message.choice.options[0].id
                        print(f"\nChoosing option: {selected_option}")
                        
                        choice_move = ChoiceMove(choice_id=message.choice.choice_id, option=selected_option)
                        result_message = engine.next_message(choice_move)
                        print(f"Choice result: {result_message.type}")
                    
                    break
                    
                elif message.type == MessageType.STEP_EXECUTED:
                    # Check if this is an ability trigger
                    if hasattr(message, 'event_data') and message.event_data:
                        if 'HORSE KICK' in str(message.event_data) or 'ability' in str(message.event_data).lower():
                            print(f"  Ability-related event: {message.event_data}")
                            ability_triggered = True
                    
                elif message.type == MessageType.ACTION_REQUIRED:
                    print("  Game is asking for next action")
                    break
                    
                elif message.type == MessageType.GAME_OVER:
                    print("  Game ended")
                    break
                    
            except Exception as e:
                print(f"Error getting next message: {e}")
                break
        
        # Check final state
        print("\nFinal character states:")
        print(f"Target 1 strength: {getattr(target1, 'current_strength', target1.strength)} (base: {target1.strength})")
        print(f"Target 2 strength: {getattr(target2, 'current_strength', target2.strength)} (base: {target2.strength})")
        print(f"Friendly target strength: {getattr(friendly_target, 'current_strength', friendly_target.strength)} (base: {friendly_target.strength})")
        
        print(f"\nResults:")
        print(f"  Choice message generated: {choice_found}")
        print(f"  Ability triggered: {ability_triggered}")
        
        return choice_found
        
    except Exception as e:
        print(f"Error during HORSE KICK test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crystallize_choice():
    """Test if CRYSTALLIZE ability generates choice messages when multiple enemy targets exist."""
    print("\n=== Testing CRYSTALLIZE Choice System ===")
    
    from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.crystallize import create_crystallize
    
    # Create players and game state
    player1 = Player('Player1')
    player2 = Player('Player2')
    game_state = GameState([player1, player2])
    
    # Create CRYSTALLIZE character
    crystallize_char = create_test_character("Crystallize Character", strength=2, willpower=3, cost=3)
    crystallize_char.controller = player1
    
    # Add CRYSTALLIZE ability
    ability_data = {'name': 'CRYSTALLIZE', 'type': 'triggered'}
    crystallize_ability = create_crystallize(crystallize_char, ability_data)
    crystallize_char.composable_abilities = [crystallize_ability]
    
    # Create multiple enemy targets (CRYSTALLIZE only targets enemies)
    enemy1 = create_test_character("Enemy 1", strength=2, willpower=2, cost=1)
    enemy1.controller = player2
    
    enemy2 = create_test_character("Enemy 2", strength=3, willpower=3, cost=2)
    enemy2.controller = player2
    
    enemy3 = create_test_character("Enemy 3", strength=1, willpower=1, cost=1)
    enemy3.controller = player2
    
    # Set up game state
    player1.hand = [crystallize_char]
    player1.inkwell = [create_test_character(f"Ink {i}", cost=1) for i in range(4)]
    player2.characters_in_play = [enemy1, enemy2, enemy3]
    
    print(f"Setup complete:")
    print(f"  Player1 has {len(player1.hand)} cards in hand, {player1.total_ink} ink")
    print(f"  Player2 has {len(player2.characters_in_play)} enemy characters in play")
    
    # Create game engine and progress to play phase
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    engine.start_game()
    
    # Skip to play phase (simplified)
    for attempt in range(50):
        try:
            message = engine.next_message()
            if (message.type == MessageType.ACTION_REQUIRED and 
                hasattr(message, 'phase') and message.phase and 
                message.phase.name == 'PLAY' and message.player == player1):
                break
            elif message.type != MessageType.ACTION_REQUIRED:
                continue
            else:
                message = engine.next_message(PassMove())
        except:
            break
    
    # Play the CRYSTALLIZE character
    print("\nPlaying CRYSTALLIZE character...")
    try:
        play_move = PlayMove(crystallize_char)
        message = engine.next_message(play_move)
        
        if message.type != MessageType.STEP_EXECUTED:
            print(f"Failed to play character: {message}")
            return False
        
        print("Character played successfully!")
        
        # Look for choice messages
        choice_found = False
        for i in range(10):
            try:
                message = engine.next_message()
                print(f"Message {i+1}: {message.type}")
                
                if isinstance(message, ChoiceRequiredMessage):
                    print("*** CHOICE REQUIRED! ***")
                    print(f"Choice ID: {message.choice.choice_id}")
                    print(f"Player: {message.choice.player.name}")
                    print(f"Ability: {message.choice.ability_name}")
                    print(f"Prompt: {message.choice.prompt}")
                    print(f"Options ({len(message.choice.options)}):")
                    for j, opt in enumerate(message.choice.options):
                        print(f"  {j}. {opt.id}: {opt.description}")
                    
                    choice_found = True
                    break
                    
                elif message.type in [MessageType.ACTION_REQUIRED, MessageType.GAME_OVER]:
                    break
                    
            except Exception as e:
                print(f"Error: {e}")
                break
        
        # Check if any enemies were exerted
        print("\nFinal enemy states:")
        print(f"Enemy 1 exerted: {getattr(enemy1, 'exerted', False)}")
        print(f"Enemy 2 exerted: {getattr(enemy2, 'exerted', False)}")
        print(f"Enemy 3 exerted: {getattr(enemy3, 'exerted', False)}")
        
        print(f"\nResults:")
        print(f"  Choice message generated: {choice_found}")
        
        return choice_found
        
    except Exception as e:
        print(f"Error during CRYSTALLIZE test: {e}")
        return False


if __name__ == "__main__":
    print("Testing Choice System for Abilities")
    print("=" * 50)
    
    horse_kick_works = test_horse_kick_choice()
    crystallize_works = test_crystallize_choice()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"HORSE KICK generates choices: {horse_kick_works}")
    print(f"CRYSTALLIZE generates choices: {crystallize_works}")
    
    if horse_kick_works or crystallize_works:
        print("\n✓ Choice system is working for at least some abilities!")
    else:
        print("\n✗ Choice system appears to be broken for tested abilities.")