# AuditFlow AI: MVP Project Plan

Python, FastAPI, PostgreSQL (pgvector), Redis queue, LangChain agent with RAG.

**Goal of this document:** build a small MVP in 7 days, prove the full pipeline works end to end, and only then polish. Everything is kept simple: plain function names, few comments, pinned library versions.

---

## 1. What the app does

AuditFlow AI helps a finance team or audit firm find problems in their payables before money is lost.

1. A user uploads invoices (PDF or CSV) and optionally purchase orders and contracts.
2. The API saves the file and returns immediately. A background worker parses it, extracts fields, and stores chunks plus embeddings.
3. A rules engine runs on every new invoice and creates **findings**.
4. A user asks questions in plain language. A LangChain agent uses tools (search documents, list findings, look up invoices) and answers **with citations**.
5. Every action is written to an append-only audit log.

### Detection rules in the MVP

| Rule | What it catches |
| --- | --- |
| Duplicate invoice | Same vendor, same invoice number, or same vendor + amount + date |
| Amount mismatch | Invoice total differs from the linked PO total |
| Missing evidence | Invoice has no PO or no supporting document |
| Invalid GSTIN | GSTIN fails the format check (India) |
| Unusual amount | Amount is far above the vendor's average |

### What the output looks like

- **Findings list** (JSON via API): type, severity, invoice, reason, evidence references, status (open, confirmed, dismissed).
- **Agent answer** (JSON): answer text, list of citations (document, page, chunk), and a flag `answered_from_sources`.
- **Audit report** (JSON now, PDF later): summary counts, total amount at risk, top vendors by findings.
- **Audit log**: who did what, when, with before and after values.

Example agent answer:

> "Invoice INV-1042 from Sharma Traders (₹1,18,000) looks like a duplicate of INV-1042-A paid on 12 Aug. Sources: \[invoice\_1042.pdf p1\], \[finding #31\]."

The agent **never changes data**. It reads, explains and suggests. A human confirms or dismisses findings.

---

## 2. How "millions of requests" is handled

Being honest about this: the MVP is designed so it can scale, and you prove it with a load test. You do not need production traffic to claim the design.

| Concern | Approach |
| --- | --- |
| API stays fast | The API only validates, writes a row, enqueues a job, returns `202`. Heavy work is never in the request. |
| Burst traffic | Redis queue absorbs spikes. Workers drain it at their own speed. |
| Scale out | API is stateless. Run N API containers and M worker containers. |
| Slow LLM calls | Run in workers or in a bounded async call with timeout and retry. |
| Duplicate uploads | `Idempotency-Key` header on write endpoints. |
| Database | Indexes on `(tenant_id, created_at)`, connection pooling, later read replicas and partitioning. |
| Abuse | Per-tenant rate limit in Redis. |

The thing to measure in Day 6 is **API accept rate** (uploads accepted per second, p95 latency) and **queue drain rate** (documents processed per minute per worker). Put those two numbers in your README.

---

## 3. Architecture

```
Client
  |
  v
FastAPI (stateless, N copies)
  |-- writes rows -----------> PostgreSQL (+ pgvector)
  |-- enqueues job ----------> Redis (queue)
  |                                |
  |                                v
  |                         Celery workers
  |                          - parse file
  |                          - extract invoice fields
  |                          - chunk + embed
  |                          - run rules
  |                                |
  |                                v
  |                          PostgreSQL (findings, chunks)
  |
  '-- /agent/ask --> LangChain agent --> tools --> PostgreSQL / vector search
                                   |
                                   '--> LLM API (OpenAI-compatible)
```

**Multi-tenancy:** one shared schema, `tenant_id` on every table, every query filtered by it. Row-Level Security is added in the polish phase.

**Money:** stored as `NUMERIC(18,2)`, never float.

---

## 4. Cheap AI API options

LangChain's `ChatOpenAI` and `OpenAIEmbeddings` work with any OpenAI-compatible endpoint, so you only change three env variables (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`) to switch provider. Prices change often, so always check the pricing page before choosing.

| Provider | Good for | Link |
| --- | --- | --- |
| Google AI Studio (Gemini) | Free tier for testing, chat and embeddings | https://aistudio.google.com |
| Groq | Very fast open models, free tier | https://console.groq.com |
| DeepSeek | Very low cost chat model | https://platform.deepseek.com |
| OpenRouter | One key for many models, easy to switch | https://openrouter.ai |
| OpenAI | Small models and `text-embedding-3-small` embeddings | https://platform.openai.com |
| Mistral | Cheap small models, embeddings | https://console.mistral.ai |
| Jina AI | Embeddings with a free quota | https://jina.ai |
| Together AI | Open models, pay as you go | https://www.together.ai |

