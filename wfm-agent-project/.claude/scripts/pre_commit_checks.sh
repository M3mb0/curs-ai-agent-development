#!/usr/bin/env bash
# Pre-commit checks for the /pre-commit slash command.
#
# Runs the pytest suite with the venv interpreter from the repo root
# (curs_agent_AI/), then prints the git status and the diff stat against HEAD.
# The logic lives here so that pre-commit.md can call one simple, statically
# analyzable command. Always exits 0: results are reported in the output.

set -u

ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$ROOT" ]; then
    echo "Not a git repository: cannot run pre-commit checks."
    exit 0
fi
if ! cd "$ROOT"; then
    echo "Cannot cd to the repo root: $ROOT"
    exit 0
fi

PYTHON="venv/Scripts/python.exe"

echo "## Tests (pytest, run from curs_agent_AI with the venv)"
if [ -x "$PYTHON" ]; then
    "$PYTHON" -m pytest wfm-agent-project/tests -q -p no:cacheprovider 2>&1 | tail -25
    PYTEST_EXIT=${PIPESTATUS[0]}
else
    echo "Python interpreter not found: $ROOT/$PYTHON"
    PYTEST_EXIT="n/a"
fi
echo "pytest exit code: $PYTEST_EXIT"
echo

echo "## git status --short (untracked files listed individually)"
git status --short --untracked-files=all
echo

echo "## git diff --stat against HEAD (staged + unstaged, tracked files; new files are the \`??\` lines above)"
git diff HEAD --stat

exit 0
