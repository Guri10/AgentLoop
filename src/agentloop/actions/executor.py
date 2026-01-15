"""
Action executor implementations.

Each action is executed by the system (not the LLM).
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import requests
from bs4 import BeautifulSoup

from ..core.schemas import (
    ActionResult,
    ActionType,
    SearchWebInput,
    RunCodeInput,
    WriteFileInput,
    FinishInput,
)


class ActionExecutor:
    """Executes actions and returns observations."""
    
    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the action executor.
        
        Args:
            output_dir: Directory where files will be written
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
    
    def execute(self, action_type: ActionType, input_data: Dict[str, Any]) -> ActionResult:
        """
        Execute an action and return the result.
        
        Args:
            action_type: The type of action to execute
            input_data: Input parameters for the action
            
        Returns:
            ActionResult with success status and output/error
        """
        handlers = {
            ActionType.SEARCH_WEB: self._search_web,
            ActionType.RUN_CODE: self._run_code,
            ActionType.WRITE_FILE: self._write_file,
            ActionType.FINISH: self._finish,
        }
        
        handler = handlers.get(action_type)
        if not handler:
            return ActionResult(
                action=action_type,
                success=False,
                error=f"Unknown action type: {action_type}"
            )
        
        try:
            return handler(input_data)
        except Exception as e:
            return ActionResult(
                action=action_type,
                success=False,
                error=f"Execution error: {str(e)}"
            )
    
    def _search_web(self, input_data: Dict[str, Any]) -> ActionResult:
        """
        Execute web search action.
        
        Uses DuckDuckGo HTML search (no API key required).
        """
        try:
            search_input = SearchWebInput(**input_data)
            
            # Use DuckDuckGo HTML search
            url = "https://html.duckduckgo.com/html/"
            params = {"q": search_input.query}
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            response = requests.post(url, data=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse results
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            
            for result_div in soup.find_all("div", class_="result")[:search_input.num_results]:
                title_elem = result_div.find("a", class_="result__a")
                snippet_elem = result_div.find("a", class_="result__snippet")
                
                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": title_elem.get("href", ""),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                    })
            
            if not results:
                return ActionResult(
                    action=ActionType.SEARCH_WEB,
                    success=False,
                    error="No search results found"
                )
            
            return ActionResult(
                action=ActionType.SEARCH_WEB,
                success=True,
                output=results,
                metadata={"query": search_input.query, "num_results": len(results)}
            )
            
        except Exception as e:
            return ActionResult(
                action=ActionType.SEARCH_WEB,
                success=False,
                error=f"Search failed: {str(e)}"
            )
    
    def _run_code(self, input_data: Dict[str, Any]) -> ActionResult:
        """
        Execute Python code in a subprocess.
        
        Runs code in isolated subprocess for safety.
        """
        try:
            code_input = RunCodeInput(**input_data)
            
            # Execute code in subprocess
            result = subprocess.run(
                [sys.executable, "-c", code_input.code],
                capture_output=True,
                text=True,
                timeout=code_input.timeout,
                cwd=str(self.output_dir)
            )
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            
            success = result.returncode == 0
            
            return ActionResult(
                action=ActionType.RUN_CODE,
                success=success,
                output=output.strip() if output else "Code executed successfully (no output)",
                error=None if success else f"Exit code {result.returncode}",
                metadata={
                    "exit_code": result.returncode,
                    "execution_time": "N/A"  # Could add timing if needed
                }
            )
            
        except subprocess.TimeoutExpired:
            return ActionResult(
                action=ActionType.RUN_CODE,
                success=False,
                error=f"Code execution timed out after {code_input.timeout} seconds"
            )
        except Exception as e:
            return ActionResult(
                action=ActionType.RUN_CODE,
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    def _write_file(self, input_data: Dict[str, Any]) -> ActionResult:
        """Write content to a file."""
        try:
            write_input = WriteFileInput(**input_data)
            
            # Ensure filename is safe (no path traversal)
            safe_filename = Path(write_input.filename).name
            filepath = self.output_dir / safe_filename
            
            # Write file
            filepath.write_text(write_input.content, encoding="utf-8")
            
            return ActionResult(
                action=ActionType.WRITE_FILE,
                success=True,
                output=f"File written successfully: {filepath}",
                metadata={
                    "filepath": str(filepath),
                    "size_bytes": len(write_input.content.encode("utf-8"))
                }
            )
            
        except Exception as e:
            return ActionResult(
                action=ActionType.WRITE_FILE,
                success=False,
                error=f"File write failed: {str(e)}"
            )
    
    def _finish(self, input_data: Dict[str, Any]) -> ActionResult:
        """Mark task as complete."""
        try:
            finish_input = FinishInput(**input_data)
            
            return ActionResult(
                action=ActionType.FINISH,
                success=True,
                output={
                    "summary": finish_input.summary,
                    "artifacts": finish_input.artifacts
                },
                metadata={"completed": True}
            )
            
        except Exception as e:
            return ActionResult(
                action=ActionType.FINISH,
                success=False,
                error=f"Finish action failed: {str(e)}"
            )

