# AgentLoop Architecture

## Overview

AgentLoop demonstrates how to build an autonomous agent using an LLM as a decision-making controller within a software system. This document explains the architectural decisions and their rationale.

## Core Principle: The Decision Loop

The fundamental insight is that autonomy emerges from a simple loop:

```python
state = initialize(goal)

while not goal_satisfied(state):
    decision = llm_decide(state)      # LLM picks an action
    result = system_execute(decision)  # System runs it
    state = update(state, result)      # State evolves
```

This is **fundamentally different** from:
- Chatbots (reactive, user-driven)
- Prompt chains (predetermined flow)
- Workflow engines (explicit DAGs)

## Design Decisions

### 1. Plan-Execute Separation

**Decision:** The LLM only decides; it never executes.

**Rationale:**
- **Reduces hallucination**: LLM can't fabricate execution results
- **Improves reliability**: System code is deterministic
- **Enables testing**: Can mock executors independently
- **Demonstrates architecture**: Shows proper separation of concerns

**Implementation:**
```python
# LLM (decision_engine.py)
def decide_next_action(state) -> ActionDecision:
    # Returns structured decision, doesn't execute anything
    pass

# System (executor.py)  
def execute(action_type, input_data) -> ActionResult:
    # Executes deterministically, no LLM involved
    pass
```

### 2. Fixed Action Space

**Decision:** The agent has exactly 4 actions, no more, no less.

**Rationale:**
- **Controlled autonomy**: Agent can't invent arbitrary capabilities
- **Predictable behavior**: System knows all possible actions
- **Safety**: Limited blast radius
- **Simplicity**: Easy to reason about

**Trade-off:** Less flexible than tool-use agents, but more reliable and debuggable.

### 3. Structured Action Schema

**Decision:** All LLM outputs must match strict Pydantic schemas.

**Rationale:**
- **Type safety**: Catch errors before execution
- **Validation**: Reject invalid decisions immediately
- **Documentation**: Schema is self-documenting
- **Reliability**: No parsing ambiguity

**Implementation:**
```python
class ActionDecision(BaseModel):
    action: ActionType       # Enum, not freeform string
    reasoning: str           # Required explanation
    input: Dict[str, Any]    # Will be validated per action
```

Invalid outputs trigger retry with error feedback.

### 4. Explicit State Management

**Decision:** All execution history is stored and passed to LLM.

**Rationale:**
- **Learning**: Agent sees past successes/failures
- **Context**: Decisions informed by history
- **Debugging**: Complete audit trail
- **Transparency**: User can inspect state

**Trade-off:** State grows with execution length, hitting context limits around 30-50 steps.

**Future improvement:** Implement state summarization.

### 5. Retry Logic with Context

**Decision:** Failed actions retry up to 3 times, with error passed to LLM.

**Rationale:**
- **Resilience**: Handle transient failures (network issues, etc.)
- **Learning**: LLM sees error and can adjust approach
- **Recovery**: Many failures are recoverable with different parameters

**Implementation:**
```python
for attempt in range(max_retries):
    result = execute(action)
    if result.success:
        return result
    # Error is added to state, LLM sees it in next decision
```

### 6. Safety Limits

**Decision:** Hard limits on steps (50) and retries (3).

**Rationale:**
- **Cost control**: Prevent runaway loops
- **Predictable termination**: Always ends eventually
- **User protection**: No surprise $100 API bills

**Trade-off:** May terminate before complex goals complete.

## Component Breakdown

### 1. Schemas (`core/schemas.py`)

**Purpose:** Define the contracts between components.

**Key types:**
- `ActionType`: Enum of available actions
- `ActionDecision`: LLM output format
- `ActionResult`: Execution result format
- `AgentState`: Complete system state

**Why Pydantic?**
- Runtime validation
- Type hints for IDEs
- Automatic serialization
- Clear error messages

### 2. Decision Engine (`llm/decision_engine.py`)

**Purpose:** Interface to the LLM for decision-making.

**Key responsibilities:**
- Format prompts with state
- Call OpenAI API
- Parse and validate responses
- Track token usage

**Prompt design:**
```
System: You are an autonomous agent. You have 4 actions...
User: Goal: X. Current state: Y. History: Z. Decide next action.
```

**Why JSON mode?**
- Structured output is required
- Reduces parsing errors
- Works with response_format parameter

### 3. Action Executor (`actions/executor.py`)

**Purpose:** Execute actions in the real world.

**Implementation details:**

**search_web:**
- Uses DuckDuckGo HTML (no API key needed)
- Parses results with BeautifulSoup
- Returns structured data (title, URL, snippet)

