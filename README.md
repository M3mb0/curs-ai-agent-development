# WFM Agent — AI Agent Development course project

A multi-agent assistant for **workforce management (WFM)** in a contact center, built with LangGraph on Google Gemini. It answers questions about a contact-center dataset (`wfm.xlsx`): call volumes, service level, abandon rate, talk time, day-to-day comparisons, volume forecasts, break distribution and capacity. It also answers procedure and SLA questions from a small markdown knowledge base using RAG.

The project was built step by step during an AI Agent Development course. This repository also holds the per-lesson exercises and my course notes.

## Features

- **LangGraph multi-agent graph** (`src/agents/supervisor.py`): a `supervisor` node chooses the next step, an `extractor` node parses parameters (language, LOB, dates, target volume, weekday, meeting times…), specialist nodes run the tools, and a `writer` node formats the final answer. The loop is capped at 10 iterations.
- **Conversation memory:** a `MemorySaver` checkpointer keyed by `thread_id`, so follow-up questions work (e.g. *"What about LOB 2?"*).
- **Model routing:** `gemini-3.5-flash-lite` handles classification, routing, extraction and writing. `gemini-3.6-flash` handles analysis and reasoning.
- **WFM tools** (plain Python, no LLM logic):
  - `src/tools/wfm_data.py`: daily metrics, service level and abandon rate, talk time for a period, comparing two days, forecasts from a historical date or a weekday pattern, call distribution by language, and a timezone-shifted column.
  - `src/tools/capacity_planning.py`: break distribution across shifts (optionally avoiding team meetings), staffing and capacity per interval.
- **RAG** (`src/rag/`): the documents in `data/kb_documents/*.md` are split into 500-token chunks with 50 tokens of overlap (tiktoken), embedded with `gemini-embedding-001` (3072 dimensions) and stored in PostgreSQL with `pgvector`. A query returns the 3 closest chunks by cosine distance, with an in-memory cache.
- **Guardrails** (`safe_process_question`): a per-user rate limit, a 500-character input limit, an LLM prompt-injection classifier and an LLM output filter. They are fail-closed: if a check can't run, the request is rejected. Gemini API errors are mapped to `LLMUnavailableError` (temporary) or `LLMConfigError` (permanent) in `src/exceptions/custom_errors.py`.
- **MCP server** (`src/mcp_server.py`): exposes the same WFM tools and the knowledge-base search as MCP tools, so clients such as Claude Desktop can call them directly.
- **Azure deployment (exercise):** `Lectia_11/azure_function_project/` is a standalone HTTP Azure Function (`/api/hello`). It was deployed with Azure Functions Core Tools and the Azure resources were deleted afterwards. The WFM agent itself is **not** deployed to Azure, because it needs PostgreSQL and persistent conversation memory, which don't fit the stateless free tier of Azure Functions.
- **Tests** (`wfm-agent-project/tests/`): pytest covers the deterministic code (`tools/`, RAG loading and chunking). LLM error handling and guardrails are tested with monkeypatching, and no test calls the Gemini API.
- **Claude Code tooling** (`wfm-agent-project/.claude/`): a hook that runs pytest after Python edits, a `/pre-commit` command (tests plus sensitive-file checks), and a read-only `code-reviewer` subagent.

## Project structure

```
curs_agent_AI/
├── wfm-agent-project/
│   ├── src/
│   │   ├── main.py              # interactive CLI chat
│   │   ├── mcp_server.py        # MCP server entry point
│   │   ├── config.py            # loads .env, model name, DB_CONFIG
│   │   ├── agents/              # LangGraph graph: supervisor, extractor, tool nodes, writer, guardrails
│   │   ├── tools/               # WFM data and capacity-planning functions
│   │   ├── rag/                 # document loader, chunking, embeddings, vector store, search
│   │   └── exceptions/          # custom LLM error types
│   ├── data/
│   │   ├── kb_documents/        # knowledge-base markdown files used by RAG
│   │   └── wfm.xlsx             # dataset (git-ignored, not in the repo)
│   ├── tests/                   # pytest suite
│   ├── .claude/                 # Claude Code hook, command, subagent, settings
│   └── CLAUDE.md                # guidance for Claude Code
├── Lectia_1 … Lectia_11/        # per-lesson exercises (Gemini API, RAG, LangGraph, MCP, Azure Functions…)
├── Teme/                        # homework
└── Curs_AI_Agent_Notite.md      # course notes (Romanian)
```

## Setup

Requirements: Python 3.12 and a local PostgreSQL with the `pgvector` extension (needed only for RAG).

```powershell
# from the repo root (curs_agent_AI/)
python -m venv venv
venv\Scripts\Activate.ps1
pip install langgraph langchain-google-genai google-genai pandas openpyxl matplotlib psycopg2 tiktoken python-dotenv mcp pytest
```

Create a `.env` file in the repo root with these variables:

```
GEMINI_API_KEY=
DB_PASSWORD=

# optional, for LangSmith tracing
LANGSMITH_TRACING=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
```

Database: start PostgreSQL with `pgvector` (for example the `pgvector/pgvector` Docker image) and adjust `DB_CONFIG` in `wfm-agent-project/src/config.py` to match your instance. Then build the RAG index once:

```powershell
python wfm-agent-project/src/rag/vector_store.py
```

Place the dataset at `wfm-agent-project/data/wfm.xlsx`.

## Running

Run all commands from the repo root (`curs_agent_AI/`), because data paths are relative to it.

```powershell
# interactive agent chat (type "exit" to quit)
python wfm-agent-project/src/main.py

# MCP server, e.g. for Claude Desktop
python wfm-agent-project/src/mcp_server.py
```

The agent uses Gemini's free tier. One question takes roughly 5–7 flash-lite calls, so the CLI is rate-limited to about 2 questions per minute.

## Tests

```powershell
# all tests
pytest wfm-agent-project/tests

# a single test
pytest wfm-agent-project/tests/test_wfm_data.py::test_get_daily_metrics
```

The tests need `data/wfm.xlsx` locally. They don't call the Gemini API.

## Not included in the repo

- `wfm-agent-project/data/wfm.xlsx`: private WFM data, git-ignored.
- `.env`: API keys, git-ignored.

Both must be created locally before running the agent or the tests.

## Course notes

[`Curs_AI_Agent_Notite.md`](Curs_AI_Agent_Notite.md) holds my notes, in Romanian, from the AI Agent Development course, lessons 1–15:

- **Lessons 1–12:** LLM APIs and tool calling, prompts and observability (LangSmith), document processing, databases and RAG (pgvector), LangGraph state and workflows, multi-agent orchestration, ML optimization, memory and caching, guardrails and security, the Model Context Protocol, cloud deployment on Azure, and fine-tuning/RLHF (theory only).
- **Lesson 13, Claude Code:** `CLAUDE.md`, permissions, hooks, custom commands and subagents.
- **Lesson 14, Cowork:** using the project's MCP server from another agent, building an Excel report for the WFM case study, and turning it into a reusable skill and scheduled task.
- **Lesson 15, n8n / Make / Zapier:** no-code automations, including a self-hosted n8n in Docker and an n8n AI agent.
