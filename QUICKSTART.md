# AgentLoop Quick Start Guide

Get up and running with AgentLoop in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- `uv` installed (or `pip`)

## Installation

### Option 1: Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/AgentLoop.git
cd AgentLoop

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### Option 2: Using pip

```bash
git clone https://github.com/YOUR_USERNAME/AgentLoop.git
cd AgentLoop

pip install -e .
```

## Configuration

1. **Create a `.env` file:**

```bash
cp .env.example .env
```

2. **Add your OpenAI API key:**

Edit `.env` and add:
```
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
MAX_STEPS=50
MAX_RETRIES=3
```

## Your First Agent

### Method 1: Command Line

```bash
python -m agentloop.main "Search for the latest Python releases and list them"
```

### Method 2: Python Script

Create `my_agent.py`:

```python
from agentloop.main import run_agent

state = run_agent(
    goal="Write a Python script that prints Hello World and save it as hello.py"
)

print(f"\nTask completed: {state.is_complete}")
print(f"Steps taken: {state.current_step}")
print(f"Cost: ${state.total_cost:.4f}")
```

Run it:
```bash
python my_agent.py
```

### Method 3: Run Demo Examples

```bash
# Simple demo (5-8 steps, ~30 seconds)
python examples/demo_simple.py

# Research demo (10-15 steps, ~1-2 minutes)
python examples/demo_research.py

# Analysis demo (5-10 steps, ~45 seconds)
python examples/demo_analysis.py
```

## Understanding the Output

When you run an agent, you'll see:

```
============================================================
🎯 GOAL: Your goal here
============================================================

--- Step 1/50 ---
🤔 Decision: search_web
💭 Reasoning: Need to find information about...
✅ Success: 5 items

--- Step 2/50 ---
🤔 Decision: write_file
💭 Reasoning: Save the results to a file
✅ Success: File written successfully: ./output/results.txt

--- Step 3/50 ---
🤔 Decision: finish
💭 Reasoning: Goal accomplished
✅ Success: {'summary': 'Task completed', 'artifacts': [...]}

🎉 Task completed!

============================================================
📊 EXECUTION SUMMARY
============================================================
Goal: Your goal here
Status: ✅ Complete
Steps taken: 3/50
Estimated cost: $0.0123
Success rate: 3/3 actions
============================================================
```

## Check Your Output

All generated files are saved to `./output/`:

```bash
ls -la output/
```

## Example Goals to Try

### Simple Tasks (3-5 steps)
```python
"Search for Python 3.12 new features and list the top 5"
"Calculate the factorial of 10 and save it to a file"
"Find today's date and write it to a file called date.txt"
```

### Medium Tasks (8-15 steps)
```python
"Research recent developments in WebAssembly and create a summary report"
"Write code to generate the first 50 prime numbers, then analyze their distribution"
"Search for popular Python testing frameworks and create a comparison table"
```

### Complex Tasks (15-30 steps)
```python
"Research small language models, compare their sizes and capabilities, write code to visualize the data, and create a comprehensive report"
```

## Common Issues

### Issue: "OPENAI_API_KEY not found"
**Solution:** Make sure you created `.env` file and added your API key.

### Issue: "No module named 'agentloop'"
**Solution:** Install the package with `uv sync` or `pip install -e .`

### Issue: Search results are empty
**Solution:** DuckDuckGo search may be rate-limited. Wait a few seconds and try again.

### Issue: Code execution times out
**Solution:** Increase timeout in the action input or simplify the code.

## Cost Estimation

Typical costs with GPT-4o-mini:

| Task Complexity | Steps | Est. Cost |
|----------------|-------|-----------|
| Simple | 3-8 | $0.05 - $0.15 |
| Medium | 8-20 | $0.15 - $0.50 |
| Complex | 20-40 | $0.50 - $2.00 |

Monitor costs:
```python
state = run_agent(goal="...")
print(f"Total cost: ${state.total_cost:.4f}")
```

## Advanced Configuration

### Use a Different Model

```python
from agentloop.main import create_agent

agent = create_agent(
    model="gpt-4o",  # More capable but more expensive
    max_steps=30,
    verbose=True
)

state = agent.run("Your complex goal here")
```

### Custom Output Directory

```python
agent = create_agent(
    output_dir="./my_outputs",
    max_steps=50
)
```

### Silent Mode (No Logs)

```python
agent = create_agent(verbose=False)
state = agent.run("Your goal")
# Only see the final summary
```

## Next Steps

1. **Read the Architecture:** See `ARCHITECTURE.md` to understand how it works
2. **Modify Actions:** Add custom actions in `src/agentloop/actions/executor.py`
3. **Experiment:** Try different goals and observe the decision-making
4. **Extend:** Add new capabilities (database access, API calls, etc.)

## Need Help?

- Check `README.md` for detailed documentation
- Review `ARCHITECTURE.md` for design decisions
- Look at `examples/` for more patterns
- Open an issue on GitHub

## Safety Notes

⚠️ **Code Execution:** The `run_code` action executes Python code in a subprocess. Only use this agent with trusted goals.

⚠️ **API Costs:** Monitor your OpenAI usage at https://platform.openai.com/usage

⚠️ **Rate Limits:** Web search may be rate-limited. The agent will retry, but may hit limits with very frequent requests.

---

**Ready to build?** Start with a simple goal and watch the agent work autonomously!

```bash
python -m agentloop.main "Your goal here"
```

