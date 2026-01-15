"""
Demo: Simple web search and report.

This is the simplest demo showing basic autonomous behavior.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentloop.main import run_agent


def main():
    """Run simple demo."""
    goal = "Search for the latest OpenAI models and list them in a file called 'openai_models.txt'."
    
    print("🚀 Demo: Simple Autonomous Agent")
    print(f"Goal: {goal}\n")
    
    state = run_agent(
        goal=goal,
        output_dir="./output/simple",
        max_steps=8,
        model="gpt-4o-mini"
    )
    
    print(f"\n✅ Demo complete!")
    print(f"Check ./output/simple/ for results")


if __name__ == "__main__":
    main()

