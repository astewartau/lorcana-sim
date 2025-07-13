"""Tests for the step-by-step game progression system."""

import pytest
from unittest.mock import Mock, patch
from src.lorcana_sim.engine.step_system import (
    StepProgressionEngine, GameStep, StepType, ExecutionMode, 
    StepStatus, PlayerInput, GameStepQueue
)
from src.lorcana_sim.engine.input_system import (
    InputManager, MockInputProvider, QueuedInputProvider, 
    AbilityInputBuilder, InputValidationError
)
from src.lorcana_sim.engine.state_serializer import (
    GameStateSerializer, SnapshotManager, GameStateSnapshot
)


class TestGameStepQueue:
    """Test the game step queue functionality."""
    
    def test_queue_initialization(self):
        """Test queue initialization with different modes."""
        queue = GameStepQueue(ExecutionMode.MANUAL)
        assert queue.execution_mode == ExecutionMode.MANUAL
        assert len(queue.steps) == 0
        assert queue.current_step_index == 0
        assert not queue.is_paused
        assert not queue.waiting_for_input
    
    def test_add_steps(self):
        """Test adding steps to the queue."""
        queue = GameStepQueue()
        
        step1 = GameStep(
            step_id="test_1",
            step_type=StepType.AUTOMATIC,
            description="Test step 1",
            execute_fn=lambda: "result1"
        )
        step2 = GameStep(
            step_id="test_2",
            step_type=StepType.CHOICE,
            description="Test step 2",
            execute_fn=lambda choice: f"result2_{choice}"
        )
        
        queue.add_step(step1)
        queue.add_steps([step2])
        
        assert len(queue.steps) == 2
        assert queue.steps[0] == step1
        assert queue.steps[1] == step2
    
    def test_get_current_step(self):
        """Test getting the current step."""
        queue = GameStepQueue()
        
        # No steps - should return None
        assert queue.get_current_step() is None
        
        step = GameStep(
            step_id="test",
            step_type=StepType.AUTOMATIC,
            description="Test step",
            execute_fn=lambda: "result"
        )
        queue.add_step(step)
        
        # Should return the first step
        assert queue.get_current_step() == step
        
        # Advance and check
        queue.advance_step()
        assert queue.get_current_step() is None
    
    def test_advance_step(self):
        """Test advancing through steps."""
        queue = GameStepQueue()
        
        step1 = GameStep("test_1", StepType.AUTOMATIC, "Test 1", lambda: "1")
        step2 = GameStep("test_2", StepType.AUTOMATIC, "Test 2", lambda: "2")
        queue.add_steps([step1, step2])
        
        # Start at step 1
        current = queue.get_current_step()
        assert current == step1
        assert current.status == StepStatus.PENDING
        
        # Advance to step 2
        next_step = queue.advance_step()
        assert next_step == step2
        assert step1.status == StepStatus.COMPLETED
        assert queue.current_step_index == 1
        
        # Advance past end
        final = queue.advance_step()
        assert final is None
        assert queue.current_step_index == 2
    
    def test_pause_resume(self):
        """Test pausing and resuming execution."""
        queue = GameStepQueue()
        
        assert not queue.is_paused
        
        queue.pause()
        assert queue.is_paused
        
        queue.resume()
        assert not queue.is_paused
        assert not queue.waiting_for_input


