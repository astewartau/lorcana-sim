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
        
        # NOTE: Ink drying is now handled by event-driven DryInkEffect scheduled during character play.
        # No need to manually update dry status - it's handled during each player's ready phase.
        
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
        
        # NOTE: Ink drying is now handled by event-driven DryInkEffect scheduled during character play.
        # Characters start with wet ink (is_dry=False) and DryInkEffect sets is_dry=True during ready phase.
        # This replaces the old turn_played calculation system for better testability and visibility.
        
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
        """Determine what should happen in the draw step WITHOUT executing it.
        
        Returns:
            List of event data for draw events that should occur.
        """
        from ....engine.event_system import GameEvent
        
        current_player = game_state.current_player
        draw_events = []
        
        # Determine if card should be drawn (skip on first turn for first player)
        should_draw = not (game_state.turn_number == 1 and 
                          game_state.current_player_index == 0 and 
                          not game_state.first_turn_draw_skipped)
        
        if should_draw:
            # DON'T execute the draw - just indicate that a draw should happen
            # Check if deck is empty to know if draw will fail
            if len(current_player.deck) > 0:
                draw_events.append({
                    'event': GameEvent.CARD_DRAWN,
                    'context': {
                        'player_name': current_player.name,
                        'should_draw': True
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
    
    # NOTE: _update_character_dry_status_except_current method removed.
    # Ink drying is now handled by event-driven DryInkEffect system.