**run_code:**
- Executes in subprocess (isolated from main process)
- Has timeout protection
- Captures stdout and stderr
- Runs in output directory (files persist)

**write_file:**
- Sanitizes filename (prevents path traversal)
- Writes to output directory
- Returns file metadata

**finish:**
- Simply marks completion
- Returns summary and artifacts list

### 4. Agent (`core/agent.py`)

**Purpose:** The main controller—runs the decision loop.

**Flow:**
```python
def run(goal):
    state = init_state(goal)
    
    while state.can_continue():
        # THE LOOP
        decision = decide_with_retry(state)
        result = execute_with_retry(decision)
        state.add_action(decision, result)
        
        if decision.action == FINISH and result.success:
            break
    
    return state
```

**Retry strategies:**
- Decision retry: LLM errors (invalid JSON, etc.)
- Execution retry: Transient failures (network, etc.)

**Termination conditions:**
1. Finish action succeeds (happy path)
2. Max steps reached (safety limit)
3. Decision fails after retries (stuck)

## State Evolution Example

```
Step 0:
  State: {goal: "Research X", actions: [], results: []}

Step 1:
  Decision: search_web("X")
  Result: [5 search results]
  State: {goal: "Research X", actions: [search_web], results: [...]}

Step 2:
  Decision: write_file("report.md", "...")
  Result: File written
  State: {goal: "Research X", actions: [search_web, write_file], results: [...]}

Step 3:
  Decision: finish("Report created")
  Result: Success
  State: {goal: "Research X", ..., is_complete: True}
```

Each decision is informed by complete history.

## Cost Model

**Token usage per step:**
- System prompt: ~500 tokens (fixed)
- State serialization: ~200-500 tokens (grows with history)
- LLM reasoning: ~100-200 tokens
- **Total per decision: ~1000-1500 tokens**

**For 20-step task:**
- ~20k-30k tokens total
- With GPT-4o-mini ($0.15/$0.60 per 1M): ~$0.30-0.60

**Optimization opportunities:**
1. Prompt caching (Anthropic offers 90% discount)
2. State summarization (compress old history)
3. Cheaper model for simple decisions
4. Batch actions (multiple steps at once)

## Error Handling Strategy

**Three layers:**

1. **Input validation** (before execution)
   - Pydantic validates schemas
   - Reject early, retry with error

2. **Execution errors** (during action)
   - Catch exceptions
   - Return ActionResult with error
   - LLM sees error in next decision

3. **Retry logic** (recovery)
   - Transient failures: retry same action
   - Persistent failures: LLM chooses different action
   - Max retries: move on or terminate

**Philosophy:** Fail gracefully, learn from errors, keep going.

## Testing Strategy

**Unit tests:**
- Schema validation
- Action executors (mock HTTP/subprocess)
- State management

**Integration tests:**
- Mock LLM (return fixed decisions)
- Test full loop with deterministic behavior

**End-to-end tests:**
- Real LLM, simple goals
- Assert on final state

## Trade-offs Summary

| Decision | Pro | Con | Verdict |
|----------|-----|-----|---------|
| Fixed actions | Reliability | Limited flexibility | Good for demo |
| Full state history | Context | Token usage | Add compression later |
| Plan-execute separation | Clean architecture | Added complexity | Worth it |
| Strict schemas | Type safety | Less LLM freedom | Essential |
| Hard limits | Safety | May truncate tasks | Necessary evil |

## Future Architecture Improvements

### 1. State Compression
After N steps, summarize old history:
```python
if len(state.actions) > 20:
    state.compressed_history = llm_summarize(state.actions[:15])
    state.actions = state.actions[15:]  # Keep recent
```

### 2. Action Registry
Make actions pluggable:
```python
@register_action("custom_action")
def my_action(input_data):
    ...
```

### 3. Parallel Execution
Some actions could run concurrently:
```python
if decision.allows_parallel():
    results = asyncio.gather(*[execute(a) for a in actions])
```

### 4. Hierarchical Planning
Break goals into subgoals:
```python
plan = llm_plan(goal)  # Returns subtasks
for subtask in plan:
    run_agent(subtask)  # Recursive
```

### 5. Memory System
Persistent memory across executions:
```python
agent.memory.store("learned that X API needs auth token")
agent.memory.retrieve("how to call X API")
```

## Conclusion

The architecture prioritizes:
1. **Clarity** over cleverness
2. **Reliability** over flexibility
3. **Debuggability** over abstraction
4. **Safety** over capability

This makes it excellent for demonstrating autonomous agents in a controlled, understandable way.

The goal is not to build the most powerful agent, but to show how to build a system where an LLM can make reliable decisions.

