# AI Expense Audit Agent - Implementation Plan

## 1. Restate and validate the problem
**Problem:** Consumers and small businesses leak capital via unused subscriptions, forgotten recurring payments, and unnoticed price hikes.
**Validation:** The problem is real and measurable. Bank statements are voluminous and noisy. Rule-based parsers fail on ambiguous merchant names and dynamic pricing. An AI-driven approach is justified to semantically classify transactions and infer recurring intent.

## 2. List assumptions and challenge weak ones
- *Assumption:* We have raw transaction data. *Challenge:* How do we get it? Plaid? CSV uploads? *Decision:* System will expose an agnostic ingestion API. Aggregation (Plaid) is out of scope for the core engine but supported via contract.
- *Assumption:* LLM can process all transactions. *Challenge:* LLMs have token limits and hallucinate. Passing 10,000 transactions to an LLM is slow and costly. *Decision:* We will pre-filter and aggregate transactions using deterministic rules (e.g., grouping by merchant, filtering small one-offs) before passing candidate recurring clusters to the LLM agent.
- *Assumption:* Users want automatic cancellations. *Challenge:* Too risky. *Decision:* System is read-only. It generates actionable recommendations (Action Plan) but does not mutate external bank state.

## 3. Define functional requirements
- System must accept and store raw banking transactions idempotently.
- System must identify recurring subscriptions and regular bills (utilities, etc.).
- System must detect distinct but similar subscriptions (duplicate detection).
- System must generate a monthly savings report with concrete recommendations.
- System must expose an API to trigger audits and retrieve results.

## 4. Define non-functional requirements
- **Scalability:** Should handle bursts of transaction ingestion (10k+ rows per user) efficiently.
- **Availability:** API must be 99.9% available. Audit processing can be asynchronous.
- **Data Correctness:** Financial data must never be lost, corrupted, or misattributed.
- **Security:** Transactions contain PII. Must encrypt data at rest. Multi-tenant isolation at the database level (tenant ID on all tables).
- **Idempotency:** Ingesting the same transactions twice must not duplicate data.

## 5. Propose a high-level architecture
The system is an asynchronous, API-first platform:
1. **Sync Ingestion API:** FastAPI accepts transactions, validates payload, and strictly persists to PostgreSQL.
2. **Async Audit Engine:** An event-driven worker (or background task) invokes the LangGraph Agent pipeline.
3. **Agent Pipeline:** 
   - *Node 1: Pre-processing* (Groups transactions, calculates frequencies deterministically).
   - *Node 2: LLM Classification* (Identifies subscriptions, identifies duplicates).
   - *Node 3: Recommendation Engine* (Generates savings plan).
4. **Data Store:** PostgreSQL for relational persistence (Transactions, Subscriptions, Reports).

## 6. Deep-dive into each major component
- **FastAPI Layer:** Strict Pydantic validation. Rate-limited. Uses dependency injection for services.
- **Data Layer:** SQLAlchemy ORM. Strict UUID primary keys. Timestamped records. Soft deletes for user data.
- **LangGraph Agent:** 
  - Uses a state graph containing `TransactionContext`, `IdentifiedSubscriptions`, and `DraftReport`.
  - Tools are pure Python functions that the LLM invokes (e.g., `calculate_annual_cost()`, `search_cheaper_alternatives()`).
  - LLM strictly returns Pydantic models (structured output) to enforce typing. No raw string parsing.

## 7. Define data models and schemas
```sql
CREATE TABLE users (id UUID PRIMARY KEY, created_at TIMESTAMPTZ);
CREATE TABLE bank_accounts (id UUID PRIMARY KEY, user_id UUID, mask VARCHAR);
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES bank_accounts,
    external_id VARCHAR UNIQUE, -- For idempotency
    date DATE,
    amount DECIMAL(12,2),
    merchant_name VARCHAR,
    description TEXT
);
CREATE TABLE audit_reports (
    id UUID PRIMARY KEY,
    user_id UUID,
    status VARCHAR (pending, completed, failed),
    raw_result JSONB,
    created_at TIMESTAMPTZ
);
```

## 8. Define APIs and contracts
All APIs versioned under `/v1/`.
- `POST /v1/transactions/ingest`
  - Input: List of transactions.
  - Contract: Upserts by `external_id`.
