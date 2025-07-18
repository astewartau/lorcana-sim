"""Turn management component for GameState."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState, GameAction, Phase


class TurnManagementComponent:
    """Handles turn-related operations for the game state."""
    
    def can_play_ink(self, game_state: "GameState") -> bool:
        """Check if current player can play ink."""
        from ..game_state import Phase
        return not game_state.ink_played_this_turn and game_state.current_phase == Phase.PLAY
    
    def has_character_acted_this_turn(self, character_id: int, game_state: "GameState") -> bool:
        """Check if a character has already acted this turn."""
        return character_id in game_state.characters_acted_this_turn
    
    def mark_character_acted(self, character_id: int, game_state: "GameState") -> None:
        """Mark that a character has acted this turn."""
        if character_id not in game_state.characters_acted_this_turn:
            game_state.characters_acted_this_turn.append(character_id)
    
    def can_perform_action(self, action: "GameAction", game_state: "GameState") -> bool:
        """Check if current player can perform the given action."""
        from ..game_state import Phase, GameAction
        
        # Game over - no actions allowed
        if game_state.is_game_over():
            return False
        
        if game_state.current_phase == Phase.PLAY:
            return action in [
                GameAction.PLAY_INK,
                GameAction.PLAY_CHARACTER,
                GameAction.PLAY_ACTION, 
                GameAction.PLAY_ITEM,
                GameAction.QUEST_CHARACTER,
                GameAction.CHALLENGE_CHARACTER,
                GameAction.SING_SONG,
                GameAction.ACTIVATE_ABILITY,
                GameAction.PROGRESS,
                GameAction.PASS_TURN
            ]
        elif game_state.current_phase in [Phase.READY, Phase.SET, Phase.DRAW]:
            return action in [GameAction.PROGRESS, GameAction.PASS_TURN]
        
        return False
    
    def record_action(self, action: "GameAction", game_state: "GameState") -> None:
        """Record an action for stalemate detection."""
        from ..game_state import GameAction
        
        if action == GameAction.PASS_TURN:
            game_state.consecutive_passes += 1
        else:
            # Reset pass counter on any meaningful action
            game_state.consecutive_passes = 0