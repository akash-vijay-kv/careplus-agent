"""Shell command toolkit for executing system commands.

Provides the agent with the ability to run shell commands on the host system.
This is intentionally provided with minimal restrictions for diagnostic and
administrative use cases.
"""

import json
import subprocess

from agno.tools import Toolkit

COMMAND_TIMEOUT_SECONDS = 30
MAX_OUTPUT_LENGTH = 10000


class ShellTools(Toolkit):
    """Tools for executing shell commands on the host system."""

    def __init__(self, **kwargs) -> None:
        """Initialize shell tools."""
        tools = [self.run_command]
        super().__init__(name="shell_tools", tools=tools, **kwargs)

    def run_command(self, command: str) -> str:
        """Execute a shell command and return its output.

        Use this tool to run system commands for diagnostics, file lookups,
        or administrative tasks.

        Args:
            command: The shell command string to execute (e.g. 'ls -la /tmp').

        Returns:
            JSON string with stdout, stderr, and the return code.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
            )

            stdout = result.stdout[:MAX_OUTPUT_LENGTH]
            stderr = result.stderr[:MAX_OUTPUT_LENGTH]

            return json.dumps({
                "status": "success",
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            })
        except subprocess.TimeoutExpired:
            return json.dumps({
                "status": "error",
                "message": f"Command timed out after {COMMAND_TIMEOUT_SECONDS} seconds.",
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Command execution failed: {str(e)}",
            })
