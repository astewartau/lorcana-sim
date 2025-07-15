"""Complete game example demonstrating a full game to completion with real decks.

This example shows:
- Loading real decks from data/decks using dreamborn parser
- Matching cards by nickname/full name with card database
- Playing to completion (20 lore or deck exhaustion)
- Random decision making for actions
- Concise output focusing on meaningful game events
- Character abilities in action during gameplay
"""

import sys
import os
import random
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.lorcana_sim.models.game.game_state import GameState, GameAction, Phase, GameResult
from src.lorcana_sim.engine.stepped_game_engine import SteppedGameEngine
from src.lorcana_sim.engine.game_messages import (
    MessageType, ActionRequiredMessage, ChoiceRequiredMessage, 
    StepExecutedMessage, GameOverMessage
)
from src.lorcana_sim.engine.game_moves import (
    GameMove, ActionMove, InkMove, PlayMove, QuestMove, ChallengeMove, 
    SingMove, ChoiceMove, PassMove
)
from src.lorcana_sim.loaders.deck_loader import DeckLoader


def setup_game():
    """Set up a game with real decks from data/decks."""
    # Path to cards database and deck files
    cards_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'all-cards', 'allCards.json')
    deck1_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'decks', 'amethyst-steel.json')
    deck2_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'decks', 'tace.json')
    
    # Load decks using the deck loader
    loader = DeckLoader(cards_db_path)
    
    # Load both decks
    ashley, tace = loader.load_two_decks(deck1_path, deck2_path, "Ashley (Amethyst-Steel)", "Tace")
    
    # Create game state
    game_state = GameState([ashley, tace])
    return game_state


def get_ability_summary(character):
    """Get a short summary of character abilities."""
    abilities = []
    
    # Check for temporary abilities in metadata
    if hasattr(character, 'metadata') and character.metadata:
        if character.metadata.get('has_evasive'):
            abilities.append("Evasive")
        if character.metadata.get('has_rush'):
            abilities.append("Rush")
        if character.metadata.get('has_bodyguard'):
            abilities.append("Bodyguard")
        if character.metadata.get('has_ward'):
            abilities.append("Ward")
        if character.metadata.get('challenger_bonus'):
            bonus = character.metadata.get('challenger_bonus')
            abilities.append(f"Challenger +{bonus}")
    
    # Check for temporary challenger bonuses
    if hasattr(character, 'current_challenger_bonus') and character.current_challenger_bonus > 0:
        abilities.append(f"Challenger +{character.current_challenger_bonus}")
    
    # Check composable abilities
    if hasattr(character, 'composable_abilities') and character.composable_abilities:
        for ability in character.composable_abilities:
            name = ability.name.lower()
            if 'rush' in name:
                abilities.append("Rush")
            elif 'support' in name:
                abilities.append("Support")
            elif 'resist' in name:
                # Extract resist value
                parts = name.split()
                value = next((p for p in parts if p.isdigit()), '1')
                abilities.append(f"Resist {value}")
            elif 'singer' in name:
                # Extract singer value
                parts = name.split()
                value = next((p for p in parts if p.isdigit()), '4')
                abilities.append(f"Singer {value}")
            elif 'challenger' in name:
                # Extract challenger value
                parts = name.split()
                value = next((p.replace('+', '') for p in parts if '+' in p or p.isdigit()), '1')
                abilities.append(f"Challenger +{value}")
            elif 'evasive' in name:
                abilities.append("Evasive")
            elif 'bodyguard' in name:
                abilities.append("Bodyguard")
            elif 'ward' in name:
                abilities.append("Ward")
            elif 'reckless' in name:
                abilities.append("Reckless")
            elif 'vanish' in name:
                abilities.append("Vanish")
            elif 'shift' in name:
                # Extract shift value
                parts = name.split()
                value = next((p for p in parts if p.isdigit()), '1')
                abilities.append(f"Shift {value}")
            elif 'sing together' in name:
                # Extract sing together value
                parts = name.split()
                value = next((p for p in parts if p.isdigit()), '4')
                abilities.append(f"Sing Together {value}")
            else:
                # Check if it's a named ability (not a keyword ability)
                if not any(keyword in name for keyword in ['singer', 'challenger', 'rush', 'support', 'resist', 'bodyguard', 'ward', 'evasive', 'vanish', 'reckless', 'shift', 'sing together']):
                    # Display named abilities in a shortened format
                    named_ability = name.replace('_', ' ').title()
                    abilities.append(named_ability)
    
    return f" ({', '.join(abilities)})" if abilities else ""




