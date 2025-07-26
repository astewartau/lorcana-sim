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

from src.lorcana_sim.models.game.game_state import GameState, Phase, GameResult
from src.lorcana_sim.engine.event_system import GameEvent
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.engine.game_messages import (
    MessageType, ActionRequiredMessage, ChoiceRequiredMessage, 
    StepExecutedMessage, GameOverMessage
)
from src.lorcana_sim.engine.game_moves import (
    GameMove, InkMove, PlayMove, QuestMove, ChallengeMove, 
    SingMove, ChoiceMove, PassMove
)
from src.lorcana_sim.loaders.deck_loader import DeckLoader
from src.lorcana_sim.models.abilities.composable.conditional_effects import ActivationZone


def setup_game():
    """Set up a game with real decks from data/decks."""
    # Path to cards database and deck files
    cards_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'all-cards', 'allCards.json')
    deck1_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'decks', 'amethyst-steel.json')
    deck2_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'decks', 'tace.json')
    
    # Load decks using the deck loader
    loader = DeckLoader(cards_db_path)
    
    # Load both decks
    ashley, tace = loader.load_two_decks(deck1_path, deck2_path, "Ashley", "Tace")
    
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
        print(f"   🔮 Ink pile ({len(ashley.inkwell)} cards)")
    
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
        print(f"   🔮 Ink pile ({len(tace.inkwell)} cards)")
    


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
        progress_actions = [a for a in legal_actions if a.action == "progress"]
        if progress_actions:
            return PassMove()
    
    # Play ink early game only - hard limit at 7 to prevent excessive inking
    if current_player.total_ink < 5:  # Much more aggressive - stop at 5 ink
        ink_actions = [a for a in legal_actions if a.action == "play_ink"]
        if ink_actions:
            card = random.choice(ink_actions).target
            return InkMove(card=card)
    
    # Prioritize playing characters if we can afford them
    char_actions = [a for a in legal_actions if a.action == "play_character"]
    affordable_chars = [a for a in char_actions if current_player.can_afford(a.target)]
    if affordable_chars and random.random() < 0.8:  # 80% chance to play character
        card = random.choice(affordable_chars).target
        return PlayMove(card=card)
    
    # Look for quest actions
    quest_actions = [a for a in legal_actions if a.action == "quest_character"]
    challenge_actions = [a for a in legal_actions if a.action == "challenge_character"]
    
    # Strategic decision making - be very aggressive
    if challenge_actions and random.random() < 0.95:  # 95% chance to challenge
        action = random.choice(challenge_actions)
        return ChallengeMove(
            attacker=action.parameters.get('attacker'),
            defender=action.parameters.get('defender')
        )
    
    if quest_actions and random.random() < 0.9:  # 90% chance to quest
        character = random.choice(quest_actions).target
        return QuestMove(character=character)
    
    # Try to play characters
    char_actions = [a for a in legal_actions if a.action == "play_character"]
    affordable_chars = [a for a in char_actions if current_player.can_afford(a.target)]
    if affordable_chars:
        card = random.choice(affordable_chars).target
        return PlayMove(card=card)
    
    # Only ink if we have very low ink and can't afford anything (respect 7 ink limit)
    ink_actions = [a for a in legal_actions if a.action == "play_ink"]
    if ink_actions and phase == Phase.PLAY and current_player.total_ink < 3 and current_player.total_ink < 7:
        # Emergency ink if we have very little (but never exceed 7 total ink)
        affordable_cards = [card for card in current_player.hand if card.cost <= current_player.available_ink]
        if not affordable_cards:
            card = random.choice(ink_actions).target
            return InkMove(card=card)
    
    # Last check: just take ANY action instead of passing if we have actions available
    if legal_actions and phase == Phase.PLAY:
        # Don't pass if we have other actions available (but respect ink limit)
        non_pass_actions = [a for a in legal_actions if a.action not in ["progress", "pass_turn"]]
        # Filter out ink actions if we already have 7 or more ink
        if current_player.total_ink >= 7:
            non_pass_actions = [a for a in non_pass_actions if a.action != "play_ink"]
        
        if non_pass_actions:
            action = random.choice(non_pass_actions)
            # Convert to move
            if action.action == "play_ink":
                return InkMove(action.target)
            elif action.action == "play_character":
                return PlayMove(action.target)
            elif action.action == "quest_character":
                return QuestMove(action.target)
            elif action.action == "challenge_character":
                return ChallengeMove(action.parameters['attacker'], action.parameters['defender'])
    
    # Default to pass/progress
    pass_actions = [a for a in legal_actions if a.action in ["progress", "pass_turn"]]
    if pass_actions:
        return PassMove()
    
    # Last resort - random action (respect ink limit)
    if legal_actions:
        # Filter out ink actions if we already have 7 or more ink
        filtered_actions = legal_actions
        if current_player.total_ink >= 7:
            filtered_actions = [a for a in legal_actions if a.action != "play_ink"]
        
        # Use filtered actions if available, otherwise fallback to all actions
        actions_to_choose_from = filtered_actions if filtered_actions else legal_actions
        action = random.choice(actions_to_choose_from)
        
        # Convert LegalAction to appropriate move type
        if action.action == "play_ink":
            return InkMove(action.parameters['card'])
        elif action.action == "play_character":
            return PlayMove(action.parameters['card'])
        elif action.action == "quest_character":
            return QuestMove(action.parameters['character'])
        elif action.action == "challenge_character":
            return ChallengeMove(action.parameters['attacker'], action.parameters['defender'])
        elif action.action in ["progress", "pass_turn"]:
            return PassMove()
        else:
            # Fallback for other action types
            return PassMove()
    
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