- `POST /v1/audits`
  - Input: `user_id`.
  - Output: `audit_id` (Async HTTP 202 Accepted).
- `GET /v1/audits/{audit_id}`
  - Output: Status and Report JSON.

## 9. Explain data flow and control flow
1. Client POSTs transactions. DB upserts.
2. Client POSTs `/audits`. DB creates `audit_reports` entry (`status: pending`).
3. Background worker picks up audit.
4. Worker fetches last 90 days of transactions for the user.
5. LangGraph workflow executes.
6. Worker saves output to `audit_reports` (`status: completed`).
7. Client GETs the report.

## 10. Explain scaling strategy
- **Compute:** FastAPI is stateless. Can scale horizontally behind a load balancer. LangGraph workers can be decoupled into Celery/Temporal workers if CPU/LLM wait times become a bottleneck.
- **Database:** Postgres scales vertically well. Indexes on `(user_id, date)` and `external_id`.
- **LLM Rate Limits:** Requests to OpenAI/Claude will be wrapped in exponential backoff and retry logic.

## 11. Explain failure scenarios and recovery mechanisms
- *LLM API Outage:* Worker fails, `audit_reports` marked `failed`. Client can retry later.
- *LLM Hallucination:* LLM output is strictly validated via Pydantic. If validation fails, agent retries up to 3 times before failing the audit.
- *DB Connection Drops:* Services use connection pooling with automatic reconnection.

## 12. Explain deployment and rollback strategy
- **Migrations:** Expand-migrate-contract. Never drop columns in the same release as code changes.
- **Deployment:** Dockerized containers. Blue/Green deployment using Kubernetes or ECS.
- **Rollback:** If API error rates spike >1%, automated traffic shift back to Blue environment.

## 13. Explain testing strategy
- **Unit Tests:** Pytest for all deterministic functions (Savings Calculator, Pre-processor).
- **Integration Tests:** Testcontainers (PostgreSQL) for DB queries and API endpoints.
- **Contract Tests:** Verify Pydantic schemas against external API specs.
- **LLM Evals:** We cannot use standard unit tests for LLMs. We will have a golden dataset of 50 transaction histories to test the LangGraph agent's accuracy offline.

## 14. Explain observability and alerting
- **Logging:** Structured JSON logs via `structlog`.
- **Tracing:** OpenTelemetry exported to Jaeger/Datadog. Every audit gets a unique `trace_id`.
- **Metrics:** 
  - API Latency (p99).
  - LLM Token Usage (Cost tracking).
  - Audit Success/Failure Rate.
- **Alerts:** PagerDuty for API 5xx > 1% or Audit Failure Rate > 5%.

## 15. Identify risks and mitigations
- *Risk:* Skyrocketing LLM costs due to processing massive transaction lists.
  - *Mitigation:* Heavy deterministic pre-filtering. Group identical recurring transactions in SQL *before* sending to LLM (e.g., send "Netflix, $15.99, 3 occurrences" instead of 3 raw rows).
- *Risk:* Data privacy leakage (sending PII to LLM).
  - *Mitigation:* Redact/hash account numbers, strict zero-data-retention agreements with LLM providers via enterprise APIs.

## 16. Justify tradeoffs and explicitly reject alternatives
- **Rejected:** Rule-based only engine. *Reason:* Merchant strings are too noisy ("SQ* Hulu", "PAYPAL *HULU COM"). Maintaining regexes is a Sisyphean task.
- **Rejected:** Passing raw bank credentials to the system. *Reason:* Massive security liability. System only accepts transaction records.
- **Tradeoff:** Asynchronous auditing instead of synchronous. *Reason:* LLM calls take 10-30 seconds. A synchronous HTTP request would timeout or tie up web workers. We trade UX complexity (polling for results) for system stability.

## User Review Required
Please review the architecture and decisions. Specifically:
1. The **Async Audit Flow** (Client must poll for results instead of waiting on the POST request).
2. The **Agent Pipeline limitation**: The agent will strictly output structured recommendations and will NOT be allowed to directly cancel services.
3. Does this align with your vision before I proceed to the core implementation?