class TestStepProgressionEngine:
    """Test the step progression engine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = StepProgressionEngine(ExecutionMode.MANUAL)
        assert engine.step_queue.execution_mode == ExecutionMode.MANUAL
        assert len(engine.input_handlers) == 0
        assert len(engine.step_executors) == 0
        assert len(engine.step_listeners) == 0
    
    def test_queue_single_step(self):
        """Test queuing a single step."""
        engine = StepProgressionEngine()
        
        step = GameStep(
            step_id="test",
            step_type=StepType.AUTOMATIC,
            description="Test step",
            execute_fn=lambda: "success"
        )
        
        engine.queue_steps(step)
        assert len(engine.step_queue.steps) == 1
        assert engine.step_queue.get_current_step() == step
    
    def test_queue_multiple_steps(self):
        """Test queuing multiple steps."""
        engine = StepProgressionEngine()
        
        steps = [
            GameStep("test_1", StepType.AUTOMATIC, "Test 1", lambda: "1"),
            GameStep("test_2", StepType.AUTOMATIC, "Test 2", lambda: "2"),
            GameStep("test_3", StepType.AUTOMATIC, "Test 3", lambda: "3")
        ]
        
        engine.queue_steps(steps)
        assert len(engine.step_queue.steps) == 3
    
    def test_execute_automatic_step(self):
        """Test executing an automatic step."""
        engine = StepProgressionEngine()
        
        step = GameStep(
            step_id="test",
            step_type=StepType.AUTOMATIC,
            description="Test step",
            execute_fn=lambda: "success"
        )
        
        engine.queue_steps(step)
        
        # Execute the step
        executed_step = engine.execute_next_step()
        
        assert executed_step is None  # No next step
        assert step.status == StepStatus.COMPLETED
        assert step.result == "success"
    
    def test_execute_step_with_input_requirement(self):
        """Test executing a step that requires input."""
        engine = StepProgressionEngine(ExecutionMode.MANUAL)
        
        player_input = PlayerInput(
            input_type=StepType.CHOICE,
            prompt="Choose an option",
            options=["option1", "option2", "option3"]
        )
        
        step = GameStep(
            step_id="test",
            step_type=StepType.CHOICE,
            description="Test choice step",
            execute_fn=lambda choice: f"chose_{choice}",
            player_input=player_input
        )
        
        engine.queue_steps(step)
        
        # First execution should mark as waiting for input
        current_step = engine.execute_next_step()
        assert current_step == step
        assert step.status == StepStatus.WAITING_FOR_INPUT
        
        # Provide input
        next_step = engine.provide_input("option2")
        assert step.status == StepStatus.COMPLETED
        assert step.result == "chose_option2"
    
    def test_step_listeners(self):
        """Test step event listeners."""
        engine = StepProgressionEngine()
        
        completed_steps = []
        
        def step_listener(step):
            completed_steps.append(step)
        
        engine.add_step_listener(step_listener)
        
        step = GameStep(
            step_id="test",
            step_type=StepType.AUTOMATIC,
            description="Test step",
            execute_fn=lambda: "success"
        )
        
        engine.queue_steps(step)
        engine.execute_next_step()
        
        assert len(completed_steps) == 1
        assert completed_steps[0] == step
    
    def test_continue_execution_manual_mode(self):
        """Test continue execution in manual mode."""
        engine = StepProgressionEngine(ExecutionMode.MANUAL)
        
        steps = [
            GameStep("test_1", StepType.AUTOMATIC, "Test 1", lambda: "1"),
            GameStep("test_2", StepType.AUTOMATIC, "Test 2", lambda: "2"),
            GameStep("test_3", StepType.AUTOMATIC, "Test 3", lambda: "3")
        ]
        
        engine.queue_steps(steps)
        
        # In manual mode, should execute only one step
        executed = engine.continue_execution()
        assert len(executed) == 1
        assert steps[0].status == StepStatus.COMPLETED
        assert steps[1].status == StepStatus.PENDING
    
    def test_continue_execution_pause_on_input_mode(self):
        """Test continue execution in pause-on-input mode."""
        engine = StepProgressionEngine(ExecutionMode.PAUSE_ON_INPUT)
        
        steps = [
            GameStep("test_1", StepType.AUTOMATIC, "Test 1", lambda: "1"),
            GameStep("test_2", StepType.AUTOMATIC, "Test 2", lambda: "2"),
            GameStep("test_3", StepType.CHOICE, "Test 3", lambda x: f"3_{x}",
                    player_input=PlayerInput(StepType.CHOICE, "Choose", ["a", "b"]))
        ]
        
        engine.queue_steps(steps)
        
        # Should execute until the choice step
        executed = engine.continue_execution()
        
        # Check that all steps were processed correctly
        assert steps[0].status == StepStatus.COMPLETED
        assert steps[1].status == StepStatus.COMPLETED  
        assert steps[2].status == StepStatus.WAITING_FOR_INPUT
        
        # executed should contain the steps that were attempted
        assert len(executed) >= 2


class TestInputSystem:
    """Test the input system components."""
    
    def test_mock_input_provider(self):
        """Test the mock input provider."""
        provider = MockInputProvider()
        
        # Test choice
        choice = provider.get_choice("Choose", ["a", "b", "c"])
        assert choice == "a"
        
        # Test selection
        selection = provider.get_selection("Select", ["x", "y", "z"], 1, 2)
        assert selection == ["x"]  # Should return minimum count from start
        
        # Test confirmation
        confirmation = provider.get_confirmation("Confirm?", True)
        assert confirmation is True
    
    def test_queued_input_provider(self):
        """Test the queued input provider."""
        provider = QueuedInputProvider()
        
        # Queue some inputs
        provider.queue_inputs(["option2", ["target1", "target2"], False])
        
        # Test choice
        choice = provider.get_choice("Choose", ["option1", "option2", "option3"])
        assert choice == "option2"
        
        # Test selection
        selection = provider.get_selection("Select", ["target1", "target2", "target3"], 1, 3)
        assert selection == ["target1", "target2"]
        
        # Test confirmation
        confirmation = provider.get_confirmation("Confirm?")
        assert confirmation is False
        
        # Test exhaustion
        with pytest.raises(InputValidationError):
            provider.get_choice("Another choice", ["a", "b"])
    
    def test_queued_input_validation(self):
        """Test input validation in queued provider."""
        provider = QueuedInputProvider(["invalid_choice"])
        
        with pytest.raises(InputValidationError):
            provider.get_choice("Choose", ["valid1", "valid2"])
    
    def test_input_manager(self):
        """Test the input manager."""
        manager = InputManager()
        provider = MockInputProvider()
        
        manager.register_input_provider("player1", provider)
        
        # Create a step that needs input
        player_input = PlayerInput(
            input_type=StepType.CHOICE,
            prompt="Choose an option",
            options=["a", "b", "c"]
        )
        
        step = GameStep(
            step_id="test",
            step_type=StepType.CHOICE,
            description="Test step",
            execute_fn=lambda x: f"result_{x}",
            player_input=player_input
        )
        
        # Request input
        result = manager.request_input("player1", step)
        assert result == "a"  # MockInputProvider returns first option
    
    def test_ability_input_builder(self):
        """Test the ability input builder helpers."""
        # Test choice input
        choice_input = AbilityInputBuilder.create_choice_input(
            "Choose a card",
            ["card1", "card2", "card3"]
        )
        assert choice_input.input_type == StepType.CHOICE
        assert choice_input.prompt == "Choose a card"
        assert len(choice_input.options) == 3
        
        # Test target selection input
        selection_input = AbilityInputBuilder.create_target_selection_input(
            "Select targets",
            ["target1", "target2", "target3"],
            min_count=1,
            max_count=2
        )
        assert selection_input.input_type == StepType.SELECTION
        assert selection_input.constraints['min_count'] == 1
        assert selection_input.constraints['max_count'] == 2
        
        # Test confirmation input
        confirm_input = AbilityInputBuilder.create_confirmation_input(
            "Are you sure?",
            default=True
        )
        assert confirm_input.input_type == StepType.CONFIRMATION
        assert confirm_input.constraints['default'] is True


class TestStateSerializer:
    """Test the state serialization system."""
    
    def test_game_state_serializer_initialization(self):
        """Test serializer initialization."""
        serializer = GameStateSerializer()
        assert len(serializer.card_serializers) == 4
        assert len(serializer.card_deserializers) == 4
    
    def test_snapshot_manager(self):
        """Test the snapshot manager."""
        manager = SnapshotManager()
        
        # Mock game state
        mock_game_state = Mock()
        mock_game_state.turn_number = 1
        mock_game_state.current_player_index = 0
        
        # Create snapshot
        snapshot = manager.create_snapshot("step_1", mock_game_state)
        
        assert snapshot.step_id == "step_1"
        assert len(manager.snapshots) == 1
        assert manager.get_current_snapshot() == snapshot
    
    def test_snapshot_retrieval(self):
        """Test snapshot retrieval methods."""
        manager = SnapshotManager()
        mock_game_state = Mock()
        
        # Create multiple snapshots
        snapshot1 = manager.create_snapshot("step_1", mock_game_state)
        snapshot2 = manager.create_snapshot("step_2", mock_game_state)
        snapshot3 = manager.create_snapshot("step_3", mock_game_state)
        
        # Test retrieval by step ID
        found = manager.get_snapshot_by_step_id("step_2")
        assert found == snapshot2
        
        # Test restore to snapshot
        restored = manager.restore_to_snapshot(snapshot1.snapshot_id)
        assert restored == snapshot1
        assert manager.get_current_snapshot() == snapshot1
        
        # Test get all snapshots
        all_snapshots = manager.get_all_snapshots()
        assert len(all_snapshots) == 3


class TestStepSystemIntegration:
    """Test integration between step system components."""
    
    def test_complete_step_workflow(self):
        """Test a complete workflow with multiple step types."""
        engine = StepProgressionEngine(ExecutionMode.PAUSE_ON_INPUT)
        provider = QueuedInputProvider()
        manager = InputManager()
        
        manager.register_input_provider("player1", provider)
        
        # Queue inputs for the workflow
        provider.queue_inputs(["choice_b", ["target2"], True])
        
        # Create a workflow with different step types
        steps = [
            GameStep(
                step_id="auto_step",
                step_type=StepType.AUTOMATIC,
                description="Automatic step",
                execute_fn=lambda: "auto_complete"
            ),
            GameStep(
                step_id="choice_step",
                step_type=StepType.CHOICE,
                description="Choice step",
                execute_fn=lambda choice: f"chose_{choice}",
                player_input=PlayerInput(
                    StepType.CHOICE,
                    "Make a choice",
                    ["choice_a", "choice_b", "choice_c"]
                )
            ),
            GameStep(
                step_id="selection_step",
                step_type=StepType.SELECTION,
                description="Selection step",
                execute_fn=lambda targets: f"selected_{len(targets)}",
                player_input=PlayerInput(
                    StepType.SELECTION,
                    "Select targets",
                    ["target1", "target2", "target3"],
                    {"min_count": 1, "max_count": 1}
                )
            ),
            GameStep(
                step_id="confirm_step",
                step_type=StepType.CONFIRMATION,
                description="Confirmation step",
                execute_fn=lambda confirm: f"confirmed_{confirm}",
                player_input=PlayerInput(
                    StepType.CONFIRMATION,
                    "Confirm action?",
                    [True, False]
                )
            )
        ]
        
        engine.queue_steps(steps)
        
        # Execute the workflow
        executed_steps = []
        
        # Auto step should complete immediately
        executed = engine.continue_execution()
        executed_steps.extend(executed)
        
        # Should now be waiting at choice step
        current = engine.get_current_step()
        assert current.step_id == "choice_step"
        assert current.status == StepStatus.WAITING_FOR_INPUT
        
        # Provide choice input
        result = manager.request_input("player1", current)
        next_step = engine.provide_input(result)
        
        # Should now be waiting at selection step
        current = engine.get_current_step()
        assert current.step_id == "selection_step"
        
        # Provide selection input
        result = manager.request_input("player1", current)
        next_step = engine.provide_input(result)
        
        # Should now be waiting at confirmation step
        current = engine.get_current_step()
        assert current.step_id == "confirm_step"
        
        # Provide confirmation input
        result = manager.request_input("player1", current)
        next_step = engine.provide_input(result)
        
        # Verify all steps completed successfully
        # We expect the initial auto-executed steps plus the 3 input steps
        assert len([s for s in steps if s.status == StepStatus.COMPLETED]) == 4
        assert steps[0].result == "auto_complete"
        assert steps[1].result == "chose_choice_b"
        assert steps[2].result == "selected_1"
        assert steps[3].result == "confirmed_True"
        
        # All steps should be completed
        for step in steps:
            assert step.status == StepStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__])