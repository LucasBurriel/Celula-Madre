"""
Tools for the coding agent - bash + editor (same as DGM)
"""
import subprocess
import os
from pathlib import Path

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a bash command. Use for running tests, checking files, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to run."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "editor",
            "description": "View, create, or edit files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["view", "create", "edit"],
                        "description": "The command: view, create, or edit."
                    },
                    "path": {
                        "type": "string",
                        "description": "Absolute path to file or directory."
                    },
                    "file_text": {
                        "type": "string",
                        "description": "File content for create/edit commands."
                    }
                },
                "required": ["command", "path"]
            }
        }
    }
]


def execute_tool(tool_name, tool_args, workdir=None, timeout=120):
    """Execute a tool and return the result string."""
    if tool_name == "bash":
        return _run_bash(tool_args.get("command", ""), workdir=workdir, timeout=timeout)
    elif tool_name == "editor":
        return _run_editor(
            tool_args.get("command", "view"),
            tool_args.get("path", ""),
            tool_args.get("file_text"),
        )
    else:
        return f"Error: Unknown tool '{tool_name}'"


def _run_bash(command, workdir=None, timeout=120):
    if not command.strip():
        return "Error: empty command"
    try:
        result = subprocess.run(
            ["bash", "-c", command],
            capture_output=True, text=True, timeout=timeout, cwd=workdir,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\nSTDERR:\n" if output else "STDERR:\n") + result.stderr
        if not output:
            output = f"(exit code: {result.returncode})"
        return output[:10000]
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def _run_editor(command, path, file_text=None):
    try:
        path_obj = Path(path)

        if command == "view":
            if path_obj.is_dir():
                result = subprocess.run(
                    ["find", str(path_obj), "-maxdepth", "2", "-not", "-path", "*/\\.*"],
                    capture_output=True, text=True
                )
                return result.stdout[:10000]
            elif path_obj.is_file():
                content = path_obj.read_text()
                lines = content.split("\n")
                numbered = [f"{i+1:6}\t{line}" for i, line in enumerate(lines)]
                return "\n".join(numbered)[:10000]
            else:
                return f"Error: {path} does not exist"

        elif command == "create":
            if path_obj.exists():
                return f"Error: {path} already exists. Use 'edit' to overwrite."
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(file_text or "")
            return f"File created: {path}"

        elif command == "edit":
            if not path_obj.exists():
                path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(file_text or "")
            return f"File written: {path}"

        else:
            return f"Error: unknown command '{command}'"

    except Exception as e:
        return f"Error: {e}"
