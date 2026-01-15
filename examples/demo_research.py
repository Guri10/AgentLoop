"""
Demo: Research and summarize a topic.

This example shows the agent autonomously researching a topic and creating a report.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentloop.main import run_agent


def main():
    """Run research demo."""
    goal = (
        "Research recent developments in small language models (SLMs) "
        "and create a markdown report summarizing the top 3 findings. "
        "Save the report as 'slm_research.md'."
    )
    
    print("🔬 Demo: Autonomous Research Agent")
    print(f"Goal: {goal}\n")
    
    state = run_agent(
        goal=goal,
        output_dir="./output/research",
        max_steps=15,
        model="gpt-4o-mini"
    )
    
    print(f"\n✅ Demo complete!")
    print(f"Check ./output/research/ for results")


if __name__ == "__main__":
    main()

