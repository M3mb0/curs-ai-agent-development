# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

- The git repo root is the parent folder `curs_agent_AI/` (a course repo); this project lives in `wfm-agent-project/`. The Python venv (`venv/`) and `.env` (`GEMINI_API_KEY`) live in the parent folder.
- **Run everything from the parent folder `curs_agent_AI/`.** Data paths are hardcoded relative to it (e.g. `"wfm-agent-project/data/wfm.xlsx"` in `src/agents/supervisor.py` and in the tests). Only `src/mcp_server.py` resolves paths from `__file__`.
- `data/wfm.xlsx` is gitignored — it must exist locally.
- RAG requires a local PostgreSQL with the `pgvector` extension (`DB_CONFIG` in `src/config.py`).
- No requirements file; key deps: `langgraph`, `langchain-google-genai`, `google-genai`, `pandas`, `openpyxl`, `matplotlib`, `psycopg2`, `tiktoken`, `python-dotenv`, `mcp`, `pytest`.
- No packaging: each module does `sys.path.append(...)` so that `src/` is the import root (`from tools.wfm_data import ...`, `from rag.search import ...`). Follow the same pattern in new modules/tests.

## Commands (from `curs_agent_AI/`, venv active: `venv\Scripts\Activate.ps1`)

- Interactive agent chat: `python wfm-agent-project/src/main.py` (type `exit` to quit)
- MCP server (for Claude Desktop etc.): `python wfm-agent-project/src/mcp_server.py`
- Build the RAG index (one-off; embeds `data/kb_documents/*.md` into table `kb_chunks`): `python wfm-agent-project/src/rag/vector_store.py`
- All tests: `pytest wfm-agent-project/tests`
- Single test: `pytest wfm-agent-project/tests/test_wfm_data.py::test_get_daily_metrics`

Tests intentionally cover only deterministic code (`tools/`, RAG loading/chunking). Anything calling Gemini (embeddings, search, extractor, supervisor routing) is validated manually to avoid API cost/rate limits — don't add tests that hit the API.

## Architecture

LangGraph multi-agent over Gemini. Everything graph-related is in `src/agents/supervisor.py`; `src/tools/` and `src/rag/` hold plain functions with no LLM logic.

**Request flow:** `main.py` → `graph.invoke({"question", "iteration_count": 0}, thread_id)` → `supervisor` node picks the next step (one-word LLM answer) → a specialist node runs and writes its text output to `state["tool_result"]` + sets `last_tool` → back to `supervisor` → … → `done` → `writer` node (LLM formats final answer, always adds a suggestion) → `END`. Loop is capped at 10 iterations.

- **Nodes:** `extractor` (LLM parses `language/lob/date/date2/target_volume/weekday/offset_hours/column_name/meeting_times` in a `key=value;...` format, `none` if absent), `rag` (pgvector search), and tool nodes that wrap `tools/wfm_data.py` (metrics, service_level, talktime, compare_days, forecast, forecast_weekday, distribution, timezone) or `tools/capacity_planning.py` (breaks, breaks_meetings, capacity). Each tool node converts the function's dict to text.
- **Adding a tool:** implement the pure function in `tools/`, add a node in `supervisor.py`, register it with `add_node` + edge back to `supervisor` + entry in `add_conditional_edges`, describe it in the supervisor system prompt (and the allowed one-word list), add to `tools_needing_params` if it needs extracted params, and optionally expose it in `mcp_server.py`.
- **Memory:** `MemorySaver` checkpointer keyed by `thread_id`. State persists across turns; the extractor keeps previous values when a param is `none`, enabling follow-ups like "What about LOB 2?". The supervisor has a deterministic shortcut: if `last_tool` is a param-based tool, `lob` is set and `tool_result == "none"` (just reset by the extractor), it reroutes to that same tool without asking the LLM.
- **Model routing:** `route_by_complexity()` — `gemini-3.5-flash-lite` for routing/extraction/writing, `gemini-3.6-flash` for analysis/reasoning. Automatic function calling is disabled in `get_llm()`.
- **Guardrails** (`safe_process_question`: rate limit, length check, LLM prompt-injection classifier, LLM output filter) wrap `graph.invoke`, but `main.py` currently calls the graph directly, bypassing them.
- **Data loading:** `df`, `arrival_pattern`, `site_params` are loaded from `wfm.xlsx` at import time of `supervisor.py` / `mcp_server.py`.
- **RAG:** ingestion `document_loader` → `chunking` (500 tokens, 50 overlap, tiktoken `cl100k_base`) → `embeddings` (`gemini-embedding-001`, 3072 dims, retry on `RateLimitError`) → `vector_store`. Query: `search.cached_search` (in-memory cache) → cosine distance `<=>`, top 3.
- `mcp_server.py` is a separate entry point exposing the same `tools/` and `rag/` functions as MCP tools; it does not use the graph.

## Conventions

- Google-style docstrings (Args/Returns) on every function and a module docstring at the top of each file.
