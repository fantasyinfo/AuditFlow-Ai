# AuditFlow AI — Antigravity Agent Guidelines & Rules

Please refer to the comprehensive guidelines and core invariants defined in [AGENTS.md](file:///Users/gauravsharma/Documents/AuditFlow/AGENTS.md).

All agents operating in this repository must strictly adhere to:
1. **Multi-Tenancy Isolation:** Every table and query is scoped strictly by `tenant_id`.
2. **Financial Precision:** All monetary amounts MUST use Python `Decimal` and PostgreSQL `NUMERIC(18, 2)`. Never `float`.
3. **Session Separation:** Async SQLAlchemy (`asyncpg`) for FastAPI; Sync SQLAlchemy (`psycopg2`) for Celery workers.
4. **Strictly Read-Only AI Agent:** The LangChain agent and tools can only inspect and explain with citations; never mutate state.
5. **Clean Architecture:** Strict separation between Routes -> Services -> Rules/Workers -> Models.
6. **Security & Privacy:** Direct `bcrypt`, no secrets in logs, redact sensitive financial PII before sending to external LLMs.
7. **Pinned Dependencies & Tests:** Exact versions only; unit tests for every audit rule and tenant isolation test for every endpoint.

