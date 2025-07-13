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
        # Don't add turn transition message here - will be handled after board state
        pass
    
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


def analyze_board_threats(engine):
    """Analyze opponent's board and calculate potential lore gains."""
    game_state = engine.game_state
    opponent = game_state.players[1 - game_state.current_player_index]
    
    # Calculate how much lore opponent could gain next turn if all characters quest
    opponent_potential_lore = 0
    dangerous_characters = []
    
    for character in opponent.characters_in_play:
        if not character.exerted and character.is_dry:  # Can act next turn
            char_lore = character.current_lore
            opponent_potential_lore += char_lore
            # Characters with 2+ lore are "dangerous" threats
            if char_lore >= 2:
                dangerous_characters.append((character, char_lore))
    
    return opponent_potential_lore, dangerous_characters


def evaluate_combat_trades(engine, challenge_actions):
    """Evaluate potential combat trades and find the most valuable ones."""
    trades = []
    
    for action, params in challenge_actions:
        attacker = params['attacker']
        defender = params['defender']
        
        # Simple combat calculation (not accounting for all abilities yet)
        attacker_damage = defender.current_strength
        defender_damage = attacker.current_strength
        
        attacker_survives = attacker.current_willpower > attacker_damage
        defender_dies = defender.current_willpower <= defender_damage
        
        # Calculate trade value: lore we prevent - lore we lose
        lore_prevented = defender.current_lore if defender_dies else 0
        lore_lost = attacker.current_lore if not attacker_survives else 0
        trade_value = lore_prevented - lore_lost
        
        trades.append({
            'action': action,
            'params': params,
            'trade_value': trade_value,
            'attacker_survives': attacker_survives,
            'defender_dies': defender_dies,
            'lore_prevented': lore_prevented,
            'lore_lost': lore_lost
        })
    
    # Sort by trade value (best trades first)
    trades.sort(key=lambda x: x['trade_value'], reverse=True)
    return trades


