"""
Main entry point for AgentLoop.

Simple interface to create and run the autonomous agent.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from .actions.executor import ActionExecutor
from .core.agent import AutonomousAgent
from .llm.decision_engine import DecisionEngine


def create_agent(
    output_dir: str = "./output",
    max_steps: int = 50,
    max_retries: int = 3,
    model: str = "gpt-4o-mini",
    verbose: bool = True
) -> AutonomousAgent:
    """
    Create a configured autonomous agent.
    
    Args:
        output_dir: Directory for output files
        max_steps: Maximum execution steps
        max_retries: Maximum retry attempts
        model: OpenAI model to use
        verbose: Print execution logs
        
    Returns:
        Configured AutonomousAgent
    """
    # Load environment variables
    load_dotenv()
    
    # Validate API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment. "
            "Please set it in .env file or environment variables."
        )
    
    # Create components
    decision_engine = DecisionEngine(api_key=api_key, model=model)
    action_executor = ActionExecutor(output_dir=output_dir)
    
    # Create agent
    agent = AutonomousAgent(
        decision_engine=decision_engine,
        action_executor=action_executor,
        max_steps=max_steps,
        max_retries=max_retries,
        verbose=verbose
    )
    
    return agent


def run_agent(goal: str, **kwargs):
    """
    Convenience function to create and run an agent.
    
    Args:
        goal: High-level goal for the agent
        **kwargs: Additional arguments for create_agent()
        
    Returns:
        Final AgentState
    """
    agent = create_agent(**kwargs)
    return agent.run(goal)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m agentloop.main '<goal>'")
        print("\nExample:")
        print("  python -m agentloop.main 'Search for recent AI news and summarize it'")
        sys.exit(1)
    
    goal = sys.argv[1]
    run_agent(goal)

