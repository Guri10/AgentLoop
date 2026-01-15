# AgentLoop

**An Autonomous Agent System demonstrating LLM-based decision-making in a closed-loop control architecture.**

AgentLoop is not a chatbot or a prompt chain—it's a closed-loop decision system where an LLM repeatedly decides what action to take next based on evolving state until the goal is satisfied.

## 🎯 Core Objective

This project demonstrates how an LLM can be used as a **decision-making controller** inside a software system, rather than as a text generator. The agent autonomously:

- ✅ Decides what to do next
- ✅ Chooses which action to invoke
- ✅ Observes results
- ✅ Recovers from failures
- ✅ Terminates when the goal is complete

## 🏗️ Architecture

### The Fundamental Loop

The entire system is built around this explicit control loop:

```python
while goal_not_satisfied:
    decide_next_action()    # LLM decides
    execute_action()        # System executes
    observe_result()        # System observes
    update_state()          # System updates
```

### System Design

```
┌─────────────────────────────────────────┐
│         User Submits Goal               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Decision Engine (LLM)              │
│  - Receives: Goal, State, History       │
│  - Outputs: Structured Action Decision  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Action Executor (System)           │
│  - search_web                           │
│  - run_code                             │
│  - write_file                           │
│  - finish                               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         State Management                │
│  - History                              │
│  - Results                              │
│  - Errors                               │
└─────────────────────────────────────────┘
```

### Key Design Principles

1. **Plan-Execute Separation**: LLM plans, system executes
2. **Structured Actions**: Fixed action space with strict schemas
3. **Explicit State**: All history is tracked and passed to LLM
4. **Failure Recovery**: Automatic retry with error context
5. **Safety Limits**: Maximum steps and cost controls

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/AgentLoop.git
cd AgentLoop

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Add your OpenAI API key:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
MAX_STEPS=50
MAX_RETRIES=3
```

### Basic Usage

```python
from agentloop.main import run_agent

# Submit a goal - the agent does the rest
state = run_agent(
    goal="Research recent AI developments and create a summary report"
)

# Check results
print(f"Completed: {state.is_complete}")
print(f"Cost: ${state.total_cost:.4f}")
```

### Run Demo Scripts

```bash
# Simple web search demo
python examples/demo_simple.py

# Research and summarization
python examples/demo_research.py

# Code execution and analysis
python examples/demo_analysis.py
```

## 🎮 Available Actions

The agent can only interact through these predefined actions:

### 1. `search_web`

Search the internet for information.

```json
{
  "action": "search_web",
  "reasoning": "Need to find recent information",
  "input": {
    "query": "small language models 2024",
    "num_results": 5
  }
}
```

### 2. `run_code`

Execute Python code for analysis or computation.

```json
{
  "action": "run_code",
  "reasoning": "Calculate statistics from data",
  "input": {
    "code": "print(sum([1, 2, 3, 4, 5]))",
    "timeout": 30
  }
}
```

### 3. `write_file`

Save content to a file.

```json
{
  "action": "write_file",
  "reasoning": "Save final report",
  "input": {
    "filename": "report.md",
    "content": "# Report\n\nFindings..."
  }
}
```

### 4. `finish`

Complete the task and terminate.

```json
{
  "action": "finish",
  "reasoning": "Goal accomplished",
  "input": {
    "summary": "Created research report with 3 key findings",
    "artifacts": ["report.md"]
  }
}
```

## 📊 State Management

The agent maintains complete state throughout execution:

```python
class AgentState:
    goal: str                          # Original goal
    current_step: int                  # Current step number
    max_steps: int                     # Step limit
    actions_taken: list[ActionDecision]  # Decision history
    action_results: list[ActionResult]   # Execution results
    is_complete: bool                  # Completion status
    total_cost: float                  # API cost tracking