def print_board_state(game_state):
    """Print detailed board state."""
    ashley = game_state.players[0]
    tace = game_state.players[1]
    current = game_state.current_player
    
    print(f"📊 Board State (Turn {game_state.turn_number}):")
    print(f"{'='*60}")
    
    # Ashley's state
    print(f"👤 Ashley: {ashley.lore} lore, {ashley.available_ink}/{ashley.total_ink} ink")
    print(f"   📚 Hand: {len(ashley.hand)} cards, Deck: {len(ashley.deck)} cards")
    
    if ashley.characters_in_play:
        print(f"   🎭 Characters in play ({len(ashley.characters_in_play)}):")
        for i, char in enumerate(ashley.characters_in_play, 1):
            # Determine character status
            if char.exerted:
                status = "Exerted ⚡"
            elif not char.is_dry:
                status = "Wet Ink 💧"
            else:
                status = "Ready ✅"
            
            dmg = f" (damaged -{char.damage})" if char.damage > 0 else ""
            abilities = get_ability_summary(char)
            print(f"      {i}. {char.name}{abilities}")
            print(f"         💪{char.current_strength}/❤️{char.current_willpower}/⭐{char.current_lore} | {status}{dmg}")
    else:
        print(f"   🎭 No characters in play")
    
    # Show Ashley's ink pile (if any)
    if ashley.inkwell:
        print(f"   🔮 Ink pile ({len(ashley.inkwell)}): {', '.join([card.name for card in ashley.inkwell[:5]])}")
        if len(ashley.inkwell) > 5:
            print(f"      ... and {len(ashley.inkwell) - 5} more")
    
    print()
    
    # Tace's state
    print(f"👤 Tace: {tace.lore} lore, {tace.available_ink}/{tace.total_ink} ink")
    print(f"   📚 Hand: {len(tace.hand)} cards, Deck: {len(tace.deck)} cards")
    
    if tace.characters_in_play:
        print(f"   🎭 Characters in play ({len(tace.characters_in_play)}):")
        for i, char in enumerate(tace.characters_in_play, 1):
            # Determine character status
            if char.exerted:
                status = "Exerted ⚡"
            elif not char.is_dry:
                status = "Wet Ink 💧"
            else:
                status = "Ready ✅"
            
            dmg = f" (damaged -{char.damage})" if char.damage > 0 else ""
            abilities = get_ability_summary(char)
            print(f"      {i}. {char.name}{abilities}")
            print(f"         💪{char.current_strength}/❤️{char.current_willpower}/⭐{char.current_lore} | {status}{dmg}")
    else:
        print(f"   🎭 No characters in play")
    
    # Show Tace's ink pile (if any)
    if tace.inkwell:
        print(f"   🔮 Ink pile ({len(tace.inkwell)}): {', '.join([card.name for card in tace.inkwell[:5]])}")
        if len(tace.inkwell) > 5:
            print(f"      ... and {len(tace.inkwell) - 5} more")
    
    print(f"{'='*60}")
    print(f"▶️  Current: {current.name}'s {game_state.current_phase.value} phase")




