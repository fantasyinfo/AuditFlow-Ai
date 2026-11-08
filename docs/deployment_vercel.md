# AuditFlow AI — Vercel Production Deployment Guide

This guide explains how to deploy the entire AuditFlow AI platform (React frontend + FastAPI serverless backend with pgvector RAG and Gemini AI) to **Vercel** with zero code changes.

---

## 1. Architecture on Vercel

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel Edge Network                      │
│                                                             │
│   Static Assets (React + Vite + Tailwind)  ──> Edge CDN     │
│   API Requests (/documents, /projects, etc)──> api/index.py │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
  Remote PostgreSQL + pgvector     Google AI Studio (Gemini)
  (Neon / Supabase / Railway)       (Free Tier LLM & Vision)
```

- **Frontend:** Built via `cd frontend && npm install && npm run build` and output to `frontend/dist`.
- **Backend:** Ephemeral Python 3.12 ASGI serverless function served by `api/index.py` using `NullPool` database connections to eliminate connection leaks across cold/warm starts.
- **Background Tasks:** Synchronous in-process execution (`SYNC_PROCESSING=true`) processes uploaded invoices and evaluates audit detection rules within milliseconds during the request.
- **Storage:** Writes to ephemeral `/tmp/uploads` on Vercel functions, avoiding read-only root errors.

---

## 2. Prerequisites

1. A free **Vercel Account** ([vercel.com](https://vercel.com))
2. A free **Serverless PostgreSQL database with pgvector support**:
   - [Neon.tech](https://neon.tech) (Recommended — free serverless Postgres with pgvector)
   - [Supabase.com](https://supabase.com) (Free tier includes pgvector)
   - [Railway.app](https://railway.app)
3. A free **Google AI Studio Gemini API Key** ([aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey))

---

## 3. Environment Variables

Configure these environment variables in your Vercel Project Settings (**Settings** -> **Environment Variables**):

| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@ep-cool-db.us-east-2.aws.neon.tech/neondb?sslmode=require` |
| `SYNC_DATABASE_URL` | Synchronous PostgreSQL connection string | `postgresql+psycopg2://user:pass@ep-cool-db.us-east-2.aws.neon.tech/neondb?sslmode=require` |
| `JWT_SECRET` | 32+ character random string for token signing | e.g. `9f823a9d45e82110c7bf982348a04912` |
| `GEMINI_API_KEY` | Google AI Studio Gemini API key | `AIzaSy...` |
| `SYNC_PROCESSING` | Force in-process document processing | `true` |

> [!NOTE]
> Neon or Supabase provide connection strings starting with `postgres://` or `postgresql://`.
> Make sure to prefix:
> - `DATABASE_URL` with `postgresql+asyncpg://`
> - `SYNC_DATABASE_URL` with `postgresql+psycopg2://`

---

## 4. Deployment Steps

### Method A: Deploy via GitHub (Recommended)

1. Push your repository to GitHub:
   ```bash
   git add .
   git commit -m "Configure Vercel serverless deployment"
   git push origin main
   ```
2. Go to [vercel.com/new](https://vercel.com/new).
3. Select your repository `AuditFlow`.
4. In **Project Settings**:
   - **Framework Preset:** `Vite` (or leave default, `vercel.json` configures everything automatically).
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Output Directory:** `frontend/dist`
5. Expand **Environment Variables** and add the 5 variables from Section 3 above.
6. Click **Deploy**.

### Method B: Deploy via Vercel CLI

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. Run deploy from the repository root:
   ```bash
   vercel
   ```
3. Set your environment variables:
   ```bash
   vercel env add DATABASE_URL
   vercel env add SYNC_DATABASE_URL
   vercel env add JWT_SECRET
   vercel env add GEMINI_API_KEY
   ```
4. Deploy to production:
   ```bash
   vercel --prod
   ```

---

## 5. Automatic Database Initialization

When the application boots for the first time on Vercel, the `lifespan` handler automatically:
1. Executes `CREATE EXTENSION IF NOT EXISTS vector;`
2. Creates all tables (`tenants`, `users`, `projects`, `documents`, `document_chunks`, `invoices`, `findings`, `audit_logs`, `custom_rules`, `idempotency_keys`).
3. Seeds the default primary tenant if absent.

No manual migration commands (`alembic upgrade head`) are required.

---

## 6. Verification Checklist

Once your deployment is live at `https://<your-project>.vercel.app`:
- [ ] Visit `https://<your-project>.vercel.app/` — verify that the clean Executive Dashboard and Projects workspace load.
- [ ] Visit `https://<your-project>.vercel.app/docs` — verify that FastAPI Swagger documentation is accessible.
- [ ] Visit `https://<your-project>.vercel.app/health` — verify `{"status":"healthy","database":"connected"}`.
- [ ] Upload an invoice in the **Documents** tab — verify that commercial record extraction and audit rules evaluate successfully.
- [ ] Ask a question in the **AI Assistant** tab — verify that the strictly read-only LangChain agent answers with exact citations.
