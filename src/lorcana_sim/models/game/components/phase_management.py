"""Phase management component for GameState."""

from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState, Phase


class PhaseManagementComponent:
    """Handles phase-related operations for the game state."""
    
    def advance_phase(self, game_state: "GameState") -> None:
        """Advance to the next phase."""
        from ..game_state import Phase
        
        if game_state.current_phase == Phase.READY:
            game_state.current_phase = Phase.SET
        elif game_state.current_phase == Phase.SET:
            game_state.current_phase = Phase.DRAW
        elif game_state.current_phase == Phase.DRAW:
            game_state.current_phase = Phase.PLAY
        elif game_state.current_phase == Phase.PLAY:
            # End turn, move to next player
            self.end_turn(game_state)
    
    def end_turn(self, game_state: "GameState") -> None:
        """End current player's turn and start next player's turn."""
        # Reset turn state
        game_state.ink_played_this_turn = False
        game_state.card_drawn_this_turn = False
        game_state.actions_this_turn.clear()
        game_state.characters_acted_this_turn.clear()
        
        # Move to next player
        game_state.current_player_index = (game_state.current_player_index + 1) % len(game_state.players)
        
        # If back to first player, increment turn number
        if game_state.current_player_index == 0:
            game_state.turn_number += 1
        
        # Update character dry status after turn changes (but not for current player - they'll update in ready phase)
        self._update_character_dry_status_except_current(game_state)
        
        # Start ready phase for new player (but don't execute ready_step yet)
        from ..game_state import Phase
        game_state.current_phase = Phase.READY
    
    def ready_step(self, game_state: "GameState") -> List[Dict[str, Any]]:
        """Execute the ready step (ready all cards and start turn).
        
        Returns:
            List of event data for items that were readied.
        """
        from ....engine.event_system import GameEvent
        from ....models.abilities.composable import ReadyInk
        
        current_player = game_state.current_player
        readied_items = []
        
        # Get list of exerted characters before readying
        exerted_characters = [char for char in current_player.characters_in_play if char.exerted]
        
        # Update dry status for current player's characters (happens during ready phase)
        for char in current_player.characters_in_play:
            if char.turn_played is not None:
                # Ink dries at start of owner's next turn
                old_dry_status = char.is_dry
                char.is_dry = game_state.turn_number > char.turn_played
                # Track characters that just dried
                if not old_dry_status and char.is_dry and not char.exerted:
                    readied_items.append({
                        'event': GameEvent.CHARACTER_READIED,
                        'context': {
                            'character_name': char.name,
                            'reason': 'ink_dried'
                        }
                    })
            else:
                # Character wasn't played this game (already dry)
                char.is_dry = True
        
        # Start the turn (reset ink usage, ready characters)
        current_player.start_turn()
        
        # Track which characters were readied from exerted state
        for char in exerted_characters:
            readied_items.append({
                'event': GameEvent.CHARACTER_READIED,
                'context': {
                    'character_name': char.name,
                    'character': char,  # Include full character object for detailed display
                    'reason': 'ready_step'
                }
            })
        
        # Ready all items
        exerted_items = [item for item in current_player.items_in_play 
                        if hasattr(item, 'exerted') and item.exerted]
        for item in exerted_items:
            item.exerted = False
            readied_items.append({
                'event': GameEvent.CHARACTER_READIED,  # Using CHARACTER_READIED for items too
                'context': {
                    'item_name': item.name,
                    'item_type': 'item',
                    'reason': 'ready_step'
                }
            })
        
        # Count exerted ink cards
        exerted_ink_count = sum(1 for card in current_player.inkwell if card.exerted)
        
        # If there are exerted ink cards, queue a ReadyInk effect
        if exerted_ink_count > 0:
            # Create and apply the ReadyInk effect
            ready_ink_effect = ReadyInk()  # No parameter = ready all
            context = {
                'game_state': game_state,
                'player': current_player,
                'ability_name': 'Ready Phase'
            }
            
            # Apply the effect
            ready_ink_effect.apply(current_player, context)
            
            # Get the events from the effect
            ink_events = ready_ink_effect.get_events(current_player, context, None)
            
            # Add ink ready events to the list
            for event in ink_events:
                event_data = {
                    'event': event['type'],
                    'context': event['additional_data']
                }
                readied_items.append(event_data)
        
        return readied_items
    
    def set_step(self, game_state: "GameState") -> List[Dict[str, Any]]:
        """Execute the set step (resolve start-of-turn effects).
        
        Returns:
            List of event data for set step events that occurred.
        """
        # Handle any start-of-turn triggered abilities
        # TODO: Implement start-of-turn ability resolution here
        set_events = []
        
        # Currently no set phase effects, but structure for future expansion
        # Example future effects:
        # - Start-of-turn triggered abilities
        # - Ongoing effect resolutions
        # - Status effect processing
        
        return set_events
    
    def draw_step(self, game_state: "GameState") -> List[Dict[str, Any]]:
        """Execute the draw step (draw a card).
        
        Returns:
            List of event data for draw events that occurred.
        """
        from ....engine.event_system import GameEvent
        
        current_player = game_state.current_player
        draw_events = []
        
        # Draw card (skip on first turn for first player)
        should_draw = not (game_state.turn_number == 1 and 
                          game_state.current_player_index == 0 and 
                          not game_state.first_turn_draw_skipped)
        
        if should_draw:
            drawn_card = current_player.draw_card()
            if drawn_card:
                draw_events.append({
                    'event': GameEvent.CARD_DRAWN,
                    'context': {
                        'player_name': current_player.name,
                        'card_name': drawn_card.name
                    }
                })
            else:
                draw_events.append({
                    'event': GameEvent.CARD_DRAWN,
                    'context': {
                        'player_name': current_player.name,
                        'draw_failed': True,
                        'reason': 'empty_deck'
                    }
                })
        elif game_state.turn_number == 1 and game_state.current_player_index == 0:
            game_state.first_turn_draw_skipped = True
            draw_events.append({
                'event': GameEvent.DRAW_STEP,
                'context': {
                    'player_name': current_player.name,
                    'action': 'skipped',
                    'reason': 'first_turn'
                }
            })
        
        return draw_events
    
    def _update_character_dry_status_except_current(self, game_state: "GameState") -> None:
        """Update dry status for all characters except current player (they update during ready phase)."""
        current_player = game_state.current_player
        for player in game_state.players:
            if player != current_player:
                for char in player.characters_in_play:
                    if char.turn_played is None:
                        # Character wasn't played this game (already dry)
                        char.is_dry = True