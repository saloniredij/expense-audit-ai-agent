# AI Expense Auditor

An AI agent that audits bank transactions and identifies wasteful spending using LangGraph and FastAPI.

## Setup

```bash
docker-compose up -d db
alembic upgrade head
python -m uvicorn src.main:app --reload
```
