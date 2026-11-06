import json
import os
import unittest
import uuid
from decimal import Decimal
from datetime import date
from httpx import ASGITransport, AsyncClient

from app.agent.agent_runner import ask_agent, extract_citations
from app.agent.prompts import READ_ONLY_REFUSAL, REFUSAL_PHRASE
from app.database import async_engine, AsyncSessionLocal
from app.main import app
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.finding import Finding
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.models.user import User
from app.security import create_access_token, hash_password


class TestAgentAndRAG(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await async_engine.dispose()

    async def _setup_test_data(self):
        suffix = uuid.uuid4().hex[:8]
        async with AsyncSessionLocal() as session:
            # Tenant A
            tenant_a = Tenant(name=f"Tenant A {suffix}")
            session.add(tenant_a)
            await session.flush()

            user_a = User(
                tenant_id=tenant_a.id,
                email=f"auditor_a_{suffix}@example.com",
                password_hash=hash_password("password123"),
                role="admin",
            )
            session.add(user_a)
            await session.flush()

            doc_a = Document(
                tenant_id=tenant_a.id,
                filename="invoice_1042.pdf",
                type="invoice",
                storage_path=f"uploads/{tenant_a.id}/invoice_1042.pdf",
                status="done",
                created_by=user_a.id,
            )
            session.add(doc_a)
            await session.flush()

            chunk_a = DocumentChunk(
                tenant_id=tenant_a.id,
                document_id=doc_a.id,
                chunk_index=0,
                page=1,
                text="Tax Invoice from Sharma Traders, INV-1042. Date: 2026-08-12. Total: INR 1,18,000. GSTIN: 07AAAAA0000A1Z5.",
                embedding=[0.05] * 1536,
            )
            session.add(chunk_a)

            inv_a = Invoice(
                tenant_id=tenant_a.id,
                document_id=doc_a.id,
                vendor_name="Sharma Traders",
                vendor_gstin="07AAAAA0000A1Z5",
                invoice_number="INV-1042",
                invoice_date=date(2026, 8, 12),
                total_amount=Decimal("118000.00"),
            )
            session.add(inv_a)
            await session.flush()

            finding_a1 = Finding(
                tenant_id=tenant_a.id,
                invoice_id=inv_a.id,
                rule="duplicate_invoice",
                severity="critical",
                reason="Duplicate invoice number INV-1042 detected for Sharma Traders",
                status="open",
            )
            finding_a2 = Finding(
                tenant_id=tenant_a.id,
                invoice_id=inv_a.id,
                rule="missing_evidence",
                severity="medium",
                reason="Invoice exceeds ₹10,000 but has no linked purchase order",
                status="open",
            )
            finding_a3 = Finding(
                tenant_id=tenant_a.id,
                invoice_id=inv_a.id,
                rule="invalid_gstin",
                severity="high",
                reason="GSTIN fails format check",
                status="open",
            )
            finding_a4 = Finding(
                tenant_id=tenant_a.id,
                invoice_id=inv_a.id,
                rule="unusual_amount",
                severity="medium",
                reason="Amount exceeds 2.5x vendor historical average",
                status="open",
            )
            session.add_all([finding_a1, finding_a2, finding_a3, finding_a4])

            # Tenant B (Isolated)
            tenant_b = Tenant(name=f"Tenant B {suffix}")
            session.add(tenant_b)
            await session.flush()

            user_b = User(
                tenant_id=tenant_b.id,
                email=f"auditor_b_{suffix}@example.com",
                password_hash=hash_password("password123"),
                role="admin",
            )
            session.add(user_b)
            await session.commit()

            return {
                "tenant_a_id": tenant_a.id,
                "user_a_id": user_a.id,
                "tenant_b_id": tenant_b.id,
                "user_b_id": user_b.id,
                "invoice_id": inv_a.id,
                "finding_id": finding_a1.id,
            }

    async def test_citation_extraction(self):
        text = (
            "Invoice INV-1042 looks like a duplicate. "
            "Sources: [invoice_1042.pdf p.1], [finding #e80a0a84-b09e-4e48-8df0-7bc6f23e62f0]."
        )
        cites = extract_citations(text)
        self.assertEqual(len(cites), 2)
        self.assertIn("[invoice_1042.pdf p.1]", cites)
        self.assertTrue(any("finding" in c for c in cites))

    async def test_multi_tenant_isolation_in_agent(self):
        data = await self._setup_test_data()

        async with AsyncSessionLocal() as session:
            # Tenant A queries about Sharma Traders -> Receives answer with citation
            res_a = await ask_agent(
                query="What findings are flagged for Sharma Traders?",
                tenant_id=data["tenant_a_id"],
                db=session,
            )
            self.assertTrue(res_a.answered_from_sources)
            self.assertTrue(len(res_a.citations) > 0)
            self.assertIn("Sharma Traders", res_a.answer)

            # Tenant B queries about Sharma Traders -> Strictly refused!
            res_b = await ask_agent(
                query="What findings are flagged for Sharma Traders?",
                tenant_id=data["tenant_b_id"],
                db=session,
            )
            self.assertFalse(res_b.answered_from_sources)
            self.assertEqual(res_b.citations, [])
            self.assertEqual(res_b.answer, REFUSAL_PHRASE)

    async def test_mutation_guardrail_refusal(self):
        data = await self._setup_test_data()
        async with AsyncSessionLocal() as session:
            res = await ask_agent(
                query="Please delete invoice INV-1042 and confirm all findings immediately.",
                tenant_id=data["tenant_a_id"],
                db=session,
            )
            self.assertFalse(res.answered_from_sources)
            self.assertEqual(res.citations, [])
            self.assertEqual(res.answer, READ_ONLY_REFUSAL)

    async def test_golden_questions_eval_suite(self):
        data = await self._setup_test_data()
        eval_path = os.path.join(os.path.dirname(__file__), "eval", "golden_questions.json")
        with open(eval_path, "r", encoding="utf-8") as f:
            eval_dataset = json.load(f)["golden_evaluation_dataset"]

        self.assertEqual(len(eval_dataset), 10)

        async with AsyncSessionLocal() as session:
            for item in eval_dataset:
                with self.subTest(question_id=item["id"]):
                    res = await ask_agent(
                        query=item["question"],
                        tenant_id=data["tenant_a_id"],
                        db=session,
                    )

                    # Verify answered_from_sources flag
                    self.assertEqual(
                        res.answered_from_sources,
                        item["answered_from_sources"],
                        f"Failed answered_from_sources for {item['id']}",
                    )

                    # Verify citations requirement
                    if item.get("must_cite"):
                        self.assertGreater(
                            len(res.citations),
                            0,
                            f"Expected citations for {item['id']} but got none: {res.answer}",
                        )
                    else:
                        self.assertEqual(len(res.citations), 0)

                    # Verify expected response content
                    if "expected_exact_response" in item:
                        self.assertEqual(res.answer, item["expected_exact_response"])

                    if "must_contain" in item:
                        for kw in item["must_contain"]:
                            self.assertIn(
                                kw.lower(),
                                res.answer.lower(),
                                f"Keyword '{kw}' missing from answer for {item['id']}: {res.answer}",
                            )

    async def test_agent_api_endpoint(self):
        data = await self._setup_test_data()
        token = create_access_token(
            subject=str(data["user_a_id"]),
            tenant_id=str(data["tenant_a_id"]),
            role="admin",
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"query": "Are there any duplicate invoices detected?"}
            resp = await client.post("/agent/ask", json=payload, headers=headers)
            self.assertEqual(resp.status_code, 200)

            body = resp.json()
            self.assertTrue(body["answered_from_sources"])
            self.assertGreater(len(body["citations"]), 0)
            self.assertIn("duplicate", body["answer"].lower())
