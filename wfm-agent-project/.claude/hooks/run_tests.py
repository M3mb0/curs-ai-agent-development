"""PostToolUse hook: run the pytest suite after Claude edits a .py file in wfm-agent-project.

Reads the hook payload (JSON) from stdin. If the edited file is a .py file inside
the project, runs pytest from the parent folder (curs_agent_AI/) with the venv
interpreter. Exit 0 with no output when tests pass or the file is irrelevant;
exit 2 with the failure summary on stderr so Claude Code feeds it back to Claude.
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = PROJECT_DIR.parent
PYTEST_TIMEOUT_SECONDS = 280
MAX_FEEDBACK_CHARS = 4000


def get_edited_file(payload):
    """Extract the edited file path from the hook payload.

    Args:
        payload (dict): PostToolUse hook input.

    Returns:
        Path | None: Resolved path of the edited file, or None if absent.
    """
    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or {}
    file_path = tool_input.get("file_path") or tool_response.get("filePath")
    return Path(file_path).resolve() if file_path else None


def is_project_python_file(path):
    """Check whether a path is a .py file inside wfm-agent-project.

    Args:
        path (Path | None): File path to check.

    Returns:
        bool: True if the hook should run the tests for this file.
    """
    return path is not None and path.suffix == ".py" and PROJECT_DIR in path.parents


def main():
    """Run the tests if needed and report the result through the exit code.

    Returns:
        int: 0 if tests pass or were skipped, 2 if they fail.
    """
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not is_project_python_file(get_edited_file(payload)):
        return 0

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "wfm-agent-project/tests",
             "-q", "--tb=short", "--no-header", "-p", "no:cacheprovider"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PYTEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"pytest timed out after {PYTEST_TIMEOUT_SECONDS}s.", file=sys.stderr)
        return 2

    # 0 = all passed, 5 = no tests collected: nothing to fix
    if result.returncode in (0, 5):
        return 0

    output = (result.stdout + result.stderr).strip()
    if len(output) > MAX_FEEDBACK_CHARS:
        output = "...(truncated)\n" + output[-MAX_FEEDBACK_CHARS:]
    print(f"pytest failed (exit {result.returncode}) after editing a .py file. "
          f"Fix the code or the tests:\n{output}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