def choose_strategic_move(message: ActionRequiredMessage) -> GameMove:
    """Choose a strategic move based on available legal actions."""
    legal_actions = message.legal_actions
    
    if not legal_actions:
        return None
    
    # Convert legal actions to moves using existing strategic logic
    current_player = message.player
    phase = message.phase
    
    # Auto-progress non-play phases
    if phase != Phase.PLAY:
        progress_actions = [a for a in legal_actions if a.action == GameAction.PROGRESS]
        if progress_actions:
            return PassMove()
    
    # Play ink if low (keep existing logic)
    if current_player.total_ink < 6:
        ink_actions = [a for a in legal_actions if a.action == GameAction.PLAY_INK]
        if ink_actions:
            card = random.choice(ink_actions).target
            return InkMove(card=card)
    
    # Early game: prioritize board development
    if len(current_player.characters_in_play) == 0:
        char_actions = [a for a in legal_actions if a.action == GameAction.PLAY_CHARACTER]
        affordable_chars = [a for a in char_actions if current_player.can_afford(a.target)]
        if affordable_chars:
            card = random.choice(affordable_chars).target
            return PlayMove(card=card)
    
    # Look for quest actions
    quest_actions = [a for a in legal_actions if a.action == GameAction.QUEST_CHARACTER]
    challenge_actions = [a for a in legal_actions if a.action == GameAction.CHALLENGE_CHARACTER]
    
    # Strategic decision making (simplified version of existing logic)
    if quest_actions and random.random() < 0.7:  # 70% chance to quest
        character = random.choice(quest_actions).target
        return QuestMove(character=character)
    
    if challenge_actions and random.random() < 0.3:  # 30% chance to challenge
        action = random.choice(challenge_actions)
        return ChallengeMove(
            attacker=action.parameters.get('attacker'),
            defender=action.parameters.get('defender')
        )
    
    # Try to play characters
    char_actions = [a for a in legal_actions if a.action == GameAction.PLAY_CHARACTER]
    affordable_chars = [a for a in char_actions if current_player.can_afford(a.target)]
    if affordable_chars:
        card = random.choice(affordable_chars).target
        return PlayMove(card=card)
    
    # Default to pass/progress
    pass_actions = [a for a in legal_actions if a.action in [GameAction.PROGRESS, GameAction.PASS_TURN]]
    if pass_actions:
        return PassMove()
    
    # Last resort - random action
    if legal_actions:
        action = random.choice(legal_actions)
        return ActionMove(action.action, action.parameters)
    
    return None


def handle_choice_message(message: ChoiceRequiredMessage) -> ChoiceMove:
    """Handle a choice message by making a strategic/random decision."""
    choice = message.choice
    player_name = choice.player.name if choice.player else "Unknown"
    
    print(f"   🎯 {player_name} must make a choice for {choice.ability_name}:")
    print(f"      → {choice.prompt}")
    
    # Display available options
    for option in choice.options:
        print(f"        • {option.id}: {option.description}")
    
    # Make decision based on choice type
    selected_option = None
    
    if choice.choice_type.value == "yes_no":
        # For "may" effects, default to yes
        selected_option = "yes"
        print(f"      ✓ Auto-choosing: yes (default for 'may' effects)")
        
    elif choice.choice_type.value == "select_from_list":
        # For list selection, choose randomly but prefer non-"none" options
        non_none_options = [opt for opt in choice.options if opt.id != "none"]
        if non_none_options:
            chosen = random.choice(non_none_options)
            selected_option = chosen.id
            print(f"      ✓ Auto-choosing: {chosen.description}")
        else:
            selected_option = "none"
            print(f"      ✓ Auto-choosing: none (no other options)")
            
    elif choice.choice_type.value == "select_targets":
        # For target selection, choose randomly
        valid_targets = [opt for opt in choice.options if opt.id != "none"]
        if valid_targets:
            chosen = random.choice(valid_targets)
            selected_option = chosen.id
            print(f"      ✓ Auto-choosing: {chosen.description}")
        else:
            selected_option = "none"
            print(f"      ✓ Auto-choosing: none (no valid targets)")
    
    return ChoiceMove(choice_id=choice.choice_id, option=selected_option)