def format_card_display(card, include_owner=False):
    """Format a card for display with full name, abilities, and stats."""
    if not card:
        return "Unknown Card"
    
    # Get basic card name
    name = getattr(card, 'name', str(card))
    
    # Get abilities (excluding passive ones that don't need display)
    abilities = []
    if hasattr(card, 'abilities') and card.abilities:
        for ability in card.abilities:
            if hasattr(ability, 'ability_name') and ability.ability_name:
                abilities.append(ability.ability_name.title())
    
    # Build the display string
    display_parts = [name]
    
    # Add abilities in parentheses
    if abilities:
        display_parts.append(f"({', '.join(abilities)})")
    
    # Add stats for characters
    if hasattr(card, 'strength') and hasattr(card, 'willpower'):
        lore = getattr(card, 'lore', 0)
        strength = getattr(card, 'strength', 0)
        willpower = getattr(card, 'willpower', 0)
        display_parts.append(f"💪{strength}/❤️{willpower}/⭐{lore}")
    
    # Add owner if requested
    if include_owner and hasattr(card, 'controller') and card.controller:
        owner_name = getattr(card.controller, 'name', 'Unknown Player')
        return f"{owner_name}'s {' '.join(display_parts)}"
    
    return ' '.join(display_parts)


def display_step_message(message: StepExecutedMessage, game_state=None):
    """Display a step execution message in a user-friendly format."""
    
    # Debug: Log all effect data to see if ability triggers are being processed
    if hasattr(message, 'effect_data') and message.effect_data:
        effect_type = message.effect_data.get('type')
        if effect_type == 'ability_trigger':
            print(f"[DEBUG] Ability trigger effect found: {message.effect_data}")
    
    # Extract action type from step for better formatting
    step = message.step
    
    # Handle new event_data structure if present
    if hasattr(message, 'event_data') and message.event_data and isinstance(message.event_data, dict):
        event_data = message.event_data
        event = event_data.get('event')
        context = event_data.get('context', {})
        
        # Debug: Log all events to see what's happening
        if event == GameEvent.CARD_DRAWN:
            print(f"[DEBUG] CARD_DRAWN event detected in display_step_message")
        
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
            # Debug: Check if this is the draw that should trigger HEAVILY ARMED
            player = context.get('player')
            card = context.get('card')
            
            if player and card:
                # New structure with whole objects
                player_name = player.name if hasattr(player, 'name') else str(player)
                card_name = card.name if hasattr(card, 'name') else str(card)
                print(f"📚 {player_name} drew {card_name}")
                
                # Debug: Check for any characters with abilities in play
                if player_name == "Ashley":
                    print(f"[DEBUG] Ashley drew {card_name}, checking for abilities in play...")
                    characters_in_play = getattr(player, 'characters_in_play', [])
                    print(f"[DEBUG] Characters in play: {len(characters_in_play)}")
                    for i, char in enumerate(characters_in_play):
                        char_name = getattr(char, 'name', f'Character {i}')
                        abilities = getattr(char, 'composable_abilities', [])
                        print(f"[DEBUG] {char_name} has {len(abilities)} composable abilities")
                        for ability in abilities:
                            print(f"[DEBUG] - Ability: {ability.name}")
            else:
                # Fallback to old structure
                player_name = context.get('player_name', 'Unknown Player')
                if context.get('draw_failed'):
                    print(f"📚 {player_name} attempted to draw but deck is empty")
                else:
                    card_name = context.get('card_name', 'Unknown Card')
                    print(f"📚 {player_name} drew {card_name}")
            return
            
        elif event == GameEvent.LORE_GAINED:
            player = context.get('player')
            amount = context.get('amount', 0)
            source = context.get('source')
            
            if player:
                player_name = player.name if hasattr(player, 'name') else str(player)
                if source and hasattr(source, 'name'):
                    print(f"⭐ {player_name} gained {amount} lore from {source.name} → {player.lore} total")
                else:
                    print(f"⭐ {player_name} gained {amount} lore → {player.lore} total")
            return
            
        elif event == GameEvent.CARD_DISCARDED:
            player = context.get('player')
            card = context.get('card')
            from_zone = context.get('from_zone')
            to_zone = context.get('to_zone')
            
            if player and card:
                player_name = player.name if hasattr(player, 'name') else str(player)
                card_name = card.name if hasattr(card, 'name') else str(card)
                from_zone_str = from_zone.value if hasattr(from_zone, 'value') else str(from_zone)
                to_zone_str = to_zone.value if hasattr(to_zone, 'value') else str(to_zone)
                print(f"🗑️ {player_name} discarded {card_name} ({from_zone_str} → {to_zone_str})")
            return
            
        elif event == GameEvent.ABILITY_TRIGGERED:
            character = context.get('character')
            ability_name = context.get('ability_name', 'Unknown Ability')
            effect_type = context.get('effect_type', 'effect')
            amount = context.get('amount', 0)
            
            if character:
                char_name = character.name if hasattr(character, 'name') else str(character)
                if effect_type == "challenger_bonus":
                    print(f"⚔️ {char_name} gained Challenger +{amount} from {ability_name}")
                else:
                    print(f"✨ {char_name} triggered {ability_name}")
            return
            
        elif event == GameEvent.DRAW_STEP:
            player_name = context.get('player_name', 'Unknown Player')
            if context.get('action') == 'skipped' and context.get('reason') == 'first_turn':
                print(f"📚 {player_name} skipped first turn draw")
            return
            
        elif event == GameEvent.INK_PLAYED:
            player = context.get('player')
            card = context.get('card')
            phase = context.get('phase')
            
            # Extract phase info if available
            phase_info = f" (during {phase.value} phase)" if phase and hasattr(phase, 'value') else ""
            
            if player and card:
                player_name = player.name if hasattr(player, 'name') else str(player)
                card_display = format_card_display(card)
                print(f"🔮 {player_name} inked {card_display}{phase_info}")
            else:
                player_name = context.get('player_name', 'Unknown Player')
                card_name = context.get('card_name', 'Unknown Card')
                print(f"🔮 {player_name} inked {card_name}{phase_info}")
            return
            
        elif event == GameEvent.INK_READIED:
            player_name = context.get('player_name', 'Unknown Player')
            ink_count = context.get('ink_count', 0)
            if ink_count > 0:
                print(f"💎 {player_name} readied {ink_count} ink")
            return
            
        elif event in [GameEvent.READY_PHASE, GameEvent.SET_PHASE, GameEvent.DRAW_PHASE, GameEvent.PLAY_PHASE]:
            player = context.get('player')
            player_name = player.name if (player and hasattr(player, 'name')) else 'Unknown Player'
            
            if event == GameEvent.READY_PHASE:
                print(f"⚙️ Ready phase ({player_name})")
            elif event == GameEvent.SET_PHASE:
                print(f"⚙️ Set phase ({player_name})")
            elif event == GameEvent.DRAW_PHASE:
                print(f"⚙️ Draw phase ({player_name})")
            elif event == GameEvent.PLAY_PHASE:
                print(f"⚙️ Play phase ({player_name})")
            return
            
        elif event == GameEvent.CHARACTER_PLAYED:
            character = context.get('character')
            player = context.get('player')
            phase = context.get('phase')
            
            # Extract phase info if available
            phase_info = f" (during {phase.value} phase)" if phase and hasattr(phase, 'value') else ""
            
            if character and player:
                character_display = format_card_display(character)
                player_name = player.name if hasattr(player, 'name') else str(player)
                print(f"🎭 {player_name} played {character_display}{phase_info}")
            elif character:
                character_display = format_card_display(character)
                print(f"🎭 Played {character_display}{phase_info}")
            else:
                character_name = context.get('character_name', 'Unknown')
                player_name = context.get('player_name', 'Unknown Player')
                print(f"🎭 {player_name} played {character_name}{phase_info}")
            return
            
        elif event == GameEvent.CHARACTER_QUESTS:
            character = context.get('character')
            player = context.get('player')
            lore_gained = context.get('lore_gained', 0)
            
            if character and player:
                character_display = format_card_display(character)
                player_name = player.name if hasattr(player, 'name') else str(player)
                current_lore = getattr(player, 'lore', 0)
                print(f"🏆 {player_name} quested with {character_display} for {lore_gained} lore (now {current_lore} total)")
            elif character:
                character_display = format_card_display(character)
                print(f"🏆 Quested with {character_display} for {lore_gained} lore")
            else:
                character_name = context.get('character_name', 'Unknown')
                print(f"🏆 Quested with {character_name} for {lore_gained} lore")
            return
            
        elif event == GameEvent.CHARACTER_CHALLENGES:
            attacker = context.get('attacker')
            defender = context.get('defender')
            damage_to_attacker = context.get('damage_to_attacker', 0)
            damage_to_defender = context.get('damage_to_defender', 0)
            
            if attacker and defender:
                attacker_display = format_card_display(attacker, include_owner=True)
                defender_display = format_card_display(defender, include_owner=True)
                
                damage_parts = []
                if damage_to_defender > 0:
                    defender_name = getattr(defender, 'name', 'Unknown') if defender else 'Unknown'
                    damage_parts.append(f"{defender_name} took {damage_to_defender} damage")
                if damage_to_attacker > 0:
                    attacker_name = getattr(attacker, 'name', 'Unknown') if attacker else 'Unknown'
                    damage_parts.append(f"{attacker_name} took {damage_to_attacker} damage")
                
                details = []
                if damage_parts:
                    details.extend(damage_parts)
                
                detail_text = f" ({', '.join(details)})" if details else ""
                print(f"⚔️ {attacker_display} challenged {defender_display}{detail_text}")
            else:
                attacker_name = context.get('attacker_name', 'Unknown')
                defender_name = context.get('defender_name', 'Unknown')
                print(f"⚔️ {attacker_name} challenged {defender_name}")
            return
            
        elif event == GameEvent.CHARACTER_BANISHED:
            character = context.get('character')
            reason = context.get('reason', 'unknown')
            
            if character:
                character_display = format_card_display(character, include_owner=True)
                if reason == 'willpower_depleted':
                    print(f"💀 {character_display} was banished!")
                else:
                    print(f"💀 {character_display} was banished ({reason})!")
            else:
                character_name = context.get('character_name', 'Unknown')
                print(f"💀 {character_name} was banished!")
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
        
        if effect_type == 'ability_trigger':
            source = effect_data.get('source_card_name', 'Unknown')
            ability = effect_data.get('ability_name', 'ability')
            print(f"✨ {source} triggered {ability}")
            return
            
        elif effect_type == 'discard_card':
            card_name = effect_data.get('card_name', 'Unknown Card')
            player_name = effect_data.get('player_name', 'Unknown Player')
            print(f"🗑️ {player_name} discarded {card_name}")
            return
            
        elif effect_type == 'gain_lore':
            amount = effect_data.get('amount', 0)
            target_name = getattr(effect_data.get('target'), 'name', 'Unknown') if effect_data.get('target') else 'Unknown'
            total_lore = getattr(effect_data.get('target'), 'lore', 0) if effect_data.get('target') else 0
            
            # Check if this came from an ability (source description contains ability info)
            if hasattr(message, 'step') and '🔮' in message.step:
                # Extract ability info from source description like "🔮 Minnie Mouse's DANCE-OFF"
                source_info = message.step.replace('🔮 ', '')
                print(f"⭐ {target_name} gained {amount} lore from {source_info} (total {total_lore} lore)")
            else:
                print(f"⭐ {target_name} gained {amount} lore (total {total_lore} lore)")
            return
            
        elif effect_type == 'draw_cards':
            count = effect_data.get('count', 1)
            drawn_cards = effect_data.get('drawn_cards', [])
            player = effect_data.get('target')  # The target is usually the player who drew
            player_name = player.name if player and hasattr(player, 'name') else "Player"
            
            if drawn_cards:
                # Show the actual card names that were drawn with full details
                valid_cards = [card for card in drawn_cards if card is not None]
                if len(valid_cards) == 1:
                    card_display = format_card_display(valid_cards[0])
                    print(f"📚 {player_name} drew {card_display}")
                elif len(valid_cards) > 1:
                    card_displays = [format_card_display(card) for card in valid_cards]
                    print(f"📚 {player_name} drew {len(valid_cards)} cards: {', '.join(card_displays)}")
                else:
                    print(f"📚 {player_name} drew {count} card{'s' if count != 1 else ''} (failed)")
            else:
                # Fallback to generic message
                card_text = "card" if count == 1 else "cards"
                print(f"📚 {player_name} drew {count} {card_text}")
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
            character = effect_data.get('character')
            player = effect_data.get('player')
            player_name = player.name if player and hasattr(player, 'name') else "Player"
            
            if character:
                character_display = format_card_display(character)
                print(f"✨ {player_name} readied {character_display}")
            else:
                # Fallback to character name if no full character object
                character_name = effect_data.get('character_name', 'Unknown Character')
                print(f"✨ {player_name} readied {character_name}")
            return
            
        elif effect_type == 'ready_ink':
            ink_count = effect_data.get('ink_count', 0)
            player = effect_data.get('player')
            player_name = player.name if (player and hasattr(player, 'name')) else 'Unknown Player'
            if ink_count > 0:
                print(f"💎 {player_name} readied {ink_count} ink")
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
            elif "quest" in effect_str.lower() and "quest" in source_desc.lower():
                # Handle quest messages specially 
                target = effect_data.get('target')
                if target and hasattr(target, 'controller') and target.controller:
                    player_name = target.controller.name
                    player_lore = getattr(target.controller, 'lore', 0)
                    character_lore = getattr(target, 'lore', 1)  # Default quest lore
                    character_display = format_card_display(target)
                    print(f"🏆 {player_name} quested with {character_display} for {character_lore} lore (now {player_lore} total)")
                else:
                    # Fallback to character name from source_desc
                    character_name = source_desc.replace(" quests", "").strip()
                    print(f"🏆 Quested with {character_name}")
            else:
                formatted_desc = f"📋 {effect_str} on {target_name}"
                if source_desc:
                    formatted_desc = f"{source_desc}: {formatted_desc}"
                print(formatted_desc)
            return
    
    # Handle conditional effects with structured data
    if step == "conditional_effect_applied" and hasattr(message, 'event_data'):
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
        
    elif step == "conditional_effect_removed" and hasattr(message, 'event_data'):
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
    
    # Handle additional effect types from _extract_effect_data
    if hasattr(message, 'event_data') and message.event_data and isinstance(message.event_data, dict):
        effect_type = message.event_data.get('type')
        
        if effect_type == 'phase_transition':
            # Handle phase transition effects - don't show as "played a card"
            previous_phase = message.event_data.get('previous_phase')
            new_phase = message.event_data.get('new_phase')
            player = message.event_data.get('player')
            player_name = player.name if player and hasattr(player, 'name') else "Unknown Player"
            
            if new_phase and hasattr(new_phase, 'value'):
                print(f"⚙️ {player_name} enters {new_phase.value} phase")
                # Print board state at the start of each ready phase
                if new_phase.value == 'ready' and game_state:
                    print_board_state(game_state)
            elif previous_phase and hasattr(previous_phase, 'value'):
                print(f"⚙️ {player_name} exits {previous_phase.value} phase")
            else:
                print(f"⚙️ {player_name} phase transition")
            return
        
        elif effect_type == 'ink_card':
            # Handle ink card effects
            card = message.event_data.get('card')
            player = message.event_data.get('player')
            player_name = player.name if player and hasattr(player, 'name') else "Unknown Player"
            
            if card:
                card_display = format_card_display(card)
                print(f"🔮 {player_name} inked {card_display}")
            else:
                # Fallback to card name if no full card object
                card_name = message.event_data.get('card_name', 'Unknown Card')
                print(f"🔮 {player_name} inked {card_name}")
            return
            
        elif effect_type == 'play_character':
            # Handle character play effects
            character = message.event_data.get('character')
            player = message.event_data.get('player')
            player_name = player.name if player and hasattr(player, 'name') else "Unknown Player"
            
            if character:
                character_display = format_card_display(character)
                print(f"🎭 {player_name} played {character_display}")
            else:
                # Fallback to character name if no full character object
                character_name = message.event_data.get('character_name', 'Unknown Character')
                print(f"🎭 {player_name} played {character_name}")
            return
    
    # Handle step-based display when no structured event_data is available
    if step and hasattr(step, 'value'):
        step_str = step.value.lower()
    elif step:
        step_str = str(step).lower()
    else:
        step_str = ""
    
    # Try to get additional context from message if available
    player_name = message.player.name if message.player else "Unknown Player"
    
    if "ability_triggered" in step_str:
        print(f"✨ Ability triggered")
    elif "character_readied" in step_str or "readied" in step_str:
        print(f"🔄 Character readied")
    elif step_str == "card_drawn":
        # Already handled by structured event_data above
        return
    elif "ink" in step_str:
        # Try to find ink action context
        if hasattr(message, 'event_data') and message.event_data:
            context = message.event_data.get('context', {})
            card = context.get('card')
            phase = context.get('phase')
            
            # Extract phase info if available
            phase_info = f" (during {phase.value} phase)" if phase and hasattr(phase, 'value') else ""
            
            if card and hasattr(card, 'name'):
                card_display = format_card_display(card)
                print(f"🔮 {player_name} inked {card_display}{phase_info}")
            else:
                print(f"🔮 {player_name} inked a card{phase_info}")
        else:
            print(f"🔮 {player_name} played ink")
    elif "play" in step_str:
        # Try to find play action context
        if hasattr(message, 'event_data') and message.event_data:
            context = message.event_data.get('context', {})
            card = context.get('card')
            phase = context.get('phase')
            
            # Extract phase info if available
            phase_info = f" (during {phase.value} phase)" if phase and hasattr(phase, 'value') else ""
            
            if card and hasattr(card, 'name'):
                print(f"🎭 {player_name} played {card.name}{phase_info}")
            else:
                print(f"🎭 {player_name} played a card{phase_info}")
        else:
            print(f"🎭 {player_name} played a card")
    elif "quest" in step_str:
        print(f"🏆 {player_name}'s character quested")
    elif "challenge" in step_str:
        # Try to find challenge context
        if hasattr(message, 'event_data') and message.event_data:
            context = message.event_data.get('context', {})
            attacker = context.get('attacker')
            defender = context.get('defender')
            damage_to_attacker = context.get('damage_to_attacker', 0)
            damage_to_defender = context.get('damage_to_defender', 0)
            
            if attacker and defender:
                attacker_display = format_card_display(attacker, include_owner=True)
                defender_display = format_card_display(defender, include_owner=True)
                
                damage_parts = []
                if damage_to_defender > 0:
                    defender_name = getattr(defender, 'name', 'Unknown') if defender else 'Unknown'
                    damage_parts.append(f"{defender_name} took {damage_to_defender} damage")
                if damage_to_attacker > 0:
                    attacker_name = getattr(attacker, 'name', 'Unknown') if attacker else 'Unknown'
                    damage_parts.append(f"{attacker_name} took {damage_to_attacker} damage")
                
                damage_text = f" ({', '.join(damage_parts)})" if damage_parts else ""
                print(f"⚔️ {attacker_display} challenged {defender_display}{damage_text}")
            else:
                print(f"⚔️ {player_name}'s character challenged")
        else:
            print(f"⚔️ {player_name}'s character challenged")
    elif "character_banished" in step_str:
        print(f"💀 Character banished")
    elif "card_discarded" in step_str:
        print(f"🗑️ Card discarded")
    elif "lore_gained" in step_str:
        print(f"⭐ Lore gained")
    elif "phase" in step_str:
        # Handle specific phase events
        if step_str in ["ready_phase", "set_phase", "draw_phase", "play_phase"]:
            phase_name = step_str.replace("_", " ").title()
            print(f"⚙️ {phase_name} ({player_name})")
        else:
            # Try to find phase context
            if hasattr(message, 'event_data') and message.event_data:
                context = message.event_data.get('context', {})
                previous_phase = context.get('previous_phase')
                new_phase = context.get('new_phase')
                
                if new_phase and hasattr(new_phase, 'value'):
                    print(f"⚙️ Phase change ({player_name}; {new_phase.value} phase)")
                elif previous_phase and hasattr(previous_phase, 'value'):
                    print(f"⚙️ Phase change ({player_name}; ending {previous_phase.value} phase)")
                else:
                    print(f"⚙️ Phase change ({player_name})")
            else:
                print(f"⚙️ Phase change ({player_name})")
    elif "turn_ended" in step_str:
        print(f"🔄 {player_name} ended turn")
    else:
        # Generic step display
        #print(f"📋 Game step: {step}")
        pass


