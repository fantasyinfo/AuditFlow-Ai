# AuditFlow AI — Automated AP Audit & Fraud Detection

> Automated Accounts Payable (AP) audit and anomaly detection platform built with Python 3.12, FastAPI, PostgreSQL (`pgvector`), Redis Celery workers, Google AI Studio (Gemini 2.0), and a Vite + React + Tailwind CSS Admin Center.

---

## ⚡ 5-Minute Quickstart

### 1. Start the Stack with Docker Compose
```bash
docker compose up -d
```
This launches:
- `db`: PostgreSQL 16 with `pgvector` extension
- `redis`: Redis 7.4 task queue & rate limiter
- `migrate`: Runs Alembic migrations automatically on boot
- `api`: FastAPI application serving on `http://localhost:8000`
- `worker`: Synchronous Celery workers processing background ingestion

### 2. Access the Admin Panel
Open your browser to:
- **Interactive Vite React Admin Panel:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Production Admin Panel:** [http://localhost:8000/app](http://localhost:8000/app)
- **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Metrics:** [http://localhost:8000/metrics](http://localhost:8000/metrics)

You can click **"Instant Test Tenant (1-Click Generator)"** on the login screen to immediately enter an isolated environment.

### 3. Seed Realistic Demo Data (50 Invoices & Anomalies)
```bash
docker compose exec api python scripts/seed_demo_data.py
```

### 4. Run High-Throughput Load Benchmark
```bash
docker compose exec api python scripts/benchmark_throughput.py
```

---

## 📊 Measured Ingestion Performance

Under concurrent load testing (100 documents, concurrency 10):
- **API Accept Rate:** **49.31 uploads / second**
- **P50 Latency:** **168.30 ms**
- **P95 Latency:** **416.41 ms**
- **Queue Absorption:** 100% accepted with HTTP `202 Accepted` and zero dropped requests.

---

## 🛡️ Core Invariants

1. **Multi-Tenancy Isolation:** Every database table and vector chunk is scoped by `tenant_id`.
2. **Financial Precision:** All money values are strictly Python `Decimal` and PostgreSQL `NUMERIC(18, 2)`. Zero floating-point math.
3. **Strictly Read-Only AI Agent:** Powered by Google AI Studio (Gemini 2.0 Flash) and LangChain. Tools only query data and return mandatory citations (`[filename.pdf p.X]`, `[finding #ID]`). Refuses out-of-context requests.
4. **Tenant Custom Rules:** Users can create condition-based rules (amount thresholds, vendor checks, missing fields, weekend billing) evaluated dynamically on every document.

---

## 🧪 Running Tests
```bash
# Run all 22 unit, integration, and golden evaluation tests:
docker compose exec api python -m unittest discover tests -v
```
