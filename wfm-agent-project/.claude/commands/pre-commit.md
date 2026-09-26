---
description: Pre-commit check - run tests, review changes, flag sensitive files, propose a commit message (never commits)
argument-hint: [optional commit topic hint]
disable-model-invocation: true
shell: bash
allowed-tools: Bash(bash .claude/scripts/pre_commit_checks.sh)
---

Pre-commit review for this repo. Do NOT run `git add`, `git commit` or `git push` in this turn.

!`bash .claude/scripts/pre_commit_checks.sh`

## Commit topic hint from the user
$ARGUMENTS

## Your task
1. **Tests:** state pass/fail from the exit code above (0 = pass, 5 = no tests). If they fail, list the failing tests and stop recommending a commit until they are fixed.
2. **Changes:** summarize the modified, staged and new (`??`) files from the status and diff above.
3. **Sensitive files:** check the file lists above yourself (do not run shell commands that contain the env-file name; they are denied). Warn loudly if any path is:
   - a `settings.local.json`,
   - an env file (`.env` or `.env.*`),
   - anything under a `data/` folder (e.g. `wfm-agent-project/data/`: `wfm.xlsx`, generated charts).
   Recommend leaving them out of the commit (and adding them to `.gitignore` if they are untracked). If none, say so explicitly.
4. **Commit message:** propose one in English, following the repo style (`git log` subjects like `Area: short imperative summary`):
   - subject ≤ 72 chars,
   - blank line, then a body explaining **why** the change was made (not just what), wrapped at ~72 chars,
   - end with the Co-Authored-By trailer.
   Use the topic hint above if present; otherwise infer the topic from the diff. If needed, read the diff of specific files to understand the change.
   Also list exactly which files you would `git add` (never `git add -A` if a sensitive file is present).
5. **Stop.** Do not commit or push. Ask me to confirm the message and the file list.
