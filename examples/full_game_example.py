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
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.engine.action_result import ActionResult, ActionResultType
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
    if not hasattr(character, 'composable_abilities') or not character.composable_abilities:
        return ""
    
    abilities = []
    for ability in character.composable_abilities:
        name = ability.name.lower()
        if 'rush' in name:
            abilities.append("Rush")
        elif 'support' in name:
            abilities.append(f"Support {name.split()[-1] if name.split()[-1].isdigit() else '1'}")
        elif 'resist' in name:
            abilities.append(f"Resist {name.split()[-1] if name.split()[-1].isdigit() else '1'}")
        elif 'singer' in name:
            abilities.append(f"Singer {name.split()[-1] if name.split()[-1].isdigit() else '3'}")
        elif 'evasive' in name:
            abilities.append("Evasive")
        elif 'bodyguard' in name:
            abilities.append("Bodyguard")
    
    return f" ({', '.join(abilities)})" if abilities else ""


def format_action_result(result: ActionResult, game_state: GameState) -> list[str]:
    """Format an action result into display messages."""
    messages = []
    
    if not result.success:
        messages.append(f"❌ Action failed: {result.error_message}")
        return messages
    
    if result.result_type == ActionResultType.INK_PLAYED:
        card = result.data['card']
        player = result.data['player']
        ink_after = result.data['ink_after']
        total_ink = result.data['total_ink']
        messages.append(f"🔮 {player.name} inks {card.name} → Ink: {ink_after}/{total_ink}")
        
    elif result.result_type == ActionResultType.CHARACTER_PLAYED:
        character = result.data['character']
        player = result.data['player']
        ink_after = result.data['ink_after']
        total_ink = result.data['total_ink']
        abilities = get_ability_summary(character)
        messages.append(f"🎭 {player.name} plays {character.name}{abilities} ({character.cost} ink) → Ink: {ink_after}/{total_ink}")
        
    elif result.result_type == ActionResultType.ACTION_PLAYED:
        action = result.data['action']
        player = result.data['player']
        ink_after = result.data['ink_after']
        total_ink = result.data['total_ink']
        messages.append(f"⚡ {player.name} plays action {action.name} ({action.cost} ink) → Ink: {ink_after}/{total_ink}")
        
    elif result.result_type == ActionResultType.ITEM_PLAYED:
        item = result.data['item']
        player = result.data['player']
        ink_after = result.data['ink_after']
        total_ink = result.data['total_ink']
        messages.append(f"🔧 {player.name} plays item {item.name} ({item.cost} ink) → Ink: {ink_after}/{total_ink}")
        
    elif result.result_type == ActionResultType.CHARACTER_QUESTED:
        character = result.data['character']
        player = result.data['player']
        lore_gained = result.data['lore_gained']
        lore_after = result.data['lore_after']
        abilities = get_ability_summary(character)
        messages.append(f"🏆 {character.name}{abilities} quests for {lore_gained} lore → {player.name}: {lore_after} lore")
        
    elif result.result_type == ActionResultType.CHARACTER_CHALLENGED:
        attacker = result.data['attacker']
        defender = result.data['defender']
        player = result.data['player']
        attacker_damage = result.data['attacker_damage_taken']
        defender_damage = result.data['defender_damage_taken']
        banished = result.data['banished_characters']
        
        attacker_abilities = get_ability_summary(attacker)
        defender_abilities = get_ability_summary(defender)
        challenge_msg = f"⚔️  {attacker.name}{attacker_abilities} challenges {defender.name}{defender_abilities}"
        
        damage_details = []
        if defender_damage > 0:
            damage_details.append(f"{defender.name} takes {defender_damage} damage")
        if attacker_damage > 0:
            damage_details.append(f"{attacker.name} takes {attacker_damage} damage")
        
        if damage_details:
            challenge_msg += f" → {', '.join(damage_details)}"
        
        if banished:
            challenge_msg += f" → {', '.join(banished)} banished"
            
        messages.append(challenge_msg)
        
    elif result.result_type == ActionResultType.SONG_SUNG:
        singer = result.data['singer']
        song = result.data['song']
        player = result.data['player']
        singer_abilities = get_ability_summary(singer)
        messages.append(f"🎵 {singer.name}{singer_abilities} sings {song.name}")
        
    elif result.result_type == ActionResultType.PHASE_ADVANCED:
        old_phase = result.data['old_phase']
        new_phase = result.data['new_phase']
        player = result.data['player']
        
        if new_phase == Phase.SET:
            messages.append(f"⚙️  {player.name} - Set phase")
        elif new_phase == Phase.DRAW:
            messages.append(f"📖 {player.name} - Draw phase")
            if result.data.get('card_drawn', False):
                cards_drawn = result.data['cards_drawn']
                hand_size = result.data['hand_size']
                deck_size = result.data['deck_size']
                card_text = "card" if cards_drawn == 1 else "cards"
                messages.append(f"   → Drew {cards_drawn} {card_text} → Hand: {hand_size} cards, Deck: {deck_size} cards")
            elif result.data.get('first_player_first_turn', False):
                messages.append(f"   → No draw (first player, first turn)")
            else:
                hand_size = result.data.get('hand_size', 0)
                deck_size = result.data.get('deck_size', 0)
                messages.append(f"   → No draw → Hand: {hand_size} cards, Deck: {deck_size} cards")
        elif new_phase == Phase.PLAY:
            messages.append(f"🎮 {player.name} - Play phase")
            
    elif result.result_type == ActionResultType.TURN_ENDED:
        old_player = result.data['old_player']
        new_player = result.data['new_player']
        turn_number = result.data['turn_number']
        messages.append(f"⚪ {new_player.name} begins turn {turn_number} - Ready phase")
    
    # Handle triggered abilities
    if result.data.get('triggered_abilities'):
        abilities_str = '; '.join(result.data['triggered_abilities'])
        messages.append(f"     → Abilities triggered: {abilities_str}")
    
    return messages


