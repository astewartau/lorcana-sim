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
from src.lorcana_sim.engine.event_system import GameEvent
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.engine.step_system import ExecutionMode
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
    
    # Handle new event_data structure if present
    if hasattr(message, 'event_data') and message.event_data and isinstance(message.event_data, dict):
        event_data = message.event_data
        event = event_data.get('event')
        context = event_data.get('context', {})
        
        # Handle GameEvent enum-based events
        if event == GameEvent.CHARACTER_READIED:
            if 'character_name' in context:
                char_name = context['character_name']
                reason = context.get('reason', '')
                if reason == 'ink_dried':
                    print(f"💧 {char_name} ink dried")
                elif reason == 'ready_step':
                    print(f"🔄 {char_name} readied")
                else:
                    print(f"🔄 {char_name} readied")
            elif 'item_name' in context:
                item_name = context['item_name']
                print(f"🔄 {item_name} (item) readied")
            return
            
        elif event == GameEvent.CARD_DRAWN:
            player_name = context.get('player_name', 'Unknown Player')
            if context.get('draw_failed'):
                print(f"📚 {player_name} attempted to draw but deck is empty")
            else:
                card_name = context.get('card_name', 'Unknown Card')
                print(f"📚 {player_name} drew {card_name}")
            return
            
        elif event == GameEvent.DRAW_STEP:
            player_name = context.get('player_name', 'Unknown Player')
            if context.get('action') == 'skipped' and context.get('reason') == 'first_turn':
                print(f"📚 {player_name} skipped first turn draw")
            return
            
        elif event == GameEvent.GAME_ENDS:
            result = context.get('result')
            if result == 'lore_victory':
                winner_name = context.get('winner_name', 'Unknown')
                lore = context.get('lore', 0)
                print(f"🏆 {winner_name} wins with {lore} lore!")
            elif result == 'deck_exhaustion':
                winner_name = context.get('winner_name', 'Unknown')
                loser_name = context.get('loser_name', 'Unknown')
                print(f"🏆 {winner_name} wins - {loser_name} ran out of cards!")
            elif result == 'stalemate':
                passes = context.get('consecutive_passes', 0)
                print(f"🏆 Game ended in stalemate - both players unable to make progress")
            return
    
    # Handle structured effect data from action queue
    if hasattr(message, 'effect_data') and message.effect_data:
        effect_data = message.effect_data
        effect_type = effect_data.get('type')
        
        if effect_type == 'discard_card':
            card_name = effect_data.get('card_name', 'Unknown Card')
            player_name = effect_data.get('player_name', 'Unknown Player')
            print(f"🗑️ {player_name} discarded {card_name}")
            return
            
        elif effect_type == 'gain_lore':
            amount = effect_data.get('amount', 0)
            print(f"⭐ Gained {amount} lore")
            return
            
        elif effect_type == 'draw_cards':
            count = effect_data.get('count', 1)
            card_text = "card" if count == 1 else "cards"
            print(f"📚 Drew {count} {card_text}")
            return
            
        elif effect_type == 'banish_character':
            character_name = effect_data.get('character_name', 'Unknown Character')
            print(f"💀 Banished {character_name}")
            return
            
        elif effect_type == 'return_to_hand':
            card_name = effect_data.get('card_name', 'Unknown Card')
            print(f"↩️ Returned {card_name} to hand")
            return
            
        elif effect_type == 'exert_character':
            character_name = effect_data.get('character_name', 'Unknown Character')
            print(f"💤 Exerted {character_name}")
            return
            
        elif effect_type == 'ready_character':
            character_name = effect_data.get('character_name', 'Unknown Character')
            print(f"✨ Readied {character_name}")
            return
            
        elif effect_type == 'remove_damage':
            amount = effect_data.get('amount', 0)
            character_name = effect_data.get('character_name', 'Unknown Character')
            print(f"❤️‍🩹 Removed {amount} damage from {character_name}")
            return
            
        elif effect_type == 'generic':
            # Handle generic effects with available data
            effect_str = effect_data.get('effect_str', 'Unknown Effect')
            target_name = effect_data.get('target_name', 'Unknown Target')
            source_desc = effect_data.get('source_description', '')
            
            if source_desc and "(sub-effect)" in source_desc:
                print(f"📋 {effect_str}")
            else:
                formatted_desc = f"📋 {effect_str} on {target_name}"
                if source_desc:
                    formatted_desc = f"{source_desc}: {formatted_desc}"
                print(formatted_desc)
            return
    
    # Handle conditional effects with structured data
    if step_id == "conditional_effect_applied" and hasattr(message, 'event_data'):
        event_data = message.event_data
        source = event_data.get('source', 'Unknown')
        ability_name = event_data.get('ability_name', 'Unknown Ability')
        details = event_data.get('details', {})
        
        if details.get('ability_type') == 'keyword':
            ability = details.get('ability_name', 'unknown ability')
            action = details.get('action', 'affected')
            description = f"✨ {source} {action} {ability} ({ability_name})"
        else:
            description = f"✨ {source} - {ability_name} activated"
        
        print(description)
        return
        
    elif step_id == "conditional_effect_removed" and hasattr(message, 'event_data'):
        event_data = message.event_data
        source = event_data.get('source', 'Unknown')
        ability_name = event_data.get('ability_name', 'Unknown Ability')
        details = event_data.get('details', {})
        
        if details.get('ability_type') == 'keyword':
            ability = details.get('ability_name', 'unknown ability')
            description = f"✨ {source} lost {ability} ({ability_name} ended)"
        else:
            description = f"✨ {source} - {ability_name} deactivated"
        
        print(description)
        return
    
    elif "ability_triggered" in step_id.lower():
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
        # Turn transitions now use the same format as phase transitions
        if " → " in description and "phase" in description:
            print(f"⚙️  {description}")
        else:
            print(f"🔄 {description}")
    else:
        # Generic step display
        print(f"📋 {description}")


