"""
LLM-based decision engine.

The LLM acts as a controller that decides what action to take next.
"""

import json
import os
from typing import Optional

from openai import OpenAI
from pydantic import ValidationError

from ..core.schemas import ActionDecision, ActionType, AgentState


class DecisionEngine:
    """LLM-based decision maker for the agent."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7
    ):
        """
        Initialize the decision engine.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use for decisions
            temperature: Sampling temperature
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.total_tokens = 0
    
    def decide_next_action(self, state: AgentState) -> ActionDecision:
        """
        Ask the LLM to decide the next action.
        
        Args:
            state: Current agent state
            
        Returns:
            ActionDecision with the chosen action and reasoning
            
        Raises:
            ValueError: If LLM output is invalid
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(state)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Track usage
            if response.usage:
                self.total_tokens += response.usage.total_tokens
            
            # Parse response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
            
            decision_data = json.loads(content)
            decision = ActionDecision(**decision_data)
            
            return decision
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from LLM: {e}")
        except ValidationError as e:
            raise ValueError(f"Invalid action schema: {e}")
        except Exception as e:
            raise ValueError(f"Decision failed: {e}")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines the agent's behavior."""
        return """You are an autonomous agent that breaks down high-level goals into concrete actions.

Your role is to DECIDE what to do next, not to execute actions yourself.

AVAILABLE ACTIONS:
1. search_web - Search the internet for information
   Input: {"query": "search terms", "num_results": 5}

2. run_code - Execute Python code for analysis/computation
   Input: {"code": "python code as string", "timeout": 30}

3. write_file - Save content to a file
   Input: {"filename": "output.txt", "content": "file content"}

4. finish - Complete the task and terminate
   Input: {"summary": "what was accomplished", "artifacts": ["file1.txt"]}

CRITICAL RULES:
- You must output ONLY valid JSON in this exact format:
  {
    "action": "action_name",
    "reasoning": "why you chose this action",
    "input": {<action-specific input>}
  }

- Choose ONE action per decision
- Base decisions on the current state and recent history
- If the goal is complete, choose "finish"
- If stuck after 3 failed attempts, try a different approach
- Be specific in your reasoning

OUTPUT FORMAT:
Your entire response must be valid JSON matching the schema above."""
    
    def _build_user_prompt(self, state: AgentState) -> str:
        """Build the user prompt with current state."""
        can_continue, reason = state.can_continue()
        
        if not can_continue:
            # Force finish if we can't continue
            return f"""GOAL: {state.goal}

STATUS: Cannot continue - {reason}

You MUST output a finish action with a summary of what was accomplished."""
        
        prompt = f"""GOAL: {state.goal}

CURRENT STATUS:
- Step: {state.current_step + 1}/{state.max_steps}
- Actions completed: {len(state.actions_taken)}
- Total cost: ${state.total_cost:.4f}

RECENT HISTORY:
{state.get_recent_history()}

TASK:
Decide the next action to take toward completing the goal.

Remember:
- Output ONLY valid JSON
- Choose the most logical next step
- If goal is satisfied, use "finish" action
- Be specific and actionable

OUTPUT (JSON only):"""
        
        return prompt
    
    def get_cost_estimate(self) -> float:
        """
        Estimate total cost based on tokens used.
        
        Rough estimate using GPT-4o-mini pricing:
        $0.150 per 1M input tokens, $0.600 per 1M output tokens
        Simplified to $0.30 per 1M total tokens average
        """
        return (self.total_tokens / 1_000_000) * 0.30

