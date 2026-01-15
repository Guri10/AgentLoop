"""
Test action schemas and validation.
"""

import pytest
from pydantic import ValidationError

from agentloop.core.schemas import (
    ActionDecision,
    ActionType,
    ActionResult,
    AgentState,
    SearchWebInput,
    RunCodeInput,
    WriteFileInput,
    FinishInput,
)


def test_action_type_enum():
    """Test ActionType enum values."""
    assert ActionType.SEARCH_WEB == "search_web"
    assert ActionType.RUN_CODE == "run_code"
    assert ActionType.WRITE_FILE == "write_file"
    assert ActionType.FINISH == "finish"


def test_search_web_input_valid():
    """Test valid SearchWebInput."""
    input_data = SearchWebInput(query="test query", num_results=5)
    assert input_data.query == "test query"
    assert input_data.num_results == 5


def test_search_web_input_defaults():
    """Test SearchWebInput defaults."""
    input_data = SearchWebInput(query="test")
    assert input_data.num_results == 5  # Default value


def test_search_web_input_validation():
    """Test SearchWebInput validation."""
    with pytest.raises(ValidationError):
        SearchWebInput(query="test", num_results=0)  # Must be >= 1
    
    with pytest.raises(ValidationError):
        SearchWebInput(query="test", num_results=11)  # Must be <= 10


def test_run_code_input_valid():
    """Test valid RunCodeInput."""
    input_data = RunCodeInput(code="print('hello')", timeout=30)
    assert input_data.code == "print('hello')"
    assert input_data.timeout == 30


def test_write_file_input_valid():
    """Test valid WriteFileInput."""
    input_data = WriteFileInput(filename="test.txt", content="hello")
    assert input_data.filename == "test.txt"
    assert input_data.content == "hello"


def test_finish_input_valid():
    """Test valid FinishInput."""
    input_data = FinishInput(
        summary="Task complete",
        artifacts=["file1.txt", "file2.txt"]
    )
    assert input_data.summary == "Task complete"
    assert len(input_data.artifacts) == 2


def test_action_decision_valid():
    """Test valid ActionDecision."""
    decision = ActionDecision(
        action=ActionType.SEARCH_WEB,
        reasoning="Need information",
        input={"query": "test", "num_results": 5}
    )
    assert decision.action == ActionType.SEARCH_WEB
    assert decision.reasoning == "Need information"
    
    # Test typed input conversion
    typed_input = decision.get_typed_input()
    assert isinstance(typed_input, SearchWebInput)
    assert typed_input.query == "test"


def test_action_result():
    """Test ActionResult."""
    result = ActionResult(
        action=ActionType.SEARCH_WEB,
        success=True,
        output=["result1", "result2"],
        metadata={"count": 2}
    )
    assert result.success is True
    assert len(result.output) == 2
    assert result.metadata["count"] == 2


def test_agent_state_initialization():
    """Test AgentState initialization."""
    state = AgentState(goal="Test goal", max_steps=10)
    assert state.goal == "Test goal"
    assert state.current_step == 0
    assert state.max_steps == 10
    assert state.is_complete is False
    assert len(state.actions_taken) == 0


def test_agent_state_add_action():
    """Test adding actions to state."""
    state = AgentState(goal="Test", max_steps=10)
    
    decision = ActionDecision(
        action=ActionType.SEARCH_WEB,
        reasoning="Test",
        input={"query": "test", "num_results": 5}
    )
    
    result = ActionResult(
        action=ActionType.SEARCH_WEB,
        success=True,
        output=["result"]
    )
    
    state.add_action(decision, result)
    
    assert state.current_step == 1
    assert len(state.actions_taken) == 1
    assert len(state.action_results) == 1


def test_agent_state_can_continue():
    """Test state continuation checks."""
    state = AgentState(goal="Test", max_steps=3)
    
    # Can continue initially
    can_continue, reason = state.can_continue()
    assert can_continue is True
    
    # Add actions until max steps
    for _ in range(3):
        decision = ActionDecision(
            action=ActionType.SEARCH_WEB,
            reasoning="Test",
            input={"query": "test"}
        )
        result = ActionResult(action=ActionType.SEARCH_WEB, success=True)
        state.add_action(decision, result)
    
    # Cannot continue - max steps reached
    can_continue, reason = state.can_continue()
    assert can_continue is False
    assert "Maximum steps" in reason


def test_agent_state_completion():
    """Test state completion flag."""
    state = AgentState(goal="Test", max_steps=10)
    
    can_continue, _ = state.can_continue()
    assert can_continue is True
    
    # Mark as complete
    state.is_complete = True
    
    can_continue, reason = state.can_continue()
    assert can_continue is False
    assert "already completed" in reason


def test_agent_state_get_recent_history():
    """Test recent history formatting."""
    state = AgentState(goal="Test", max_steps=10)
    
    # Empty history
    history = state.get_recent_history()
    assert "No actions taken" in history
    
    # Add an action
    decision = ActionDecision(
        action=ActionType.SEARCH_WEB,
        reasoning="Need info",
        input={"query": "test"}
    )
    result = ActionResult(
        action=ActionType.SEARCH_WEB,
        success=True,
        output="Found results"
    )
    state.add_action(decision, result)
    
    history = state.get_recent_history()
    assert "Step 1" in history
    assert "search_web" in history
    assert "Need info" in history