def print_board_state(game_state):
    """Print current board state concisely."""
    ashley = game_state.players[0]
    tace = game_state.players[1]
    current = game_state.current_player
    
    print(f"📊 Board State:")
    print(f"   Ashley: {ashley.lore} lore, {ashley.available_ink}/{ashley.total_ink} ink")
    if ashley.characters_in_play:
        chars = []
        for char in ashley.characters_in_play:
            # Determine character status
            if char.exerted:
                status_letter = "E"  # Exerted
                status_icon = "⚡"
            elif not char.is_dry:
                status_letter = "W"  # Wet ink
                status_icon = "⚪"
            else:
                status_letter = "R"  # Ready
                status_icon = "⚪"
            
            dmg = f"(-{char.damage})" if char.damage > 0 else ""
            abilities = get_ability_summary(char)
            chars.append(f"{char.name}{abilities} {char.current_strength}/{char.current_willpower}{dmg} ({status_letter}) {status_icon}")
        print(f"     Characters: {', '.join(chars)}")
    
    print(f"   Tace: {tace.lore} lore, {tace.available_ink}/{tace.total_ink} ink")
    if tace.characters_in_play:
        chars = []
        for char in tace.characters_in_play:
            # Determine character status
            if char.exerted:
                status_letter = "E"  # Exerted
                status_icon = "⚡"
            elif not char.is_dry:
                status_letter = "W"  # Wet ink
                status_icon = "⚪"
            else:
                status_letter = "R"  # Ready
                status_icon = "⚪"
            
            dmg = f"(-{char.damage})" if char.damage > 0 else ""
            abilities = get_ability_summary(char)
            chars.append(f"{char.name}{abilities} {char.current_strength}/{char.current_willpower}{dmg} ({status_letter}) {status_icon}")
        print(f"     Characters: {', '.join(chars)}")
    
    print(f"   Turn {game_state.turn_number}, {current.name}'s {game_state.current_phase.value} phase")