**Suggested MVP setup:** a cheap chat model from Groq or DeepSeek or Gemini for the agent, and `text-embedding-3-small` (1536 dimensions) or a Gemini/Jina embedding for vectors. Keep the embedding model fixed once you have stored vectors. Changing it means re-embedding everything, and `EMBEDDING_DIM` must match the vector column.

**Cost controls:** set `max_tokens`, cache answers per question, limit retrieved chunks to 5, and use the cheap model for everything in the MVP.

**Data caution:** invoices contain personal and financial data. Redact names, PAN and bank numbers before sending text to an external LLM, or use a provider whose data terms you have read.

---

## 5. Folder structure

```
auditflow-ai/
├── README.md
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── .env.example
├── .gitignore
├── requirements.txt          # pinned runtime libraries
├── requirements-dev.txt      # pinned test and lint libraries
├── alembic.ini
├── migrations/
│   └── versions/
├── app/
│   ├── main.py               # creates the FastAPI app
│   ├── config.py             # reads env settings
│   ├── database.py           # engine and session
│   ├── security.py           # password hash, JWT
│   ├── dependencies.py       # current user, tenant, db session
│   ├── models/               # SQLAlchemy tables
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── chunk.py
│   │   ├── invoice.py
│   │   ├── purchase_order.py
│   │   ├── finding.py
│   │   └── audit_log.py
│   ├── schemas/              # Pydantic request and response models
│   ├── routes/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── invoices.py
│   │   ├── findings.py
│   │   ├── agent.py
│   │   └── health.py
│   ├── services/             # business logic, called by routes and workers
│   │   ├── auth_service.py
│   │   ├── document_service.py
│   │   ├── invoice_service.py
│   │   ├── finding_service.py
│   │   └── audit_service.py
│   ├── rules/                # one file per detection rule
│   │   ├── duplicate_invoice.py
│   │   ├── amount_mismatch.py
│   │   ├── missing_evidence.py
│   │   ├── gstin_check.py
│   │   ├── unusual_amount.py
│   │   └── run_rules.py
│   ├── rag/
│   │   ├── parser.py         # PDF and CSV to text
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   └── retriever.py      # tenant-filtered vector search
│   ├── agent/
│   │   ├── llm.py            # builds the chat model
│   │   ├── tools.py          # tools the agent can call
│   │   ├── prompts.py
│   │   └── agent_runner.py
│   └── worker/
│       ├── celery_app.py
│       └── tasks.py
├── tests/
│   ├── test_rules.py
│   ├── test_documents.py
│   ├── test_agent.py
│   └── eval/
│       └── golden_questions.json
├── scripts/
│   ├── seed_demo_data.py
│   └── load_test.py          # Locust file
└── docs/
    ├── architecture.md
    ├── api.md
    ├── modules/
    │   ├── auth.md
    │   ├── documents.md
    │   ├── rules.md
    │   ├── rag.md
    │   ├── agent.md
    │   ├── worker.md
    │   └── audit_log.md
    └── decisions/            # short ADRs
```

---

## 6. Locked library versions

`requirements.txt` (exact versions, no ranges):

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.1
sqlalchemy==2.0.36
asyncpg==0.30.0
psycopg2-binary==2.9.10
alembic==1.14.0
pgvector==0.3.6
celery==5.4.0
redis==5.2.1
langchain==0.3.13
langchain-core==0.3.28
langchain-openai==0.2.14
langchain-text-splitters==0.3.4
pypdf==5.1.0
python-multipart==0.0.20
PyJWT==2.10.1
bcrypt==4.2.1
httpx==0.28.1
structlog==24.4.0
prometheus-fastapi-instrumentator==7.0.0
```

`requirements-dev.txt`:

```
-r requirements.txt
pytest==8.3.4
pytest-asyncio==0.25.0
ruff==0.8.4
locust==2.32.5
```

**Rules to keep versions locked:**

- Never write `pip install <name>` without a version. Add the exact version to the file.
- The Dockerfile installs only from `requirements.txt`.
- After your first clean install, run `pip freeze > requirements.lock` and commit it. This also pins sub-dependencies. Build the Docker image from the lock file if you want a fully reproducible build.
- Upgrade only on purpose, in its own commit, with tests passing. Use Dependabot or Renovate later, set to open pull requests, never auto-merge.

**Important:** these versions were chosen as a mutually compatible set from my knowledge and I could not run an install here. On Day 1, build the image once. If pip reports a conflict, fix that one line, then freeze the lock file. This is the one place to check before trusting the list.

---

## 7. Docker setup

`docker-compose.yml`:

```yaml
services:
  db:
    image: pgvector/pgvector:0.8.0-pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7.4.1-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

  migrate:
    build: .
    command: alembic upgrade head
    env_file: .env
    depends_on:
      db:
        condition: service_healthy

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - uploads:/data/uploads
    depends_on:
      migrate:
        condition: service_completed_successfully
      redis:
        condition: service_healthy

  worker:
    build: .
    command: celery -A app.worker.celery_app worker --loglevel=info --concurrency=4
    env_file: .env
    volumes:
      - uploads:/data/uploads
    depends_on:
      migrate:
        condition: service_completed_successfully
      redis:
        condition: service_healthy

