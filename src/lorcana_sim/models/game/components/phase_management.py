"""Phase management component for GameState."""

from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState, Phase


class PhaseManagementComponent:
    """Handles phase-related operations for the game state."""
    
    def advance_phase(self, game_state: "GameState") -> List[Any]:
        """Advance to the next phase, returning effects to queue."""
        from ..game_state import Phase
        from ....models.abilities.composable.effects import TriggerPhaseTransition
        
        effects_to_queue = []
        current_phase = game_state.current_phase
        
        if current_phase == Phase.READY:
            effects_to_queue.append(TriggerPhaseTransition(Phase.READY, Phase.SET))
        elif current_phase == Phase.SET:
            effects_to_queue.append(TriggerPhaseTransition(Phase.SET, Phase.DRAW))
        elif current_phase == Phase.DRAW:
            effects_to_queue.append(TriggerPhaseTransition(Phase.DRAW, Phase.PLAY))
        elif current_phase == Phase.PLAY:
            # End turn, move to next player
            end_turn_effects = self.end_turn(game_state)
            effects_to_queue.extend(end_turn_effects)
        
        return effects_to_queue
    
    def end_turn(self, game_state: "GameState") -> List[Any]:
        """End current player's turn and start next player's turn.
        
        Returns list of effects to be queued by the calling system.
        """
        from ....models.abilities.composable.effects import ResetTurnState
        
        effects_to_queue = []
        
        # Queue turn state reset effect instead of direct manipulation
        reset_effect = ResetTurnState()
        effects_to_queue.append(reset_effect)
        
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
        
        return effects_to_queue
    
    def ready_step(self, game_state: "GameState") -> List[Any]:
        """Return effects to queue for ready step.
        
        Returns:
            List of effects to be queued.
        """
        from ....models.abilities.composable.effects import ReadyCharacter, ReadyInk, ResetTurnState
        
        current_player = game_state.current_player
        effects_to_queue = []
        
        # Queue turn state reset effect
        effects_to_queue.append(ResetTurnState())
        
        # Character readying effects
        exerted_characters = [char for char in current_player.characters_in_play if char.exerted]
        for character in exerted_characters:
            effects_to_queue.append(ReadyCharacter(character))
        
        # Item readying effects
        exerted_items = [item for item in current_player.items_in_play 
                        if hasattr(item, 'exerted') and item.exerted]
        for item in exerted_items:
            effects_to_queue.append(ReadyCharacter(item))  # Reuse same effect
        
        # Ink readying effect
        exerted_ink_count = sum(1 for card in current_player.inkwell if card.exerted)
        if exerted_ink_count > 0:
            effects_to_queue.append(ReadyInk())
        
        return effects_to_queue
    
    def set_step(self, game_state: "GameState") -> List[Any]:
        """Return effects to queue for set step.
        
        Returns:
            List of effects to be queued.
        """
        effects_to_queue = []
        
        # Currently no set phase effects, but structure for future expansion
        # Example future effects:
        # - Start-of-turn triggered abilities
        # - Ongoing effect resolutions
        # - Status effect processing
        
        return effects_to_queue
    
    def draw_step(self, game_state: "GameState") -> List[Any]:
        """Return effects to queue for draw step.
        
        Returns:
            List of effects to be queued.
        """
        from ....models.abilities.composable.effects import DrawCards
        
        effects_to_queue = []
        current_player = game_state.current_player
        
        # Check if should draw (skip first turn for first player)
        should_draw = not (game_state.turn_number == 1 and 
                          game_state.current_player_index == 0 and 
                          not game_state.first_turn_draw_skipped)
        
        if should_draw:
            # Queue mandatory draw (can be modified by abilities)
            effects_to_queue.append(DrawCards(1))
        else:
            # Mark first turn draw as skipped
            game_state.first_turn_draw_skipped = True
        
        return effects_to_queue
    
    # NOTE: _update_character_dry_status_except_current method removed.
    # Ink drying is now handled by event-driven DryInkEffect system.