def choose_strategic_action(engine):
    """Choose a strategic action based on game state analysis."""
    legal_actions = engine.validator.get_all_legal_actions()
    
    if not legal_actions:
        return None, None
    
    game_state = engine.game_state
    current_player = game_state.current_player
    opponent = game_state.players[1 - game_state.current_player_index]
    phase = game_state.current_phase
    
    # Auto-progress non-play phases
    for action, params in legal_actions:
        if action == GameAction.PROGRESS and phase != Phase.PLAY:
            return action, params
    
    # Play ink if low (keep existing logic)
    if current_player.total_ink < 6:
        ink_actions = [(a, p) for a, p in legal_actions if a == GameAction.PLAY_INK]
        if ink_actions:
            return random.choice(ink_actions)
    
    # Early game: prioritize board development if no characters in play
    if len(current_player.characters_in_play) == 0:
        char_actions = [(a, p) for a, p in legal_actions if a == GameAction.PLAY_CHARACTER]
        affordable_chars = [(a, p) for a, p in char_actions if current_player.can_afford(p['card'])]
        if affordable_chars:
            print(f"   🏗️  Strategic: Early game board development")
            return random.choice(affordable_chars)
    
    # Mid game: balance character playing with board actions
    if len(current_player.characters_in_play) < 3 and current_player.total_ink >= 3:
        char_actions = [(a, p) for a, p in legal_actions if a == GameAction.PLAY_CHARACTER]
        affordable_chars = [(a, p) for a, p in char_actions if current_player.can_afford(p['card'])]
        # 50% chance to play a character if we have few characters
        if affordable_chars and random.random() < 0.5:
            print(f"   🎭 Strategic: Building board presence")
            return random.choice(affordable_chars)
    
    # Now for the strategic part: quest vs challenge decisions
    quest_actions = [(a, p) for a, p in legal_actions if a == GameAction.QUEST_CHARACTER]
    challenge_actions = [(a, p) for a, p in legal_actions if a == GameAction.CHALLENGE_CHARACTER]
    sing_actions = [(a, p) for a, p in legal_actions if a == GameAction.SING_SONG]
    
    if not (quest_actions or challenge_actions or sing_actions):
        # No character actions available, progress/pass
        progress_actions = [(a, p) for a, p in legal_actions if a in [GameAction.PROGRESS, GameAction.PASS_TURN]]
        if progress_actions:
            return random.choice(progress_actions)
        return random.choice(legal_actions) if legal_actions else (None, None)
    
    # STRATEGIC DECISION MAKING STARTS HERE
    
    # Calculate current lore positions
    my_lore = current_player.lore
    opponent_lore = opponent.lore
    
    # Analyze potential lore I can gain this turn
    my_potential_lore = sum(p['character'].current_lore for a, p in quest_actions)
    
    # Analyze opponent's board threats
    opponent_potential_lore, dangerous_characters = analyze_board_threats(engine)
    
    # PRIORITY 1: Can I win this turn by questing?
    if my_lore + my_potential_lore >= 20:
        print(f"   🎯 Strategic: Going for the win! ({my_lore} + {my_potential_lore} = {my_lore + my_potential_lore} lore)")
        # Quest with highest lore characters first to guarantee win
        quest_actions.sort(key=lambda x: x[1]['character'].current_lore, reverse=True)
        return quest_actions[0]
    
    # PRIORITY 2: Can opponent win next turn? Must challenge to prevent!
    if opponent_lore + opponent_potential_lore >= 20:
        if challenge_actions:
            trades = evaluate_combat_trades(engine, challenge_actions)
            # Focus on killing the most dangerous characters
            best_preventive_trade = None
            for trade in trades:
                if trade['defender_dies'] and trade['lore_prevented'] >= 2:
                    best_preventive_trade = trade
                    break
            
            if best_preventive_trade:
                defender_name = best_preventive_trade['params']['defender'].name
                lore_prevented = best_preventive_trade['lore_prevented']
                print(f"   🛡️  Strategic: Preventing opponent win by challenging {defender_name} (prevents {lore_prevented} lore)")
                return best_preventive_trade['action'], best_preventive_trade['params']
        
        # If no good challenges, still try to quest for the race
        print(f"   ⚡ Strategic: Racing for lore (opponent could get {opponent_potential_lore} next turn)")
    
    # PRIORITY 3: Evaluate board control vs lore race
    lore_difference = my_lore - opponent_lore
    
    # If I'm significantly behind in lore (5+), focus on questing
    if lore_difference <= -5:
        print(f"   📈 Strategic: Behind by {abs(lore_difference)} lore, focusing on questing")
        if quest_actions:
            return random.choice(quest_actions)
    
    # If I'm significantly ahead in lore (7+), I can afford to challenge for board control
    elif lore_difference >= 7:
        print(f"   🏰 Strategic: Ahead by {lore_difference} lore, maintaining board control")
        if challenge_actions:
            trades = evaluate_combat_trades(engine, challenge_actions)
            if trades and trades[0]['trade_value'] > 0:  # Only if it's a good trade
                best_trade = trades[0]
                print(f"      → Taking good trade (value: {best_trade['trade_value']})")
                return best_trade['action'], best_trade['params']
    
    # PRIORITY 4: Threat assessment - challenge dangerous characters
    if dangerous_characters and challenge_actions:
        trades = evaluate_combat_trades(engine, challenge_actions)
        for trade in trades:
            defender = trade['params']['defender']
            # Challenge if we can kill a dangerous character with positive trade value
            if (trade['defender_dies'] and 
                trade['trade_value'] >= 0 and 
                any(char == defender for char, lore in dangerous_characters)):
                
                print(f"   ⚔️  Strategic: Eliminating threat {defender.name} (trade value: {trade['trade_value']})")
                return trade['action'], trade['params']
    
    # PRIORITY 5: Default to questing for lore, but consider tempo
    # If opponent has a much better board (3+ more ready characters), might want to challenge
    my_ready_chars = len([c for c in current_player.characters_in_play if not c.exerted])
    opponent_ready_chars = len([c for c in opponent.characters_in_play if not c.exerted and c.is_dry])
    
    if opponent_ready_chars >= my_ready_chars + 3 and challenge_actions:
        trades = evaluate_combat_trades(engine, challenge_actions)
        if trades and trades[0]['trade_value'] >= -1:  # Accept small negative trades to catch up
            print(f"   🔄 Strategic: Behind on board ({my_ready_chars} vs {opponent_ready_chars}), trading")
            return trades[0]['action'], trades[0]['params']
    
    # Default: Quest for lore
    if quest_actions:
        print(f"   ⭐ Strategic: Default questing (lore: {my_lore} vs {opponent_lore})")
        return random.choice(quest_actions)
    
    # If no character actions available, try playing characters (higher priority now)
    char_actions = [(a, p) for a, p in legal_actions if a == GameAction.PLAY_CHARACTER]
    affordable_chars = [(a, p) for a, p in char_actions if current_player.can_afford(p['card'])]
    if affordable_chars:
        print(f"   🎭 Strategic: Continuing board development")
        return random.choice(affordable_chars)
    
    # Fallback to any available action
    available_actions = quest_actions + challenge_actions + sing_actions
    if available_actions:
        return random.choice(available_actions)
    
    # Final fallback
    progress_actions = [(a, p) for a, p in legal_actions if a in [GameAction.PROGRESS, GameAction.PASS_TURN]]
    if progress_actions:
        return random.choice(progress_actions)
    
    return random.choice(legal_actions) if legal_actions else (None, None)


def choose_random_action(engine):
    """Choose a strategic action based on game state analysis."""
    return choose_strategic_action(engine)


def simulate_random_game():
    """Simulate a complete random game with real decks."""
    print("🎲 Starting Real Deck Lorcana Game!")
    print("=" * 50)
    
    game_state = setup_game()
    engine = GameEngine(game_state)
    
    turn_count = 0
    max_turns = 200  # Safety limit
    first_action = True  # Track if this is the first action
    
    print_board_state(game_state)
    print()
    print(f"⚪ {game_state.current_player.name} begins turn {game_state.turn_number} - Ready phase")
    
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
        
        # Track if this is the first action (no longer need to print turn start)
        if first_action:
            first_action = False
        
        # Format and display the action result
        display_messages = format_action_result(result, game_state)
        for message in display_messages:
            print(message)
        
        if not result.success:
            continue
        
        # Capture state after action for board state logic
        lore_after = current_player.lore
        
        # Print board state at the end of each player's turn
        if result.result_type == ActionResultType.TURN_ENDED:
            print()  # Blank line before board state
            print_board_state(game_state)
            
            # Add turn transition message for next player
            new_player = result.data['new_player']
            turn_number = result.data['turn_number']
            print()  # Blank line after board state
            print(f"⚪ {new_player.name} begins turn {turn_number} - Ready phase")
    
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
