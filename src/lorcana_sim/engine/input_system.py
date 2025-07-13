"""Player input system for step-by-step game progression."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

from .step_system import StepType, PlayerInput, GameStep
from ..models.cards.base_card import Card
from ..models.cards.character_card import CharacterCard


class InputValidationError(Exception):
    """Raised when player input is invalid."""
    pass


class InputProvider(ABC):
    """Abstract base class for providing player input."""
    
    @abstractmethod
    def get_choice(self, prompt: str, options: List[Any], constraints: Dict[str, Any] = None) -> Any:
        """Get a choice from available options."""
        pass
    
    @abstractmethod
    def get_selection(self, prompt: str, targets: List[Any], 
                     min_count: int = 1, max_count: int = 1,
                     constraints: Dict[str, Any] = None) -> List[Any]:
        """Get a selection of targets."""
        pass
    
    @abstractmethod
    def get_confirmation(self, prompt: str, default: bool = False) -> bool:
        """Get a confirmation (yes/no)."""
        pass


class MockInputProvider(InputProvider):
    """Mock input provider for testing - always returns first valid option."""
    
    def get_choice(self, prompt: str, options: List[Any], constraints: Dict[str, Any] = None) -> Any:
        if not options:
            raise InputValidationError("No options available for choice")
        return options[0]
    
    def get_selection(self, prompt: str, targets: List[Any], 
                     min_count: int = 1, max_count: int = 1,
                     constraints: Dict[str, Any] = None) -> List[Any]:
        if len(targets) < min_count:
            raise InputValidationError(f"Not enough targets available (need {min_count}, have {len(targets)})")
        # Return minimum required count, starting from first item
        return targets[:min_count]
    
    def get_confirmation(self, prompt: str, default: bool = False) -> bool:
        return default


class QueuedInputProvider(InputProvider):
    """Input provider that uses pre-queued responses."""
    
    def __init__(self, queued_inputs: List[Any] = None):
        self.queued_inputs = queued_inputs or []
        self.input_index = 0
    
    def queue_input(self, input_value: Any) -> None:
        """Queue an input value."""
        self.queued_inputs.append(input_value)
    
    def queue_inputs(self, input_values: List[Any]) -> None:
        """Queue multiple input values."""
        self.queued_inputs.extend(input_values)
    
    def _get_next_input(self) -> Any:
        """Get the next queued input."""
        if self.input_index >= len(self.queued_inputs):
            raise InputValidationError("No more queued inputs available")
        
        value = self.queued_inputs[self.input_index]
        self.input_index += 1
        return value
    
    def get_choice(self, prompt: str, options: List[Any], constraints: Dict[str, Any] = None) -> Any:
        choice = self._get_next_input()
        if choice not in options:
            raise InputValidationError(f"Invalid choice: {choice} not in {options}")
        return choice
    
    def get_selection(self, prompt: str, targets: List[Any], 
                     min_count: int = 1, max_count: int = 1,
                     constraints: Dict[str, Any] = None) -> List[Any]:
        selection = self._get_next_input()
        if not isinstance(selection, list):
            selection = [selection]
        
        if len(selection) < min_count or len(selection) > max_count:
            raise InputValidationError(f"Invalid selection count: {len(selection)} (need {min_count}-{max_count})")
        
        for item in selection:
            if item not in targets:
                raise InputValidationError(f"Invalid selection: {item} not in targets")
        
        return selection
    
    def get_confirmation(self, prompt: str, default: bool = False) -> bool:
        value = self._get_next_input()
        if not isinstance(value, bool):
            raise InputValidationError(f"Invalid confirmation value: {value} (expected bool)")
        return value


@dataclass
class InputRequest:
    """Represents a request for player input."""
    request_id: str
    player_id: str
    step_id: str
    input_type: StepType
    prompt: str
    options: List[Any]
    constraints: Dict[str, Any]
    timeout_seconds: Optional[int] = None


class InputManager:
    """Manages player input for the step-by-step system."""
    
    def __init__(self):
        self.input_providers: Dict[str, InputProvider] = {}
        self.pending_requests: Dict[str, InputRequest] = {}
        self.input_validators: Dict[StepType, Callable] = {}
        
    def register_input_provider(self, player_id: str, provider: InputProvider) -> None:
        """Register an input provider for a player."""
        self.input_providers[player_id] = provider
    
    def register_input_validator(self, input_type: StepType, validator: Callable) -> None:
        """Register a validator for a specific input type."""
        self.input_validators[input_type] = validator
    
    def request_input(self, player_id: str, step: GameStep) -> Any:
        """Request input from a player for a step."""
        if not step.player_input:
            raise ValueError("Step does not require input")
        
        provider = self.input_providers.get(player_id)
        if not provider:
            raise ValueError(f"No input provider registered for player {player_id}")
        
        input_request = step.player_input
        
        try:
            if input_request.input_type == StepType.CHOICE:
                result = provider.get_choice(
                    input_request.prompt, 
                    input_request.options, 
                    input_request.constraints
                )
            elif input_request.input_type == StepType.SELECTION:
                min_count = input_request.constraints.get('min_count', 1)
                max_count = input_request.constraints.get('max_count', 1)
                result = provider.get_selection(
                    input_request.prompt,
                    input_request.options,
                    min_count,
                    max_count,
                    input_request.constraints
                )
            elif input_request.input_type == StepType.CONFIRMATION:
                default = input_request.constraints.get('default', False)
                result = provider.get_confirmation(input_request.prompt, default)
            else:
                raise ValueError(f"Unsupported input type: {input_request.input_type}")
            
            # Validate the input
            if input_request.input_type in self.input_validators:
                validator = self.input_validators[input_request.input_type]
                if not validator(result, input_request):
                    raise InputValidationError(f"Input validation failed for {result}")
            
            return result
            
        except Exception as e:
            raise InputValidationError(f"Failed to get input: {str(e)}")


class AbilityInputBuilder:
    """Helper class for building input requests for abilities."""
    
    @staticmethod
    def create_choice_input(prompt: str, options: List[Any], 
                           constraints: Dict[str, Any] = None) -> PlayerInput:
        """Create a choice input request."""
        return PlayerInput(
            input_type=StepType.CHOICE,
            prompt=prompt,
            options=options,
            constraints=constraints or {}
        )
    
    @staticmethod
    def create_target_selection_input(prompt: str, targets: List[Any],
                                    min_count: int = 1, max_count: int = 1,
                                    filter_fn: Callable[[Any], bool] = None) -> PlayerInput:
        """Create a target selection input request."""
        if filter_fn:
            targets = [t for t in targets if filter_fn(t)]
        
        constraints = {
            'min_count': min_count,
            'max_count': max_count
        }
        
        return PlayerInput(
            input_type=StepType.SELECTION,
            prompt=prompt,
            options=targets,
            constraints=constraints
        )
    
    @staticmethod
    def create_character_selection_input(prompt: str, characters: List[CharacterCard],
                                       min_count: int = 1, max_count: int = 1,
                                       friendly_only: bool = False,
                                       can_quest: bool = False) -> PlayerInput:
        """Create a character selection input request with common filters."""
        constraints = {
            'min_count': min_count,
            'max_count': max_count,
            'friendly_only': friendly_only,
            'can_quest': can_quest
        }
        
        # Apply filters
        filtered_characters = characters
        if friendly_only:
            # This would need access to game state to determine friendly characters
            pass
        if can_quest:
            filtered_characters = [c for c in filtered_characters if c.can_quest()]
        
        return PlayerInput(
            input_type=StepType.SELECTION,
            prompt=prompt,
            options=filtered_characters,
            constraints=constraints
        )
    
    @staticmethod
    def create_card_choice_input(prompt: str, cards: List[Card],
                               card_type: str = None) -> PlayerInput:
        """Create a card choice input request."""
        constraints = {}
        if card_type:
            constraints['card_type'] = card_type
            cards = [c for c in cards if c.card_type.value == card_type]
        
        return PlayerInput(
            input_type=StepType.CHOICE,
            prompt=prompt,
            options=cards,
            constraints=constraints
        )
    
    @staticmethod
    def create_confirmation_input(prompt: str, default: bool = False) -> PlayerInput:
        """Create a confirmation input request."""
        return PlayerInput(
            input_type=StepType.CONFIRMATION,
            prompt=prompt,
            options=[True, False],
            constraints={'default': default}
        )