def choose_random_action(engine):
    """Choose a random legal action, with some basic priorities."""
    legal_actions = engine.validator.get_all_legal_actions()
    
    if not legal_actions:
        return None, None
    
    # Basic priorities: 
    # 1. Progress through non-play phases quickly
    # 2. Play ink early game
    # 3. Play characters if affordable
    # 4. Quest/challenge randomly
    # 5. Pass turn eventually
    
    current_player = engine.game_state.current_player
    phase = engine.game_state.current_phase
    
    # Auto-progress non-play phases
    for action, params in legal_actions:
        if action == GameAction.PROGRESS and phase != Phase.PLAY:
            return action, params
    
    # Play ink if low
    if current_player.total_ink < 6:
        ink_actions = [(a, p) for a, p in legal_actions if a == GameAction.PLAY_INK]
        if ink_actions:
            return random.choice(ink_actions)
    
    # Play characters if affordable
    char_actions = [(a, p) for a, p in legal_actions if a == GameAction.PLAY_CHARACTER]
    affordable_chars = [(a, p) for a, p in char_actions if current_player.can_afford(p['card'])]
    if affordable_chars:
        return random.choice(affordable_chars)
    
    # Prefer questing for lore (80% chance)
    quest_actions = [(a, p) for a, p in legal_actions if a == GameAction.QUEST_CHARACTER]
    challenge_actions = [(a, p) for a, p in legal_actions if a == GameAction.CHALLENGE_CHARACTER]
    sing_actions = [(a, p) for a, p in legal_actions if a == GameAction.SING_SONG]
    
    available_actions = quest_actions + challenge_actions + sing_actions
    if available_actions:
        if random.random() < 0.8 and quest_actions:  # Strongly prefer questing
            return random.choice(quest_actions)
        else:
            return random.choice(available_actions)
    
    # Default to progress/pass
    progress_actions = [(a, p) for a, p in legal_actions if a in [GameAction.PROGRESS, GameAction.PASS_TURN]]
    if progress_actions:
        return random.choice(progress_actions)
    
    # Fallback to any action
    return random.choice(legal_actions)


def simulate_random_game():
    """Simulate a complete random game with real decks."""
    print("🎲 Starting Real Deck Lorcana Game!")
    print("=" * 50)
    
    game_state = setup_game()
    engine = GameEngine(game_state)
    
    turn_count = 0
    max_turns = 200  # Safety limit
    last_board_change = 0
    first_action = True  # Track if this is the first action
    
    print_board_state(game_state)
    print()
    
    while turn_count < max_turns:
        turn_count += 1
        current_player = game_state.current_player
        phase = game_state.current_phase
        
        # Check if game is over
        if game_state.is_game_over():
            result, winner, reason = game_state.get_game_result()
            print(f"🏆 {reason}")
            break
        
        # Get player references (needed for board state logic)
        ashley = game_state.players[0]
        tace = game_state.players[1]
        
        # Choose and execute action
        action, params = choose_random_action(engine)
        
        if action is None:
            print(f"❌ No legal actions for {current_player.name}, ending game")
            break
        
        # Capture state before action for comparison
        lore_before = current_player.lore
        ink_before = current_player.available_ink
        hand_before = len(current_player.hand)
        deck_before = len(current_player.deck)
        
        # Initialize variables for draw detection
        set_hand_before = hand_before
        set_deck_before = deck_before
        
        # Execute action
        result = engine.execute_action(action, params)
        
        # Special case: display first player's ready phase before first action
        if first_action:
            print(f"⚪ {current_player.name} begins turn {game_state.turn_number} - Ready phase")
            first_action = False
        
        # Format and display the action result
        display_messages = format_action_result(result, game_state)
        for message in display_messages:
            print(message)
        
        if not result.success:
            continue
        
        # Capture state after action for board state logic
        lore_after = current_player.lore
        
        # Track board changes for printing
        if result.result_type == ActionResultType.CHARACTER_PLAYED:
            last_board_change = turn_count
        
        # Print board state after significant changes
        should_print_board = (
            action == GameAction.PLAY_CHARACTER or  # New character
            action == GameAction.CHALLENGE_CHARACTER or  # Combat
            (ashley.lore >= 10 and ashley.lore % 5 == 0 and action == GameAction.QUEST_CHARACTER) or  # Every 5 lore past 10
            (tace.lore >= 10 and tace.lore % 5 == 0 and action == GameAction.QUEST_CHARACTER) or
            turn_count % 30 == 0  # Every 30 turns
        )
        
        if should_print_board:
            print_board_state(game_state)
            print()
    
    # Final results
    print("=" * 50)
    ashley = game_state.players[0]
    tace = game_state.players[1]
    print(f"📊 Final Score: Ashley {ashley.lore} - {tace.lore} Tace")
    print(f"🎮 Game completed in {turn_count} turns")
    
    # Display final game result
    result, winner, reason = game_state.get_game_result()
    if result != GameResult.ONGOING:
        print(f"🏆 {reason}")
    else:
        print("🏆 Game ended without completion (turn limit reached)")


if __name__ == "__main__":
    # Set random seed for reproducible results (remove for true randomness)
    random.seed()
    simulate_random_game()