def simulate_random_game():
    """Simulate a complete random game with real decks using message interface."""
    print("🎲 Starting Real Deck Lorcana Game (Message Interface)!")
    print("=" * 50)
    
    game_state = setup_game()
    engine = GameEngine(game_state, ExecutionMode.PAUSE_ON_INPUT)
    
    # Start the game
    engine.start_game()
    
    message_count = 0
    max_messages = 2000  # Safety limit
    last_turn_number = 0
    
    print_board_state(game_state)
    
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
                print(f"⚪ {message.player.name} begins turn {game_state.turn_number} - {message.phase.value} phase")
                last_turn_number = game_state.turn_number
            
            # Show board state only at start of ready phase
            if message.phase.value == 'ready':
                # Show board state at start of each ready phase (except turn 1)
                if game_state.turn_number > 1:
                    print_board_state(game_state)
            
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
                
        elif isinstance(message, ChoiceRequiredMessage):
            # Handle player choice
            choice_move = handle_choice_message(message)
            message = engine.next_message(choice_move)
            # Continue processing this message in the same iteration
            continue

        else:
            # Handle any other message types (e.g., info messages)
            print(f"ℹ️  {message.description}")
        
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
        result, winner, game_over_data = game_state.get_game_result()
        if game_over_data:
            event = game_over_data.get('event')
            context = game_over_data.get('context', {})
            
            if event == GameEvent.GAME_ENDS:
                result_type = context.get('result')
                if result_type == 'lore_victory':
                    winner_name = context.get('winner_name', 'Unknown')
                    lore = context.get('lore', 0)
                    print(f"🏆 {winner_name} wins with {lore} lore!")
                elif result_type == 'deck_exhaustion':
                    winner_name = context.get('winner_name', 'Unknown')
                    loser_name = context.get('loser_name', 'Unknown')
                    print(f"🏆 {winner_name} wins - {loser_name} ran out of cards!")
                elif result_type == 'stalemate':
                    print(f"🏆 Game ended in stalemate - both players unable to make progress")
    else:
        print("🏆 Game ended without completion (message limit reached)")


if __name__ == "__main__":
    # Set random seed for reproducible results (remove for true randomness)
    random.seed(49)
    simulate_random_game()
