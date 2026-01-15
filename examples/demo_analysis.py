"""
Demo: Data analysis with code execution.

This example shows the agent writing and executing code for analysis.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentloop.main import run_agent


def main():
    """Run analysis demo."""
    goal = (
        "Write Python code to generate a list of the first 20 Fibonacci numbers, "
        "then calculate their sum and average. "
        "Save the results and code to 'fibonacci_analysis.txt'."
    )
    
    print("📊 Demo: Autonomous Analysis Agent")
    print(f"Goal: {goal}\n")
    
    state = run_agent(
        goal=goal,
        output_dir="./output/analysis",
        max_steps=10,
        model="gpt-4o-mini"
    )
    
    print(f"\n✅ Demo complete!")
    print(f"Check ./output/analysis/ for results")


if __name__ == "__main__":
    main()

