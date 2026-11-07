from decimal import Decimal
import unittest
import uuid
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.custom_rule import CustomRule
from app.models.invoice import Invoice
from app.models.tenant import Tenant
from app.rules.custom_rule_evaluator import evaluate_custom_rules

settings = get_settings()
engine = create_engine(settings.SYNC_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class TestCustomRules(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.uid = uuid.uuid4().hex[:8]
        self.tenant_name = f"RulesTenant_{self.uid}"
        self.admin_email = f"rules_admin_{self.uid}@test.com"
        self.admin_password = "SecurePassword123!"

    def tearDown(self):
        self.db.close()

    async def test_custom_rule_creation_evaluation_and_api(self):
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=15.0) as client:
            # 1. Register tenant
            reg_res = await client.post(
                "/auth/register",
                json={
                    "tenant_name": self.tenant_name,
                    "email": self.admin_email,
                    "password": self.admin_password,
                },
            )
            self.assertEqual(reg_res.status_code, 201)
            token = reg_res.json()["access_token"]
            tenant_id = uuid.UUID(reg_res.json()["tenant_id"])
            headers = {"Authorization": f"Bearer {token}"}

            # 2. List rules (should have the 5 built-in rules initially)
            list_res = await client.get("/rules", headers=headers)
            self.assertEqual(list_res.status_code, 200)
            initial_rules = list_res.json()
            self.assertGreaterEqual(len(initial_rules), 5)
            self.assertTrue(any(r["code"] == "duplicate_invoice" for r in initial_rules))

            # 3. Create a custom rule: High-Value Threshold (> 75,000)
            create_res = await client.post(
                "/rules/custom",
                headers=headers,
                json={
                    "name": "High Value Invoice Alert",
                    "code": f"high_val_{self.uid}",
                    "severity": "high",
                    "rule_type": "amount_threshold",
                    "field_to_evaluate": "total_amount",
                    "operator": ">",
                    "threshold_value": "75000.00",
                    "reason_template": "Invoice from {vendor} for {amount} exceeds organization limit of ₹{threshold}.",
                    "is_active": True,
                },
            )
            self.assertEqual(create_res.status_code, 201)
            custom_rule_data = create_res.json()
            rule_id = custom_rule_data["id"]
            self.assertEqual(custom_rule_data["severity"], "high")

            # 4. Verify custom rule appears in /rules catalog
            updated_list_res = await client.get("/rules", headers=headers)
            self.assertEqual(updated_list_res.status_code, 200)
            custom_item = next(
                (r for r in updated_list_res.json() if r["code"] == f"high_val_{self.uid}"),
                None,
            )
            self.assertIsNotNone(custom_item)
            self.assertTrue(custom_item["is_custom"])

            # 5. Deterministic evaluation test in Python:
            # Positive test: Invoice amount 1,00,000 > 75,000
            high_invoice = Invoice(
                tenant_id=tenant_id,
                document_id=uuid.uuid4(),
                vendor_name="Acme Supercorp",
                invoice_number=f"INV-HIGH-{self.uid}",
                total_amount=Decimal("100000.00"),
            )
            findings = evaluate_custom_rules(high_invoice, self.db)
            self.assertTrue(any(f.rule == f"high_val_{self.uid}" for f in findings))
            finding = next(f for f in findings if f.rule == f"high_val_{self.uid}")
            self.assertEqual(finding.severity, "high")
            self.assertIn("Acme Supercorp", finding.reason)

            # Negative test: Invoice amount 50,000 < 75,000
            low_invoice = Invoice(
                tenant_id=tenant_id,
                document_id=uuid.uuid4(),
                vendor_name="Acme Supercorp",
                invoice_number=f"INV-LOW-{self.uid}",
                total_amount=Decimal("50000.00"),
            )
            low_findings = evaluate_custom_rules(low_invoice, self.db)
            self.assertFalse(any(f.rule == f"high_val_{self.uid}" for f in low_findings))

            # 6. Delete custom rule
            del_res = await client.delete(f"/rules/custom/{rule_id}", headers=headers)
            self.assertEqual(del_res.status_code, 204)

            # Verify it's gone
            after_del_list = await client.get("/rules", headers=headers)
            self.assertFalse(any(r["code"] == f"high_val_{self.uid}" for r in after_del_list.json()))


if __name__ == "__main__":
    unittest.main()
