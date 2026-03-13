# AI Expense Auditor - Walkthrough

## Overview
I have fully designed and implemented the **AI Expense Audit Agent** according to the strict, 16-step FAANG architecture standard defined in [implementation_plan.md](file:///Users/saloniredij/.gemini/antigravity/brain/c1062ab5-4e0c-4882-b311-e913a809c603/implementation_plan.md). 

The system leverages:
- **FastAPI** for strict, typed, asynchronous API routing.
- **PostgreSQL & SQLAlchemy** for robust data persistence, and **Alembic** for schema migrations.
- **LangGraph & LangChain (OpenAI)** for orchestrating the AI classification pipeline.

## Core Features Implemented

### 1. Robust Data Layer
- Generic asynchronous repository pattern.
- Strict UUID tracking and timestamp mixins on all tables.
- PostgreSQL `ON CONFLICT DO UPDATE` (Upsert) to ensure the core `POST /transactions/ingest` endpoint is truly idempotent.

### 2. Async Agent Architecture
- The frontend API never blocks on slow LLM calls.
- `POST /audits` creates a pending job and immediately returns an HTTP 202 status.
- FastAPI `BackgroundTasks` executes the LangGraph pipeline out-of-core.
- You can poll `GET /audits/{id}` to see if the status is `pending`, `processing`, or `completed`.

### 3. Cost-saving Deterministic Pre-processing
- We do not send 90 days of raw CSV data blindly into an LLM context window.
- The first node in LangGraph deterministically aggregates transactions by `merchant_name`, computing counts and averages.
- Only merchants hit >1 times are forwarded to the LLM. This cuts OpenAI costs drastically and prevents context overflow.

### 4. Structured LLM Output
- Using `gpt-4-turbo-preview` with `.with_structured_output()`, we force the LLM to return data matching our Pydantic schema strictly.
- The model outputs clean arrays of `subscriptions_found` and `recommendations` without parsing raw markdown JSON.

## System Verification

The database is setup, Alembic migrations have been successfully generated and applied via Docker, and local test suites are green.

To start the API visually and test the Swagger Documentation:
1. Ensure the PostgreSQL `docker-compose up -d db` is running.
2. In the terminal, run: `venv/bin/uvicorn src.main:app --reload`
3. Navigate to `http://localhost:8000/v1/openapi.json` or `http://localhost:8000/docs`.

### Test Suite
You can verify the deterministic test behaviors via:
`venv/bin/pytest tests/`

## Next Steps
The system is ready for production staging testing. To actually get real responses, you simply need to provide an `OPENAI_API_KEY` into your local `.env` file!
