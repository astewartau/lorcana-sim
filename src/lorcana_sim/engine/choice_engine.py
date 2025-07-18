"""Choice engine for handling player choice coordination and resolution."""

from typing import Dict, Any, Optional, List
from collections import deque
from .choice_system import GameChoiceManager, ChoiceContext
from .game_messages import StepExecutedMessage, MessageType
from .event_system import GameEvent
from ..models.abilities.composable.conditional_effects import ActivationZone


def create_event_data(event: GameEvent, **context) -> Dict[str, Any]:
    """Create standardized event_data structure."""
    return {
        'event': event,
        'context': context
    }


class ChoiceEngine:
    """Dedicated engine for player choice handling and resolution."""
    
    def __init__(self, game_state, choice_manager: GameChoiceManager):
        self.game_state = game_state
        self.choice_manager = choice_manager
        self.current_choice = None
        
    def resolve_choice(self, choice_id: str, option: str) -> None:
        """Resolve a player choice."""
        
        # Capture the last event timestamp before choice resolution
        last_event_before = getattr(self.game_state, 'last_event', None)
        timestamp_before = last_event_before.get('timestamp', -1) if last_event_before else -1
        
        # Set up event collection for composite effects
        if not hasattr(self.game_state, 'choice_events'):
            self.game_state.choice_events = []
        
        # Clear any previous choice events
        self.game_state.choice_events.clear()
        
        # Override the choice execution to ensure game state has choice_events
        original_provide_choice = self.choice_manager.provide_choice
        def wrapped_provide_choice(choice_id, selected_option):
            # Ensure choice_events is available during effect execution
            if not hasattr(self.game_state, 'choice_events'):
                self.game_state.choice_events = []
            
            # Also ensure the context in the current choice includes the correct game state and action queue
            if self.choice_manager.current_choice:
                context = self.choice_manager.current_choice.trigger_context.get('_choice_execution_context', {})
                context['game_state'] = self.game_state
                # Note: action_queue will be injected from the calling context
                self.choice_manager.current_choice.trigger_context['_choice_execution_context'] = context
                
            return original_provide_choice(choice_id, selected_option)
        
        # Temporarily replace the method
        self.choice_manager.provide_choice = wrapped_provide_choice
        
        try:
            success = self.choice_manager.provide_choice(choice_id, option)
        finally:
            # Restore original method
            self.choice_manager.provide_choice = original_provide_choice
            
        if not success:
            raise ValueError(f"Failed to resolve choice {choice_id} with option {option}")
    
    def queue_choice_event_message(self, event: dict, message_queue: deque) -> None:
        """Queue a message for a choice-triggered event."""
        
        event_type = event.get('type')
        player_name = event.get('player', 'Unknown')
        
        # Handle both enum objects and string values
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        
        if event_type_str == 'card_drawn':
            # Get player object - use current player if name matches, otherwise look up
            player = None
            if player_name == self.game_state.current_player.name:
                player = self.game_state.current_player
            elif player_name == self.game_state.players[0].name:
                player = self.game_state.players[0]
            elif player_name == self.game_state.players[1].name:
                player = self.game_state.players[1]
            
            # Queue draw event messages for choice-triggered draws
            cards_drawn = event.get('cards_drawn', [])
            for card in cards_drawn:
                draw_message = StepExecutedMessage(
                    type=MessageType.STEP_EXECUTED,
                    player=self.game_state.current_player,
                    step=GameEvent.CARD_DRAWN,
                    event_data=create_event_data(
                        GameEvent.CARD_DRAWN,
                        player=player,
                        card=card
                    )
                )
                message_queue.append(draw_message)
        elif event_type_str == 'card_discarded':
            # Get player object - use current player if name matches, otherwise look up
            player = None
            if player_name == self.game_state.current_player.name:
                player = self.game_state.current_player
            elif player_name == self.game_state.players[0].name:
                player = self.game_state.players[0]
            elif player_name == self.game_state.players[1].name:
                player = self.game_state.players[1]
                
            # Queue discard event messages for choice-triggered discards
            card = event.get('additional_data', {}).get('card')  # Try to get whole card object
            from_zone = event.get('additional_data', {}).get('from_zone', ActivationZone.HAND)  # Default to hand
            to_zone = ActivationZone.DISCARD  # Discarding always goes to discard pile
            discard_message = StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step=GameEvent.CARD_DISCARDED,
                event_data=create_event_data(
                    GameEvent.CARD_DISCARDED,
                    player=player,
                    card=card,
                    from_zone=from_zone,
                    to_zone=to_zone
                )
            )
            message_queue.append(discard_message)
        elif event_type_str == 'lore_gained':
            # Get player object - use current player if name matches, otherwise look up
            player = None
            if player_name == self.game_state.current_player.name:
                player = self.game_state.current_player
            elif player_name == self.game_state.players[0].name:
                player = self.game_state.players[0]
            elif player_name == self.game_state.players[1].name:
                player = self.game_state.players[1]
                
            # Queue lore gain event messages for choice-triggered lore gains
            lore_amount = event.get('additional_data', {}).get('lore_amount', 0)
            source = event.get('additional_data', {}).get('source')  # Source that caused the lore gain
            lore_message = StepExecutedMessage(
                type=MessageType.STEP_EXECUTED,
                player=self.game_state.current_player,
                step=GameEvent.LORE_GAINED,
                event_data=create_event_data(
                    GameEvent.LORE_GAINED,
                    player=player,
                    amount=lore_amount,
                    source=source
                )
            )
            message_queue.append(lore_message)
    
    def trigger_choice_events(self, event: GameEvent, context: Dict):
        """Handle choice-related event triggering."""
        # This method can be used to coordinate choice-related events
        # For now, it's a placeholder for future expansion
        pass
    
    def is_paused_for_choice(self) -> bool:
        """Check if the game is paused waiting for a player choice."""
        return self.choice_manager.is_game_paused()
    
    def get_current_choice(self) -> Optional[ChoiceContext]:
        """Get the current choice that needs player input."""
        return self.choice_manager.get_current_choice()
    
    def provide_player_choice(self, choice_id: str, selected_option: str) -> bool:
        """
        Provide a player's choice and continue game execution.
        
        Args:
            choice_id: ID of the choice being answered
            selected_option: ID of the selected option
            
        Returns:
            True if choice was valid and executed, False otherwise
        """
        return self.choice_manager.provide_choice(choice_id, selected_option)
    
    def get_choice_summary(self) -> Dict[str, Any]:
        """Get a summary of the current choice state for debugging/UI."""
        current_choice = self.get_current_choice()
        return {
            'is_paused': self.is_paused_for_choice(),
            'pending_choices': len(self.choice_manager.pending_choices),
            'current_choice': {
                'id': current_choice.choice_id if current_choice else None,
                'player': current_choice.player.name if current_choice and current_choice.player else None,
                'ability': current_choice.ability_name if current_choice else None,
                'prompt': current_choice.prompt if current_choice else None,
                'options': [opt.id for opt in current_choice.options] if current_choice else []
            } if current_choice else None
        }