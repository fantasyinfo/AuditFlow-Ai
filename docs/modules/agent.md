# Module Specification: AI Audit Assistant & RAG (agent.md)

## 1. Purpose
The AI Audit Assistant enables finance teams, audit controllers, and compliance officers to perform natural-language inquiries across all uploaded commercial documents (invoices, purchase orders, quotations, estimates, and service agreements/contracts in arbitrary global formats). Powered by Google AI Studio (Gemini) with dense vector retrieval via PostgreSQL (`pgvector`), the assistant answers user inquiries with **mandatory verifiable citations** (`[filename.pdf p.X]`, `[finding #ID]`) and strictly adheres to read-only operation and hallucination refusal guardrails.

## 2. Files
- `app/agent/llm.py`: Chat model initialization targeting Google AI Studio's Gemini models (`gemini-2.0-flash`, `gemini-1.5-flash`) via the OpenAI-compatible endpoint with automatic fallback.
- `app/agent/tools.py`: Strictly read-only LangChain tools bound securely to authenticated `tenant_id`:
  - `search_documents`: Executes tenant-scoped pgvector similarity search across document chunks.
  - `list_findings`: Queries deterministic audit detection findings and reasons.
  - `get_invoice`: Looks up structured invoice, vendor, amount, GSTIN, and linked PO details.
- `app/agent/prompts.py`: System prompt enforcing auditor persona, mandatory citations, and the exact refusal phrase: *"I could not find this in your documents."*
- `app/agent/agent_runner.py`: Orchestrates agent execution with tool calling, timeout handling (25s), mutation guardrails, deterministic fallback, and citation parsing.
- `app/rag/retriever.py`: Tenant-isolated vector similarity retriever querying `document_chunks` using pgvector's cosine distance operator (`<=>`).
- `app/routes/agent.py`: FastAPI endpoint `POST /agent/ask`.
- `tests/eval/golden_questions.json`: Golden benchmark dataset of 10 evaluation questions covering duplicates, vendor queries, missing evidence, tax compliance, refusal guardrails, and read-only safety.
- `tests/test_agent.py`: Automated test suite covering multi-tenant isolation, golden questions eval, mutation rejection, and API response format.

## 3. Inputs and Outputs

### API Request (`POST /agent/ask`)
```json
{
  "query": "Are there any duplicate invoices detected?"
}
```

### API Response (`AgentAskResponse`)
```json
{
  "query": "Are there any duplicate invoices detected?",
  "answer": "Invoice INV-1042 from Sharma Traders (₹1,18,000.00) looks like a potential duplicate. Reason: Duplicate invoice number INV-1042 detected for Sharma Traders. Sources: [finding #82da695c-7ec6-46c5-9276-2f74112e4fbc], [invoice_1042.pdf p.1].",
  "citations": [
    "[finding #82da695c-7ec6-46c5-9276-2f74112e4fbc]",
    "[invoice_1042.pdf p.1]"
  ],
  "answered_from_sources": true
}
```

## 4. Failure Cases & Guardrails
- **Information Absent / Out-of-Domain:** When a question references an entity or topic not found in the tenant's data, the assistant responds with the exact phrase:
  `"I could not find this in your documents."` and sets `answered_from_sources=false` with `citations=[]`.
- **Data Mutation Attempts:** If a user instructs the assistant to delete, update, or dismiss invoices or findings, the assistant immediately blocks the request and replies:
  `"I am a strictly read-only audit assistant. I cannot insert, update, dismiss, or delete documents, invoices, or audit findings."`
- **Multi-Tenant Separation:** All tools bind `tenant_id` at invocation time directly from verified JWT claims. A user in Tenant B querying about Tenant A's documents receives the exact refusal phrase.
- **LLM Outage / Mock Test Mode:** If an external LLM API key is not configured or fails, the deterministic assistant engine resolves queries based on domain database state and vector chunks without crashing.

## 5. How to Test It
Run the automated test suite including the 10 Golden Questions:
```bash
docker compose exec api python -m unittest tests/test_agent.py -v
```

Execute an authenticated query via cURL:
```bash
curl -s -X POST http://localhost:8000/agent/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What findings are flagged for Sharma Traders?"}'
```

Interactive Web Dashboard:
Visit `http://localhost:8000/ui` in your browser, authenticate, and use the **AI Audit Assistant** chat card to test prompt questions and verify citations interactively.

## 6. Known Limits
- Dense semantic vector search retrieves the top-5 chunks; hybrid search combining full-text PostgreSQL lexical search with pgvector embeddings is planned for Phase 2.
- Complex tabular financial analysis spanning dozens of multi-page agreements is currently summarized within token limits; full cross-document ledger reconciliation will be introduced in Phase 2.