def simulate_random_game():
    """Simulate a complete random game with real decks using message interface."""
    print("🎲 Starting Real Deck Lorcana Game (Message Interface)!")
    print("=" * 50)
    
    game_state = setup_game()
    engine = GameEngine(game_state)
    
    # Start the game
    engine.start_game()
    
    message_count = 0
    max_messages = 5000  # Safety limit
    last_turn_number = 0
    
    # Initialize move container outside loop
    move = None
    
    # DO NOT get initial message - let the loop handle it
    
    while message_count < max_messages:
        message_count += 1
        
        # Single call point for next_message - always at loop start
        message = engine.next_message(move)
        move = None  # Reset immediately after use
        
        # Handle different message types
        if isinstance(message, GameOverMessage):
            print(f"🏆 {message.reason}")
            break
            
        elif isinstance(message, ActionRequiredMessage):
            # Show turn transition if needed
            if game_state.turn_number != last_turn_number:
                last_turn_number = game_state.turn_number
                
            # Choose a move strategically
            move = choose_strategic_move(message)
            if move is None:
                print(f"❌ No legal moves for {message.player.name}, ending game")
                break
            # Move will be passed to next_message in the next iteration
            
        elif isinstance(message, StepExecutedMessage):
            # Display the step that was executed
            display_step_message(message, game_state)
            # No action needed - next message will be fetched at loop start
            
        elif isinstance(message, ChoiceRequiredMessage):
            # Handle player choice
            move = handle_choice_message(message)
            # Move will be passed to next_message in the next iteration
            
        else:
            # Handle any other message types (e.g., info messages)
            print(f"ℹ️  {message}")
    
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
    #random.seed()
    simulate_random_game()
