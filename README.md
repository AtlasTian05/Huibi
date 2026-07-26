# HuiBi (慧笔)

[![tests](https://github.com/EthanTian05/Huibi/actions/workflows/tests.yml/badge.svg)](https://github.com/EthanTian05/Huibi/actions/workflows/tests.yml)
[![license](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)

An English writing feedback and personalized learning companion agent built with LangChain + LangGraph, designed for Chinese learners of English (general English writing / IELTS / TOEFL scenarios). Submit an English essay, and the system produces a structured reference score based on official public scoring rubrics, multi-dimensional qualitative feedback (bilingual, Chinese and English), suggestions for next practice steps, and tracks progress trends across submissions. Runs entirely locally, with no server deployment required.

![Product homepage screenshot](Docs/assets/screenshot-intro.png)

## Core Capabilities

- **Quantitative Scoring** — The LLM (DeepSeek V4 Pro) produces a structured reference score based on the public scoring rubric for the corresponding exam: IELTS Band Descriptors, TOEFL ETS single-task scoring guides, or the four-dimension standard for general English writing. The scoring prompt includes few-shot calibration examples to control scoring consistency.
- **Structured Qualitative Feedback** — Grammar correction (local rule base + LanguageTool), structural suggestions, and word-choice suggestions (with the ability to call a dictionary API to verify specific usage), presented bilingually in Chinese and English.
- **CriticAgentNode Reflection Loop** — After qualitative feedback is generated, it goes through a quality review pass (checking for vague boilerplate, internal contradictions, and actionable suggestions). Feedback that fails review is automatically sent back for a rewrite, capped at one retry.
- **IELTS Task 1 Chart/Image Description** — After an image is uploaded, GLM-4V-Flash first produces an objective description, then checks whether the essay's data is consistent with the chart and scores it against the Task Achievement rubric.
- **Personalized Learning Loop** — Combines historical submission records to produce learning trend charts and targeted practice recommendations.

## Architecture

A 9-node LangGraph state graph: `intake_validator → image_analysis → retrieval_agent → grammar_check → feedback_agent → critic_agent → coach_agent → progress_tracker` (validation failures short-circuit to `short_circuit_reject`). For the full node responsibility table, routing logic, and RAG knowledge base design, see [`Docs/01-系统架构与Agent设计.md`](Docs/01-系统架构与Agent设计.md).

| Layer | Technology |
|---|---|
| Agent Orchestration | LangChain + LangGraph |
| Primary LLM | DeepSeek V4 Pro (free fallback: GLM-4.7-Flash) |
| Vision Understanding | GLM-4V-Flash (IELTS Task 1 chart recognition) |
| RAG Retrieval | Chroma + `BAAI/bge-small-en-v1.5` (local embedding) |
| Frontend | Streamlit (three pages: product intro / login-register / workbench) |
| Persistence | PostgreSQL (`psycopg` v3 with native JSONB) |

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env   # Fill in your real API keys, see "Environment Variables" below
python -m src.rag.build_kb   # Build the RAG knowledge base (embeds Markdown material from data/kb/ into local Chroma)
streamlit run app.py
```

On Windows, double-click [`启动慧笔.bat`](启动慧笔.bat) to skip manual commands (it automatically checks whether PostgreSQL and the RAG knowledge base are ready). See [`Docs/03-RUNNING.md`](Docs/03-RUNNING.md) for the complete setup/run/test steps.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

- `DEEPSEEK_API_KEY` / `GLM_API_KEY`: used for qualitative feedback, coaching suggestions, and knowledge-base Q&A — see the "Environment Variables" section of [`Docs/03-RUNNING.md`](Docs/03-RUNNING.md)
- `POSTGRES_HOST`/`PORT`/`DB`/`USER`/`PASSWORD`: local database connection

`.env` is already excluded in `.gitignore` — do not commit it, and do not paste its real values into any document.

## Testing

```bash
pytest                                        # Zero-dependency unit tests (scoring logic/validation/routing functions), run by CI
python scripts/smoke_test_nodes.py            # Equivalent pip-free smoke test script
PYTHONPATH=. python scripts/e2e_graph_test.py # Full pipeline, including real DeepSeek calls + local PostgreSQL, run manually
```

The `pytest` suite (`tests/`) covers score normalization, essay length validation, the grammar rule base, the CriticAgentNode short-circuit branch, and LangGraph routing functions. It requires no API key or database and runs automatically on every push via GitHub Actions (see badge above). The full end-to-end pipeline (real LLM calls, image understanding, database read/write) requires local PostgreSQL and API keys, so it is manually verified and not run in CI.

## Scoring Methods

For the three currently supported essay types — GENERAL (general English writing assessment), IELTS, and TOEFL — quantitative scoring is uniformly produced by the LLM based on the corresponding public scoring rubric (IELTS Band Descriptors, TOEFL ETS single-task scoring guides, and the four-dimension standard for GENERAL writing); see `src/official_rubrics.py`. Scoring, qualitative feedback, and coaching suggestions all use DeepSeek V4 Pro (free fallback: GLM-4.7-Flash). **This is a simulated review and does not represent an official score from any testing organization.**

The `retrieval_agent_node` (RAG retrieval) in `src/agents/nodes.py` automatically falls back to a placeholder result when `data/processed/chroma_kb/` is not found — **it will not crash** — but it prints a clear `warnings.warn(...)` message telling you which command to run to complete the setup.

## Project Documentation

- [`CLAUDE.md`](CLAUDE.md): project background, confirmed design decisions, environment info, lessons learned
- [`Docs/01-系统架构与Agent设计.md`](Docs/01-系统架构与Agent设计.md): LangGraph state graph, node responsibility table, RAG knowledge base design
- [`Docs/02-Progress.md`](Docs/02-Progress.md): round-by-round work log (root cause / fix / verification method)
- [`Docs/03-RUNNING.md`](Docs/03-RUNNING.md): complete environment setup/run/test steps
- [`Docs/TODO.md`](Docs/TODO.md): pending tasks and open decisions
