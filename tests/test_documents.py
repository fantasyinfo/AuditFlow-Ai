import io
import unittest
import uuid
from httpx import ASGITransport, AsyncClient
from app.database import async_engine
from app.main import app


class TestDocumentIngestion(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await async_engine.dispose()

    async def test_document_ingestion_and_isolation(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            uid_a = uuid.uuid4().hex[:8]
            uid_b = uuid.uuid4().hex[:8]

            # 1. Register Tenant A & Tenant B
            res_a = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Tenant A {uid_a}",
                    "email": f"admin_a_{uid_a}@test.com",
                    "password": "Password123!",
                },
            )
            token_a = res_a.json()["access_token"]

            res_b = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Tenant B {uid_b}",
                    "email": f"admin_b_{uid_b}@test.com",
                    "password": "Password123!",
                },
            )
            token_b = res_b.json()["access_token"]

            # 2. Reject invalid file format (.exe)
            bad_file = io.BytesIO(b"executable content")
            res_bad = await client.post(
                "/documents",
                headers={"Authorization": f"Bearer {token_a}"},
                files={"file": ("virus.exe", bad_file, "application/octet-stream")},
                data={"doc_type": "invoice"},
            )
            self.assertEqual(res_bad.status_code, 422)

            # 3. Successful document upload for Tenant A
            valid_csv = io.BytesIO(b"vendor,invoice_number,amount\nAcme,INV-100,500.00")
            idem_key = f"idem-{uid_a}"
            res_upload = await client.post(
                "/documents",
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": idem_key,
                },
                files={"file": ("invoice_100.csv", valid_csv, "text/csv")},
                data={"doc_type": "invoice"},
            )
            self.assertEqual(res_upload.status_code, 202)
            doc_data = res_upload.json()
            doc_id = doc_data["id"]
            self.assertEqual(doc_data["filename"], "invoice_100.csv")

            # 4. Idempotency test (repeat with same Idempotency-Key)
            valid_csv_replay = io.BytesIO(b"vendor,invoice_number,amount\nAcme,INV-100,500.00")
            res_replay = await client.post(
                "/documents",
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": idem_key,
                },
                files={"file": ("invoice_100.csv", valid_csv_replay, "text/csv")},
                data={"doc_type": "invoice"},
            )
            self.assertEqual(res_replay.status_code, 202)
            self.assertEqual(res_replay.headers.get("x-cache-lookup"), "HIT")
            self.assertEqual(res_replay.json()["id"], doc_id)

            # 5. Fetch document as Tenant A (owner)
            res_get_a = await client.get(
                f"/documents/{doc_id}",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            self.assertEqual(res_get_a.status_code, 200)
            self.assertEqual(res_get_a.json()["id"], doc_id)

            # 6. Tenant B tries to fetch Tenant A's document (Strict Multi-Tenancy Isolation)
            res_get_b = await client.get(
                f"/documents/{doc_id}",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            self.assertEqual(res_get_b.status_code, 404)

            # 7. List documents for Tenant A
            res_list_a = await client.get(
                "/documents",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            self.assertEqual(res_list_a.status_code, 200)
            docs_a = res_list_a.json()
            self.assertTrue(any(d["id"] == doc_id for d in docs_a))

            # 8. List documents for Tenant B (should be empty)
            res_list_b = await client.get(
                "/documents",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            self.assertEqual(res_list_b.status_code, 200)
            self.assertEqual(len(res_list_b.json()), 0)


if __name__ == "__main__":
    unittest.main()