def display_step_message(message: StepExecutedMessage):
    """Display a step execution message in a user-friendly format."""
    # Extract action type from step_id for better formatting
    step_id = message.step_id
    description = message.description
    
    if "ability_triggered" in step_id.lower():
        print(f"✨ {description}")
    elif "character_readied" in step_id.lower() or "readied" in description:
        print(f"🔄 {description}")
    elif "card_drawn" in step_id.lower() or "drew" in description:
        print(f"📚 {description}")
    elif "ink dried" in description:
        print(f"💧 {description}")
    elif "ink" in step_id.lower() or description.startswith("Inked"):
        print(f"🔮 {description}")
    elif "play" in step_id.lower() or "Played" in description:
        print(f"🎭 {description}")
    elif "quest" in step_id.lower() or "quested" in description:
        print(f"🏆 {description}")
    elif "challenge" in step_id.lower() or "challenged" in description:
        print(f"⚔️  {description}")
    elif "character_banished" in step_id.lower() or "was banished" in description:
        print(f"💀 {description}")
    elif "card_discarded" in step_id.lower() or "discarded" in description:
        print(f"🗑️  {description}")
    elif "lore_gained" in step_id.lower() or "gained" in description and "lore" in description:
        print(f"⭐ {description}")
    elif "phase" in step_id.lower() or "Advanced" in description:
        print(f"⚙️  {description}")
    elif "turn_ended" in step_id.lower() or "Turn ended" in description:
        print(f"🔄 {description}")
    else:
        # Generic step display
        print(f"📋 {description}")


def simulate_random_game():
    """Simulate a complete random game with real decks using message interface."""
    print("🎲 Starting Real Deck Lorcana Game (Message Interface)!")
    print("=" * 50)
    
    game_state = setup_game()
    engine = SteppedGameEngine(game_state)
    
    # Start the game
    engine.start_game()
    
    message_count = 0
    max_messages = 2000  # Safety limit
    last_turn_number = 0
    
    print_board_state(game_state)
    print()
    
    # Get first message
    message = engine.next_message()
    
    while message_count < max_messages:
        message_count += 1
        
        # Handle different message types
        if isinstance(message, GameOverMessage):
            print(f"🏆 {message.reason}")
            break
            
        elif isinstance(message, ActionRequiredMessage):
            # Show turn transition if needed
            if game_state.turn_number != last_turn_number:
                # Show board state at start of each new turn (except turn 1)
                if last_turn_number > 0:
                    print()
                    print_board_state(game_state)
                    print()
                
                print(f"⚪ {message.player.name} begins turn {game_state.turn_number} - {message.phase.value} phase")
                last_turn_number = game_state.turn_number
            
            # Choose a move strategically
            move = choose_strategic_move(message)
            if move is None:
                print(f"❌ No legal moves for {message.player.name}, ending game")
                break
            
            # Process the move by getting the next message with the move
            message = engine.next_message(move)
            # Continue processing this message in the same iteration
            continue
            
        elif isinstance(message, StepExecutedMessage):
            # Display the step that was executed
            display_step_message(message)
            
            # Check if this was a turn ending action and show board state
            if 'turn_ended' in message.step_id:
                print()
                print_board_state(game_state)
                print()
                
        elif isinstance(message, ChoiceRequiredMessage):
            # Handle player choice
            choice_move = handle_choice_message(message)
            message = engine.next_message(choice_move)
            # Continue processing this message in the same iteration
            continue
        
        # Get next message for next iteration
        message = engine.next_message()
    
    # Final results
    print("=" * 50)
    ashley = game_state.players[0]
    tace = game_state.players[1]
    print(f"📊 Final Score: Ashley {ashley.lore} - {tace.lore} Tace")
    print(f"🎮 Game completed in {message_count} messages over {game_state.turn_number} turns")
    
    # Display final game result
    if game_state.is_game_over():
        result, winner, reason = game_state.get_game_result()
        print(f"🏆 {reason}")
    else:
        print("🏆 Game ended without completion (message limit reached)")


if __name__ == "__main__":
    # Set random seed for reproducible results (remove for true randomness)
    random.seed()
    simulate_random_game()
