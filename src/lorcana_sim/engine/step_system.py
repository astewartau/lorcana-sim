"""Step-by-step game progression system for interactive gameplay."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
import json
import copy


class ExecutionMode(Enum):
    """Execution modes for the step-by-step system."""
    MANUAL = "manual"  # Every step requires manual advancement
    PAUSE_ON_INPUT = "pause_on_input"  # Auto-advance except when input required


class StepType(Enum):
    """Types of steps in the progression system."""
    AUTOMATIC = "automatic"  # No user input required
    CHOICE = "choice"  # User must make a choice
    SELECTION = "selection"  # User must select targets
    CONFIRMATION = "confirmation"  # User must confirm action


class StepStatus(Enum):
    """Status of a step in execution."""
    PENDING = "pending"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class PlayerInput:
    """Represents required player input for a step."""
    input_type: StepType
    prompt: str
    options: List[Any] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'input_type': self.input_type.value,
            'prompt': self.prompt,
            'options': [self._serialize_option(opt) for opt in self.options],
            'constraints': self.constraints,
            'timeout_seconds': self.timeout_seconds
        }
    
    def _serialize_option(self, option: Any) -> Dict[str, Any]:
        """Serialize an option for JSON."""
        if hasattr(option, 'name'):
            return {'type': 'card', 'name': option.name, 'id': getattr(option, 'id', None)}
        elif hasattr(option, '__dict__'):
            return {'type': 'object', 'repr': str(option)}
        else:
            return {'type': 'primitive', 'value': option}


@dataclass
class GameStep:
    """Represents a single step in game progression."""
    step_id: str
    step_type: StepType
    description: str
    execute_fn: Callable[[], Any]
    player_input: Optional[PlayerInput] = None
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    
    def requires_input(self) -> bool:
        """Check if this step requires player input."""
        return self.step_type != StepType.AUTOMATIC
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for serialization (excluding functions)."""
        return {
            'step_id': self.step_id,
            'step_type': self.step_type.value,
            'description': self.description,
            'status': self.status.value,
            'result': str(self.result) if self.result is not None else None,
            'error': self.error,
            'player_input': self.player_input.to_dict() if self.player_input else None
        }


class StepExecutor(ABC):
    """Abstract base class for step execution."""
    
    @abstractmethod
    def execute_step(self, step: GameStep, input_data: Optional[Any] = None) -> Any:
        """Execute a step with optional input data."""
        pass


class GameStepQueue:
    """Queue system for managing game steps."""
    
    def __init__(self, execution_mode: ExecutionMode = ExecutionMode.PAUSE_ON_INPUT):
        self.execution_mode = execution_mode
        self.steps: List[GameStep] = []
        self.current_step_index = 0
        self.is_paused = False
        self.waiting_for_input = False
        self.input_providers: Dict[str, Callable] = {}
        
    def add_step(self, step: GameStep) -> None:
        """Add a step to the queue."""
        self.steps.append(step)
    
    def add_steps(self, steps: List[GameStep]) -> None:
        """Add multiple steps to the queue."""
        self.steps.extend(steps)
    
    def get_current_step(self) -> Optional[GameStep]:
        """Get the current step being executed."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def get_pending_steps(self) -> List[GameStep]:
        """Get all pending steps."""
        return [step for step in self.steps if step.status == StepStatus.PENDING]
    
    def has_pending_steps(self) -> bool:
        """Check if there are pending steps."""
        return self.current_step_index < len(self.steps)
    
    def advance_step(self) -> Optional[GameStep]:
        """Advance to the next step."""
        if self.current_step_index < len(self.steps):
            current = self.steps[self.current_step_index]
            if current.status == StepStatus.PENDING:
                current.status = StepStatus.COMPLETED
            self.current_step_index += 1
            
        return self.get_current_step()
    
    def pause(self) -> None:
        """Pause step execution."""
        self.is_paused = True
    
    def resume(self) -> None:
        """Resume step execution."""
        self.is_paused = False
        self.waiting_for_input = False
    
    def cancel_current_step(self) -> None:
        """Cancel the current step."""
        current = self.get_current_step()
        if current:
            current.status = StepStatus.CANCELLED
            self.advance_step()
    
    def clear(self) -> None:
        """Clear all steps from the queue."""
        self.steps.clear()
        self.current_step_index = 0
        self.is_paused = False
        self.waiting_for_input = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert queue state to dictionary for serialization."""
        return {
            'execution_mode': self.execution_mode.value,
            'current_step_index': self.current_step_index,
            'is_paused': self.is_paused,
            'waiting_for_input': self.waiting_for_input,
            'steps': [step.to_dict() for step in self.steps]
        }


