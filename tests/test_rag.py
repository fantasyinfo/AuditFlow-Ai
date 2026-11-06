import io
import unittest
import uuid
from decimal import Decimal
from httpx import ASGITransport, AsyncClient

from app.database import async_engine
from app.main import app
from app.rag.chunker import chunk_document
from app.rag.embedder import embed_query, embed_texts
from app.rag.parser import ParsedDocument, parse_csv, parse_document


class TestRagPipeline(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await async_engine.dispose()

    def test_csv_parser_and_invoice_extraction(self):
        csv_data = (
            b"vendor,invoice_number,date,amount,gstin\n"
            b"Apex Global,INV-8821,2026-10-15,45200.50,29ABCDE1234F2Z5\n"
        )
        parsed = parse_csv(csv_data)

        self.assertIsNotNone(parsed.extracted_invoice)
        inv = parsed.extracted_invoice
        self.assertEqual(inv.vendor_name, "Apex Global")
        self.assertEqual(inv.invoice_number, "INV-8821")
        self.assertEqual(inv.total_amount, Decimal("45200.50"))
        self.assertEqual(inv.vendor_gstin, "29ABCDE1234F2Z5")
        self.assertEqual(str(inv.invoice_date), "2026-10-15")

    def test_chunker_splits_and_preserves_pages(self):
        long_text = "AuditFlow AP invoice paragraph with audit findings. " * 30
        parsed = ParsedDocument(
            full_text=long_text,
            pages=[(1, long_text[:500]), (2, long_text[500:])],
        )
        chunks = chunk_document(parsed)
        self.assertGreater(len(chunks), 1)

        pages = {c.page for c in chunks}
        self.assertTrue(1 in pages)
        self.assertTrue(2 in pages)
        for idx, c in enumerate(chunks):
            self.assertEqual(c.chunk_index, idx)
            self.assertTrue(len(c.text) > 0)

    def test_embedder_generates_1536_dim_normalized_vectors(self):
        texts = ["Invoice INV-100 from Vendor A", "Duplicate payment on 12 Aug"]
        vectors = embed_texts(texts)

        self.assertEqual(len(vectors), 2)
        self.assertEqual(len(vectors[0]), 1536)
        self.assertEqual(len(vectors[1]), 1536)

        # Check normalization sum(v^2) ~= 1.0
        norm_sq = sum(x * x for x in vectors[0])
        self.assertAlmostEqual(norm_sq, 1.0, places=3)

        query_vec = embed_query("Find duplicate invoices")
        self.assertEqual(len(query_vec), 1536)

    async def test_end_to_end_invoice_and_chunks_api(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            uid = uuid.uuid4().hex[:8]

            # 1. Register Tenant A
            res_reg = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Audit Tenant {uid}",
                    "email": f"auditor_{uid}@auditflow.com",
                    "password": "Password123!",
                },
            )
            self.assertEqual(res_reg.status_code, 201)
            token = res_reg.json()["access_token"]

            # 2. Upload Invoice CSV
            csv_content = (
                b"vendor,invoice_number,date,amount,gstin\n"
                b"Karan Logistics,INV-5501,2026-09-01,98500.00,06AAAAA0000A1Z5\n"
            )
            res_up = await client.post(
                "/documents",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (f"inv_{uid}.csv", io.BytesIO(csv_content), "text/csv")},
                data={"doc_type": "invoice"},
            )
            self.assertEqual(res_up.status_code, 202)
            doc_id = res_up.json()["id"]

            # 3. Trigger worker task synchronously to guarantee pipeline execution in test
            from app.worker.tasks import process_document
            tenant_id = res_reg.json()["tenant_id"]
            task_res = process_document(doc_id, tenant_id)
            self.assertEqual(task_res["status"], "done")

            # 4. Verify Document status is 'done'
            res_doc = await client.get(
                f"/documents/{doc_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(res_doc.status_code, 200)
            self.assertEqual(res_doc.json()["status"], "done")

            # 5. Verify Document Chunks API
            res_chunks = await client.get(
                f"/documents/{doc_id}/chunks",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(res_chunks.status_code, 200)
            chunks = res_chunks.json()
            self.assertGreaterEqual(len(chunks), 1)
            self.assertIn("Karan Logistics", chunks[0]["text"])

            # 6. Verify Invoices API
            res_invoices = await client.get(
                "/invoices",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(res_invoices.status_code, 200)
            invoices = res_invoices.json()
            self.assertTrue(any(i["invoice_number"] == "INV-5501" for i in invoices))
            matched_inv = next(i for i in invoices if i["invoice_number"] == "INV-5501")
            self.assertEqual(matched_inv["vendor_name"], "Karan Logistics")
            self.assertEqual(matched_inv["total_amount"], "98500.00")
            self.assertEqual(matched_inv["vendor_gstin"], "06AAAAA0000A1Z5")


if __name__ == "__main__":
    unittest.main()
