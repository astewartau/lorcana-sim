"""Turn management component for GameState."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game_state import GameState, Phase


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
    
    def can_perform_action(self, action: str, game_state: "GameState") -> bool:
        """Check if current player can perform the given action."""
        from ..game_state import Phase
        
        # Game over - no actions allowed
        if game_state.is_game_over():
            return False
        
        if game_state.current_phase == Phase.PLAY:
            return action in [
                "play_ink",
                "play_character",
                "play_action", 
                "play_item",
                "quest_character",
                "challenge_character",
                "sing_song",
                "activate_ability",
                "progress",
                "pass_turn"
            ]
        elif game_state.current_phase in [Phase.READY, Phase.SET, Phase.DRAW]:
            return action in ["progress", "pass_turn"]
        
        return False
    
    def record_action(self, action: str, game_state: "GameState") -> None:
        """Record an action for stalemate detection."""
        
        if action == "pass_turn":
            game_state.consecutive_passes += 1
        else:
            # Reset pass counter on any meaningful action
            game_state.consecutive_passes = 0