class StepProgressionEngine:
    """Main engine for step-by-step game progression."""
    
    def __init__(self, execution_mode: ExecutionMode = ExecutionMode.PAUSE_ON_INPUT):
        self.step_queue = GameStepQueue(execution_mode)
        self.input_handlers: Dict[StepType, Callable] = {}
        self.step_executors: List[StepExecutor] = []
        self.step_listeners: List[Callable[[GameStep], None]] = []
        
    def register_input_handler(self, step_type: StepType, handler: Callable) -> None:
        """Register a handler for a specific type of input."""
        self.input_handlers[step_type] = handler
    
    def register_step_executor(self, executor: StepExecutor) -> None:
        """Register a step executor."""
        self.step_executors.append(executor)
    
    def add_step_listener(self, listener: Callable[[GameStep], None]) -> None:
        """Add a listener for step events."""
        self.step_listeners.append(listener)
    
    def queue_steps(self, steps: Union[GameStep, List[GameStep]]) -> None:
        """Queue one or more steps for execution."""
        if isinstance(steps, GameStep):
            self.step_queue.add_step(steps)
        else:
            self.step_queue.add_steps(steps)
    
    def execute_next_step(self, input_data: Optional[Any] = None) -> Optional[GameStep]:
        """Execute the next step in the queue."""
        if not self.step_queue.has_pending_steps():
            return None
        
        current_step = self.step_queue.get_current_step()
        if not current_step:
            return None
        
        # Check if we're waiting for input
        if (current_step.status == StepStatus.WAITING_FOR_INPUT and 
            input_data is None):
            return current_step
        
        try:
            # Execute the step
            if current_step.requires_input():
                if input_data is None:
                    # Mark as waiting for input and pause if needed
                    current_step.status = StepStatus.WAITING_FOR_INPUT
                    if self.step_queue.execution_mode == ExecutionMode.PAUSE_ON_INPUT:
                        self.step_queue.pause()
                        self.step_queue.waiting_for_input = True
                    return current_step
                else:
                    # Execute with input
                    result = self._execute_step_with_input(current_step, input_data)
            else:
                # Execute without input
                result = self._execute_step_without_input(current_step)
            
            current_step.result = result
            current_step.status = StepStatus.COMPLETED
            
            # Notify listeners
            for listener in self.step_listeners:
                listener(current_step)
            
            # Advance to next step
            next_step = self.step_queue.advance_step()
            
            # Auto-advance if in pause-on-input mode and next step doesn't need input
            if (self.step_queue.execution_mode == ExecutionMode.PAUSE_ON_INPUT and
                next_step and not next_step.requires_input()):
                return self.execute_next_step()
            
            return next_step
            
        except Exception as e:
            current_step.error = str(e)
            current_step.status = StepStatus.CANCELLED
            return self.step_queue.advance_step()
    
    def _execute_step_with_input(self, step: GameStep, input_data: Any) -> Any:
        """Execute a step that requires input."""
        if step.step_type in self.input_handlers:
            handler = self.input_handlers[step.step_type]
            return handler(step, input_data)
        else:
            # Default execution with input passed to function
            return step.execute_fn(input_data)
    
    def _execute_step_without_input(self, step: GameStep) -> Any:
        """Execute a step that doesn't require input."""
        return step.execute_fn()
    
    def continue_execution(self) -> List[GameStep]:
        """Continue execution until paused or completed."""
        executed_steps = []
        
        while (self.step_queue.has_pending_steps() and 
               not self.step_queue.is_paused and 
               not self.step_queue.waiting_for_input):
            
            current_step = self.step_queue.get_current_step()
            if not current_step:
                break
                
            # Execute the current step
            next_step = self.execute_next_step()
            executed_steps.append(current_step)
                
            # In manual mode, break after executing one step
            if self.step_queue.execution_mode == ExecutionMode.MANUAL:
                break
                
            # Break if current step is waiting for input
            if current_step.status == StepStatus.WAITING_FOR_INPUT:
                break
        
        return executed_steps
    
    def provide_input(self, input_data: Any) -> Optional[GameStep]:
        """Provide input for the current step waiting for input."""
        current_step = self.step_queue.get_current_step()
        if (current_step and 
            current_step.status == StepStatus.WAITING_FOR_INPUT):
            self.step_queue.resume()
            next_step = self.execute_next_step(input_data)
            
            # In pause-on-input mode, continue execution until next input needed
            if self.step_queue.execution_mode == ExecutionMode.PAUSE_ON_INPUT:
                self.continue_execution()
            
            return self.get_current_step()
        return None
    
    def get_current_step(self) -> Optional[GameStep]:
        """Get the current step."""
        return self.step_queue.get_current_step()
    
    def get_queue_state(self) -> Dict[str, Any]:
        """Get the current state of the step queue."""
        return self.step_queue.to_dict()
    
    def pause(self) -> None:
        """Pause execution."""
        self.step_queue.pause()
    
    def resume(self) -> None:
        """Resume execution."""
        self.step_queue.resume()
    
    def clear_queue(self) -> None:
        """Clear the step queue."""
        self.step_queue.clear()