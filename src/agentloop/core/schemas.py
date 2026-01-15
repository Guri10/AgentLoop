"""
Action schemas and contracts.

Defines the structured format for actions and decisions that the LLM must follow.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Available action types the agent can execute."""
    
    SEARCH_WEB = "search_web"
    RUN_CODE = "run_code"
    WRITE_FILE = "write_file"
    FINISH = "finish"


class ActionInput(BaseModel):
    """Base model for action inputs."""
    
    pass


class SearchWebInput(ActionInput):
    """Input schema for web search action."""
    
    query: str = Field(..., description="The search query to execute")
    num_results: int = Field(default=5, ge=1, le=10, description="Number of results to return")


class RunCodeInput(ActionInput):
    """Input schema for code execution action."""
    
    code: str = Field(..., description="Python code to execute")
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")


class WriteFileInput(ActionInput):
    """Input schema for file writing action."""
    
    filename: str = Field(..., description="Name/path of the file to write")
    content: str = Field(..., description="Content to write to the file")


class FinishInput(ActionInput):
    """Input schema for finish action."""
    
    summary: str = Field(..., description="Summary of what was accomplished")
    artifacts: list[str] = Field(
        default_factory=list, description="List of files/outputs created"
    )


class ActionDecision(BaseModel):
    """
    Structured decision output from the LLM.
    
    The LLM must output decisions in this exact format.
    """
    
    action: ActionType = Field(..., description="The action to execute")
    reasoning: str = Field(..., description="Why this action was chosen")
    input: Dict[str, Any] = Field(..., description="Input parameters for the action")
    
    def get_typed_input(self) -> ActionInput:
        """Convert generic input dict to typed input model."""
        input_map = {
            ActionType.SEARCH_WEB: SearchWebInput,
            ActionType.RUN_CODE: RunCodeInput,
            ActionType.WRITE_FILE: WriteFileInput,
            ActionType.FINISH: FinishInput,
        }
        input_class = input_map[self.action]
        return input_class(**self.input)


class ActionResult(BaseModel):
    """Result from executing an action."""
    
    action: ActionType
    success: bool
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    """
    Complete state of the agent at any point in time.
    
    This is passed to the LLM at each decision step.
    """
    
    goal: str = Field(..., description="The original high-level goal")
    current_step: int = Field(default=0, description="Current step number")
    max_steps: int = Field(default=50, description="Maximum allowed steps")
    
    # History tracking
    actions_taken: list[ActionDecision] = Field(
        default_factory=list, description="All actions taken so far"
    )
    action_results: list[ActionResult] = Field(
        default_factory=list, description="Results from all actions"
    )
    
    # Status
    is_complete: bool = Field(default=False, description="Whether goal is satisfied")
    total_cost: float = Field(default=0.0, description="Cumulative API cost in USD")
    
    def add_action(self, decision: ActionDecision, result: ActionResult):
        """Record an action and its result."""
        self.actions_taken.append(decision)
        self.action_results.append(result)
        self.current_step += 1
    
    def get_recent_history(self, n: int = 5) -> str:
        """Get formatted recent history for context."""
        recent = []
        start = max(0, len(self.actions_taken) - n)
        
        for i in range(start, len(self.actions_taken)):
            action = self.actions_taken[i]
            result = self.action_results[i]
            
            status = "✓" if result.success else "✗"
            recent.append(
                f"{status} Step {i+1}: {action.action.value}\n"
                f"   Reason: {action.reasoning}\n"
                f"   Result: {result.output if result.success else result.error}"
            )
        
        return "\n".join(recent) if recent else "No actions taken yet."
    
    def can_continue(self) -> tuple[bool, str]:
        """Check if agent can continue execution."""
        if self.is_complete:
            return False, "Goal already completed"
        if self.current_step >= self.max_steps:
            return False, f"Maximum steps ({self.max_steps}) reached"
        return True, "Can continue"

