"""
Streamlit Web Interface for AgentLoop.

A visual interface for running the autonomous agent with real-time execution display.
"""

import os
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from src.agentloop.main import create_agent
from src.agentloop.core.schemas import ActionType, AgentState

# Load environment
load_dotenv()

# Page config
st.set_page_config(
    page_title="AgentLoop - Autonomous Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
    .step-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    # Use session-specific IDs to prevent cross-user contamination
    if "execution_history" not in st.session_state:
        st.session_state.execution_history = []
    if "current_state" not in st.session_state:
        st.session_state.current_state = None
    if "is_running" not in st.session_state:
        st.session_state.is_running = False
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())[:8]


def display_header():
    """Display the app header."""
    st.markdown('<div class="main-header">AgentLoop</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #666;'>"
        "Autonomous Agent System with LLM-based Decision Making"
        "</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")


def sidebar_config():
    """Render sidebar configuration."""
    with st.sidebar:
        st.header("Configuration")
        
        # Check if API key exists (from Streamlit secrets or env)
        api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        
        if not api_key:
            st.error("API key not configured. Please contact the administrator.")
            st.stop()
        
        # Set in environment (hidden from users)
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Show that API is configured (but not the key itself)
        st.success("API Key: Configured")
        st.caption("Using administrator's API key")
        
        # Model selection
        model = st.selectbox(
            "Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            index=0,
            help="OpenAI model to use for decision making"
        )
        
        # Max steps
        max_steps = st.slider(
            "Max Steps",
            min_value=5,
            max_value=100,
            value=30,
            help="Maximum number of decision steps"
        )
        
        # Output directory (session-specific to prevent cross-contamination)
        output_dir = f"./output/streamlit_{st.session_state.session_id}"
        
        st.markdown("---")
        
        # Info
        st.subheader("About")
        st.markdown("""
        **AgentLoop** demonstrates autonomous agents with:
        - Explicit decision loop
        - Goal-driven behavior
        - Error recovery
        - Full observability
        
        **Note:** This is a demo using the author's API key. 
        Please be considerate with usage.
        
        [GitHub](https://github.com/Guri10/AgentLoop) | 
        [PyPI](https://pypi.org/project/autonomous-agentloop/)
        """)
        
        return {
            "model": model,
            "max_steps": max_steps,
            "output_dir": output_dir
        }


def display_execution_status(state: AgentState):
    """Display current execution status."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Steps", f"{state.current_step}/{state.max_steps}")
    
    with col2:
        success_rate = (
            sum(1 for r in state.action_results if r.success) / len(state.action_results) * 100
            if state.action_results else 0
        )
        st.metric("Success Rate", f"{success_rate:.0f}%")
    
    with col3:
        st.metric("Cost", f"${state.total_cost:.4f}")
    
    with col4:
        status = "✅ Complete" if state.is_complete else "🔄 Running"
        st.metric("Status", status)
    
    # Progress bar
    progress = state.current_step / state.max_steps if state.max_steps > 0 else 0
    st.progress(progress)


def display_action_history(state: AgentState):
    """Display action history."""
    st.subheader("📝 Execution History")
    
    if not state.actions_taken:
        st.info("No actions taken yet. Agent will start soon...")
        return
    
    # Show recent actions (last 10)
    recent_actions = list(zip(state.actions_taken, state.action_results))[-10:]
    
    for i, (action, result) in enumerate(reversed(recent_actions)):
        step_num = len(state.actions_taken) - i
        
        status_icon = "✅" if result.success else "❌"
        action_color = "#28a745" if result.success else "#dc3545"
        
        with st.expander(
            f"{status_icon} Step {step_num}: {action.action.value}",
            expanded=(i == 0)
        ):
            st.markdown(f"**Reasoning:** {action.reasoning}")
            
            if result.success:
                st.markdown(f'<div class="success-box">', unsafe_allow_html=True)
                st.markdown(f"**Result:** {result.output}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">', unsafe_allow_html=True)
                st.markdown(f"**Error:** {result.error}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Show input details
            with st.container():
                st.markdown("**Input:**")
                st.json(action.input)


def run_agent_with_ui(goal: str, config: dict):
    """Run agent and update UI in real-time."""
    try:
        # Check API key
        if not os.getenv("OPENAI_API_KEY"):
            st.error("API key not configured. Please contact the administrator.")
            return
        
        # Create agent
        agent = create_agent(
            output_dir=config["output_dir"],
            max_steps=config["max_steps"],
            model=config["model"],
            verbose=False  # We'll handle display ourselves
        )
        
        # Run agent
        st.session_state.is_running = True
        
        with st.spinner("🤖 Agent is thinking and executing..."):
            state = agent.run(goal)
        
        st.session_state.current_state = state
        st.session_state.is_running = False
        
        # Success message
        if state.is_complete:
            st.success("🎉 Task completed successfully!")
        else:
            st.warning("⚠️ Task incomplete (reached max steps or encountered issues)")
        
        return state
        
    except Exception as e:
        st.session_state.is_running = False
        st.error(f"❌ Error: {str(e)}")
        return None


def display_generated_files(output_dir: str):
    """Display and allow download of generated files."""
    from pathlib import Path
    
    output_path = Path(output_dir)
    if not output_path.exists():
        return
    
    files = list(output_path.glob("*"))
    if not files:
        return
    
    st.subheader("📁 Generated Files")
    
    for file in files:
        if file.is_file():
            with st.expander(f"📄 {file.name}"):
                try:
                    content = file.read_text(encoding="utf-8")
                    st.text_area(
                        "Content",
                        value=content,
                        height=200,
                        key=f"file_{file.name}"
                    )
                    
                    st.download_button(
                        label="⬇️ Download",
                        data=content,
                        file_name=file.name,
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Could not read file: {e}")


def main():
    """Main application."""
    init_session_state()
    display_header()
    
    # Sidebar configuration
    config = sidebar_config()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Enter Your Goal")
        goal = st.text_area(
            "What would you like the agent to do?",
            value="Research recent developments in small language models and create a summary report",
            height=100,
            help="Describe what you want the agent to accomplish"
        )
        
        # Action buttons
        button_col1, button_col2 = st.columns([1, 4])
        with button_col1:
            run_button = st.button(
                "▶️ Run Agent",
                type="primary",
                disabled=st.session_state.is_running,
                use_container_width=True
            )
        
        if run_button and goal:
            state = run_agent_with_ui(goal, config)
    
    with col2:
        # Example goals
        st.subheader("💡 Example Goals")
        examples = [
            "Calculate first 20 Fibonacci numbers and analyze them",
            "Search for Python 3.12 new features and list top 5",
            "Research AI agent frameworks and create comparison table",
        ]
        
        for ex in examples:
            if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
                st.session_state.example_goal = ex
                st.rerun()
    
    # Display execution status if agent has run
    if st.session_state.current_state:
        st.markdown("---")
        display_execution_status(st.session_state.current_state)
        
        # Two columns for history and files
        hist_col, file_col = st.columns([2, 1])
        
        with hist_col:
            display_action_history(st.session_state.current_state)
        
        with file_col:
            display_generated_files(config["output_dir"])


if __name__ == "__main__":
    main()