```

State is passed to the LLM at each decision point, enabling:

- Learning from past actions
- Avoiding repeated mistakes
- Contextual decision-making

## 🛡️ Failure Handling

AgentLoop implements robust error recovery:

1. **Retry Logic**: Failed actions retry up to 3 times with error context
2. **Alternative Actions**: LLM chooses different approaches after failures
3. **State Preservation**: All failures are recorded and influence future decisions
4. **Safety Limits**: Automatic termination at step/cost limits

## 💰 Cost Tracking

The system tracks API usage and estimates costs:

```python
# After execution
print(f"Total tokens: {agent.decision_engine.total_tokens}")
print(f"Estimated cost: ${state.total_cost:.4f}")
```

Typical costs with GPT-4o-mini:

- Simple task (5-8 steps): $0.05 - $0.15
- Medium task (10-20 steps): $0.15 - $0.50
- Complex task (20-40 steps): $0.50 - $2.00

## 🧪 Example: End-to-End Execution

```bash
$ python -m agentloop.main "Find recent Python web frameworks and create a comparison"

============================================================
🎯 GOAL: Find recent Python web frameworks and create a comparison
============================================================

--- Step 1/50 ---
🤔 Decision: search_web
💭 Reasoning: Need to find current information about Python web frameworks
✅ Success: 5 items

--- Step 2/50 ---
🤔 Decision: search_web
💭 Reasoning: Get more details on specific frameworks
✅ Success: 5 items

--- Step 3/50 ---
🤔 Decision: write_file
💭 Reasoning: Compile findings into comparison document
✅ Success: File written successfully: ./output/framework_comparison.md

--- Step 4/50 ---
🤔 Decision: finish
💭 Reasoning: Goal accomplished - comparison created
✅ Success: {'summary': 'Created comparison...', 'artifacts': [...]}

🎉 Task completed!

============================================================
📊 EXECUTION SUMMARY
============================================================
Goal: Find recent Python web frameworks and create a comparison
Status: ✅ Complete
Steps taken: 4/50
Estimated cost: $0.0234
Success rate: 4/4 actions
============================================================
```

## 🏗️ Project Structure

```
AgentLoop/
├── src/agentloop/
│   ├── core/
│   │   ├── agent.py          # Main decision loop
│   │   └── schemas.py        # Action/state schemas
│   ├── actions/
│   │   └── executor.py       # Action implementations
│   ├── llm/
│   │   └── decision_engine.py # LLM interface
│   └── main.py               # Entry point
├── examples/
│   ├── demo_simple.py
│   ├── demo_research.py
│   └── demo_analysis.py
├── tests/
├── output/                   # Generated artifacts
├── pyproject.toml
└── README.md
```

## 🔬 Technical Details

### Why This Architecture?

**Separation of Concerns:**

- LLM = Decision maker (what to do)
- System = Executor (how to do it)

**Benefits:**

- Reduces hallucination (LLM doesn't execute)
- Improves debuggability (clear boundaries)
- Enables testing (mock executors)
- Demonstrates software engineering

### Action Schema Enforcement

All LLM outputs must match strict Pydantic schemas:

```python
class ActionDecision(BaseModel):
    action: ActionType
    reasoning: str
    input: Dict[str, Any]
```

Invalid outputs are rejected and retried.

### State-Driven Decisions

The LLM receives:

- Original goal
- Complete history (last 5 actions)
- Current step count
- Previous failures

This enables learning and adaptation.

## 🎓 What This Project Demonstrates

### For Hiring Managers:

- ✅ Systems architecture and design
- ✅ LLM integration as a system component
- ✅ Error handling and recovery patterns
- ✅ State management
- ✅ Clean code organization
- ✅ Production considerations (cost tracking, limits)

### Not Just Prompt Engineering:

This project shows **engineering discipline**:

- Explicit control flow (not prompt chains)
- Structured interfaces (not free-form text)
- Testable components (separation of concerns)
- Observable behavior (complete state tracking)

## 📈 Future Enhancements

Potential improvements:

- [ ] Add more actions (read_document, database_query)
- [ ] Implement state compression for long tasks
- [ ] Add web UI for real-time visualization
- [ ] Multi-agent coordination
- [ ] Tool learning (let LLM suggest new actions)
- [ ] Parallel action execution
- [ ] Cost optimization with caching

## 📝 License

MIT License - see LICENSE file

## 🤝 Contributing

Contributions welcome! This is a learning project demonstrating autonomous agents.

## 📧 Contact

Built as a demonstration of LLM-based control systems.

---

**Key Insight:** This is not about making the smartest LLM—it's about building a system where an LLM can make reliable decisions within a controlled environment.