volumes:
  pgdata:
  uploads:
```

Scale later with `docker compose up --scale worker=4 --scale api=3` (put a load balancer such as nginx in front of multiple API containers; remove the fixed `8000:8000` port mapping when you do).

`Dockerfile`:

```dockerfile
FROM python:3.12.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser \
    && mkdir -p /data/uploads \
    && chown -R appuser /data /code
USER appuser
```

`.env.example`:

```
POSTGRES_USER=auditflow
POSTGRES_PASSWORD=change_me
POSTGRES_DB=auditflow
DATABASE_URL=postgresql+asyncpg://auditflow:change_me@db:5432/auditflow
SYNC_DATABASE_URL=postgresql+psycopg2://auditflow:change_me@db:5432/auditflow
REDIS_URL=redis://redis:6379/0

JWT_SECRET=change_me_to_a_long_random_string
JWT_EXPIRE_MINUTES=60

LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your_key_here
LLM_MODEL=your_chat_model_name

EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=your_key_here
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536

UPLOAD_DIR=/data/uploads
MAX_UPLOAD_MB=10
RATE_LIMIT_PER_MINUTE=120
```

The `migrate` service runs Alembic once before the API and worker start, so you never forget a migration. `.env` is in `.gitignore`; only `.env.example` is committed.

---

## 8. Core data tables (MVP)

| Table | Key columns |
| --- | --- |
| tenants | id, name, created\_at |
| users | id, tenant\_id, email, password\_hash, role |
| documents | id, tenant\_id, filename, type, status (queued, processing, done, failed), storage\_path, created\_by |
| document\_chunks | id, tenant\_id, document\_id, page, text, embedding (vector) |
| invoices | id, tenant\_id, document\_id, vendor\_name, vendor\_gstin, invoice\_number, invoice\_date, total\_amount, po\_id |
| purchase\_orders | id, tenant\_id, po\_number, vendor\_name, total\_amount |
| findings | id, tenant\_id, invoice\_id, rule, severity, reason, status, created\_at |
| audit\_log | id, tenant\_id, user\_id, action, entity, entity\_id, before, after, created\_at |
| idempotency\_keys | tenant\_id, key, response\_hash, created\_at |

Indexes on `(tenant_id, created_at)` for every table, a unique index on `(tenant_id, vendor_name, invoice_number)` for fast duplicate checks, and an HNSW index on `document_chunks.embedding`.

---

## 9. API (MVP)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | /auth/register | Create tenant and first admin |
| POST | /auth/login | Get JWT |
| POST | /documents | Upload file, returns 202 and document id |
| GET | /documents/{id} | Check processing status |
| GET | /invoices | List invoices |
| GET | /findings | List findings, filter by status or rule |
| PATCH | /findings/{id} | Confirm or dismiss, writes audit log |
| POST | /agent/ask | Ask a question, get answer with citations |
| GET | /health | Liveness and readiness |

---

## 10. Day-wise plan

### Phase 1: MVP (Days 1 to 7). Goal: it works end to end.

**Day 1: Skeleton, database, auth**

- Create repo and the folder structure above.
- Add `requirements.txt`, Dockerfile, docker-compose, `.env.example`.
- Build image once, fix any version conflict, create `requirements.lock`.
- `config.py`, `database.py`, `/health`.
- Models for tenants and users, first Alembic migration.
- `/auth/register`, `/auth/login`, JWT, `get_current_user` dependency.
- *Done when:* `docker compose up` starts everything and you can register and log in.

**Day 2: Documents and queue**

- Models: documents, invoices, purchase\_orders.
- `POST /documents`: validate type and size, save file, insert row, enqueue Celery task, return 202.
- `Idempotency-Key` handling.
- `GET /documents/{id}` status.
- Worker task that only flips status to `done` (proves the queue works).
- *Done when:* upload returns instantly and the worker log shows the job processed.

**Day 3: Parsing and embeddings**

- `rag/parser.py`: PDF text with pypdf, CSV rows.
- `rag/chunker.py` using the LangChain text splitter.
- `rag/embedder.py`: batch embeddings through the configured API, with retry and timeout.
- Store chunks and vectors with `tenant_id`.
- Extract invoice fields (vendor, number, date, total, GSTIN) from CSV directly and from PDF text with a simple regex first. LLM extraction is a later upgrade.
- *Done when:* uploading a sample invoice creates an invoice row and chunk rows.

**Day 4: Rules engine**

- One file per rule, each a plain function: `check_duplicate(invoice, db)` returning a finding or nothing.
- `run_rules.py` runs all rules, called by the worker after parsing.
- `GET /findings`, `PATCH /findings/{id}` and audit log entries.
- Unit tests for every rule using small fixed examples.
- *Done when:* a seeded duplicate invoice produces a finding.

**Day 5: Agent and RAG**

- `rag/retriever.py`: vector search filtered by `tenant_id`, top 5 chunks.
- `agent/tools.py`: `search_documents`, `list_findings`, `get_invoice`.
- `agent/agent_runner.py`: LangChain agent using tool calling, system prompt that requires citations and says "I could not find this in your documents" when sources are empty.
- `POST /agent/ask` with timeout and `max_tokens`.
- `tests/eval/golden_questions.json` with 10 questions and expected sources.
- *Done when:* the agent answers a duplicate question and cites the right finding.

**Day 6: Hardening and load test**

- Per-tenant rate limit in Redis.
- Structured JSON logs with request id and tenant id.
- Prometheus metrics endpoint.
- Locust script for `POST /documents` and `GET /findings`.
- Record accept rate, p95 latency, and worker drain rate. Tune pool size and worker concurrency.

**Day 7: Docs and demo**

- `scripts/seed_demo_data.py` with about 50 invoices including planted problems.
- Write `docs/architecture.md`, `docs/api.md`, and the module docs.
- README with a 5-minute quick start and the benchmark numbers.
- Record a short demo run: upload, findings appear, ask the agent.

**MVP acceptance checklist**

- [ ] `docker compose up` works from a clean clone
- [ ] Register, login, upload, process, findings, ask agent, all work
- [ ] Two tenants cannot see each other's data (test it)
- [ ] Rule unit tests pass
- [ ] Golden question set runs and you know the score
- [ ] Load test numbers recorded

### Phase 2: Make it solid (week 2)

- PostgreSQL Row-Level Security.
- Hash-chained audit log for tamper evidence.
- Retry with backoff and a dead-letter queue for failed jobs.
- Hybrid search (Postgres full-text plus vector) and reranking.
- Prompt-injection checks on uploaded text and PII redaction before LLM calls.
- Role-based access (admin, accountant, auditor, read-only).
- GitHub Actions: ruff, tests, Docker build, image scan.
- Run the eval set in CI and fail the build if the score drops.

### Phase 3: Make it a product (weeks 3 to 4)

- Double-entry ledger with immutable journal entries and reversals.
- Three-way match (PO, invoice, payment) and bank statement import.
- GST/TDS reference corpus as a RAG module (cite section and date).
- PDF audit reports.
- Usage metering table and per-tenant quotas (needed to sell as SaaS).
- Config-driven branding and custom domain support.
- OpenTelemetry tracing, Grafana dashboards.
- Table partitioning for audit and chunks, read replica, object storage (S3 or MinIO) instead of a local volume.
- Cloud deploy with Terraform or Helm.

---

## 11. Module documentation

Each file in `docs/modules/` uses the same short format so they stay useful:

1. **Purpose:** one paragraph.
2. **Files:** list of files and what each does.
3. **Inputs and outputs:** what goes in, what comes out.
4. **Failure cases:** what can go wrong and what the code does.
5. **How to test it:** the exact command.
6. **Known limits.**

Contents to cover:

| File | Must explain |
| --- | --- |
| auth.md | Tenant creation, password hashing, JWT claims, roles |
| documents.md | Upload flow, statuses, idempotency, file limits |
| rules.md | Each rule, its logic, thresholds, how to add a new rule |
| rag.md | Parse, chunk, embed, retrieve; chunk size; embedding model and dimension; tenant filter |
| agent.md | Tools, prompt, citation format, refusal behaviour, cost limits |
| worker.md | Task list, retries, concurrency, how to scale |
| audit\_log.md | What is logged, format, retention |

Write each doc on the same day you write the module, not at the end.

---

## 12. Coding conventions

- Plain names: `save_upload`, `parse_pdf`, `check_duplicate`, `ask_agent`.
- Routes only call services. Services hold logic. Models hold tables. No logic in routes.
- One rule per file, one job per function.
- Comments only where the reason is not obvious. Names should explain the rest.
- Type hints on every function.
- Every query includes `tenant_id`.
- Money is `Decimal`, never `float`.
- Never log API keys, tokens, or full invoice text.

---

## 13. Risks and honest limits

- Compatibility of the pinned versions needs one real install on Day 1 (see section 6).
- Regex extraction from PDFs is rough. CSV and clean PDFs work first; scanned invoices need OCR in a later phase.
- LLM output can be wrong. The citation requirement and human confirmation exist for that reason.
- Tax and legal answers are decision support, not advice. Show a disclaimer in the API response.
- Scale claims need a load test on your own hardware. Quote only numbers you measured.

