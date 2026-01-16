"""
Core autonomous agent with decision loop.

This is the main controller that runs the agent loop:
    while goal_not_satisfied:
        decide next action
        execute action
        observe result
        update state
"""

import time
from typing import Optional

from ..actions.executor import ActionExecutor
from ..llm.decision_engine import DecisionEngine
from .schemas import ActionDecision, ActionResult, ActionType, AgentState


class AutonomousAgent:
    """
    The main autonomous agent that runs the decision-execution loop.
    
    This demonstrates how an LLM can be used as a decision-making controller
    inside a software system.
    """
    
    def __init__(
        self,
        decision_engine: DecisionEngine,
        action_executor: ActionExecutor,
        max_steps: int = 50,
        max_retries: int = 3,
        verbose: bool = True
    ):
        """
        Initialize the autonomous agent.
        
        Args:
            decision_engine: LLM-based decision maker
            action_executor: System that executes actions
            max_steps: Maximum steps before forced termination
            max_retries: Maximum retries per failed action
            verbose: Whether to print progress
        """
        self.decision_engine = decision_engine
        self.action_executor = action_executor
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.verbose = verbose
    
    def run(self, goal: str) -> AgentState:
        """
        Run the autonomous agent loop.
        
        This is the core of the system - the explicit decision loop.
        
        Args:
            goal: High-level goal to accomplish
            
        Returns:
            Final agent state with complete history
        """
        # Initialize state
        state = AgentState(goal=goal, max_steps=self.max_steps)
        
        self._log(f"\n{'='*60}")
        self._log(f"GOAL: {goal}")
        self._log(f"{'='*60}\n")
        
        # THE AUTONOMOUS LOOP
        while True:
            # Check if we can continue
            can_continue, reason = state.can_continue()
            if not can_continue:
                self._log(f"\nStopping: {reason}")
                break
            
            # STEP 1: Decide next action
            self._log(f"\n--- Step {state.current_step + 1}/{state.max_steps} ---")
            
            try:
                decision = self._decide_with_retry(state)
            except Exception as e:
                self._log(f"[ERROR] Decision failed: {e}")
                break
            
            self._log(f"Decision: {decision.action.value}")
            self._log(f"Reasoning: {decision.reasoning}")
            
            # STEP 2: Execute action
            result = self._execute_with_retry(decision, state)
            
            # STEP 3: Observe result
            if result.success:
                self._log(f"[SUCCESS] {self._format_output(result.output)}")
            else:
                self._log(f"[FAILED] {result.error}")
            
            # STEP 4: Update state
            state.add_action(decision, result)
            
            # Update cost estimate
            state.total_cost = self.decision_engine.get_cost_estimate()
            
            # Check if finished
            if decision.action == ActionType.FINISH and result.success:
                state.is_complete = True
                self._log("\nTask completed!")
                break
        
        # Print summary
        self._print_summary(state)
        
        return state
    
    def _decide_with_retry(self, state: AgentState) -> ActionDecision:
        """
        Ask LLM to decide next action, with retry logic.
        
        Args:
            state: Current agent state
            
        Returns:
            ActionDecision from the LLM
            
        Raises:
            ValueError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                decision = self.decision_engine.decide_next_action(state)
                return decision
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    self._log(f"[WARNING] Decision failed (attempt {attempt + 1}): {e}")
                    time.sleep(1)  # Brief pause before retry
        
        raise ValueError(f"Decision failed after {self.max_retries} attempts: {last_error}")
    
    def _execute_with_retry(self, decision: ActionDecision, state: AgentState) -> ActionResult:
        """
        Execute an action with retry logic for transient failures.
        
        Args:
            decision: The action decision to execute
            state: Current state (for context in retry logic)
            
        Returns:
            ActionResult from execution
        """
        last_result = None
        
        for attempt in range(self.max_retries):
            result = self.action_executor.execute(
                decision.action,
                decision.input
            )
            
            if result.success:
                return result
            
            last_result = result
            
            # Don't retry certain failures
            if self._should_not_retry(result):
                return result
            
            if attempt < self.max_retries - 1:
                self._log(f"[WARNING] Retrying action (attempt {attempt + 2})...")
                time.sleep(1)
        
        return last_result or ActionResult(
            action=decision.action,
            success=False,
            error="Execution failed after retries"
        )
    
    def _should_not_retry(self, result: ActionResult) -> bool:
        """Determine if an action failure should not be retried."""
        # Don't retry validation errors or certain action types
        if result.action == ActionType.FINISH:
            return True
        
        if result.error and any(keyword in result.error.lower() for keyword in [
            "validation", "invalid", "schema", "timeout"
        ]):
            return True
        
        return False
    
    def _format_output(self, output: any) -> str:
        """Format action output for display."""
        if isinstance(output, str):
            return output[:200] + "..." if len(output) > 200 else output
        elif isinstance(output, list):
            return f"{len(output)} items"
        elif isinstance(output, dict):
            return str(output)[:200]
        else:
            return str(output)[:200]
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _print_summary(self, state: AgentState):
        """Print execution summary."""
        self._log(f"\n{'='*60}")
        self._log("EXECUTION SUMMARY")
        self._log(f"{'='*60}")
        self._log(f"Goal: {state.goal}")
        self._log(f"Status: {'Complete' if state.is_complete else 'Incomplete'}")
        self._log(f"Steps taken: {state.current_step}/{state.max_steps}")
        self._log(f"Estimated cost: ${state.total_cost:.4f}")
        
        # Count successes
        successful = sum(1 for r in state.action_results if r.success)
        self._log(f"Success rate: {successful}/{len(state.action_results)} actions")
        
        self._log(f"{'='*60}\n")

