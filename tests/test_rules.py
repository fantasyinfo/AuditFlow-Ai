import datetime
import decimal
import unittest
import uuid
from httpx import ASGITransport, AsyncClient

from app.database import SyncSessionLocal, async_engine
from app.main import app
from app.models.invoice import Invoice
from app.models.purchase_order import PurchaseOrder
from app.models.tenant import Tenant
from app.rules.amount_mismatch import check_amount_mismatch
from app.rules.duplicate_invoice import check_duplicate_invoice
from app.rules.gstin_check import check_invalid_gstin
from app.rules.missing_evidence import check_missing_evidence
from app.rules.unusual_amount import check_unusual_amount


class TestAuditRules(unittest.TestCase):
    def setUp(self):
        self.session = SyncSessionLocal()
        self.tenant_id = uuid.uuid4()
        tenant = Tenant(id=self.tenant_id, name="Test Audit Org")
        self.session.add(tenant)
        self.session.commit()

    def tearDown(self):
        self.session.rollback()
        # Clean up tenant data
        tenant = self.session.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if tenant:
            self.session.delete(tenant)
            self.session.commit()
        self.session.close()

    def test_duplicate_invoice_rule_positive_and_negative(self):
        # Base invoice
        inv1 = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="ABC Logistics",
            invoice_number="INV-001",
            total_amount=decimal.Decimal("50000.00"),
            invoice_date=datetime.date(2026, 8, 1),
        )
        self.session.add(inv1)
        self.session.commit()

        # Negative test: unique invoice passes
        inv_valid = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="ABC Logistics",
            invoice_number="INV-002",
            total_amount=decimal.Decimal("75000.00"),
            invoice_date=datetime.date(2026, 8, 5),
        )
        self.session.add(inv_valid)
        self.session.commit()
        finding_none = check_duplicate_invoice(inv_valid, self.session)
        self.assertIsNone(finding_none)

        # Positive test 1: same vendor and invoice number (evaluated against existing inv1 in DB)
        inv_dup_num = Invoice(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            vendor_name="ABC Logistics",
            invoice_number="INV-001",
            total_amount=decimal.Decimal("99999.00"),
        )
        finding_num = check_duplicate_invoice(inv_dup_num, self.session)
        self.assertIsNotNone(finding_num)
        self.assertEqual(finding_num.rule, "duplicate_invoice")
        self.assertEqual(finding_num.severity, "critical")

        # Positive test 2: same vendor, amount, date with different invoice number
        inv_dup_amt_date = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="ABC Logistics",
            invoice_number="INV-999-DIFFERENT",
            total_amount=decimal.Decimal("50000.00"),
            invoice_date=datetime.date(2026, 8, 1),
        )
        self.session.add(inv_dup_amt_date)
        self.session.commit()
        finding_amt_date = check_duplicate_invoice(inv_dup_amt_date, self.session)
        self.assertIsNotNone(finding_amt_date)
        self.assertEqual(finding_amt_date.rule, "duplicate_invoice")

    def test_amount_mismatch_rule(self):
        po = PurchaseOrder(
            tenant_id=self.tenant_id,
            po_number="PO-100",
            vendor_name="Dell India",
            total_amount=decimal.Decimal("120000.00"),
        )
        self.session.add(po)
        self.session.commit()

        # Positive: mismatch
        inv_mismatch = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="Dell India",
            invoice_number="INV-DELL-1",
            total_amount=decimal.Decimal("125000.00"),
            po_id=po.id,
        )
        self.session.add(inv_mismatch)
        self.session.commit()
        finding = check_amount_mismatch(inv_mismatch, self.session)
        self.assertIsNotNone(finding)
        self.assertEqual(finding.rule, "amount_mismatch")
        self.assertEqual(finding.severity, "high")

        # Negative: exact match
        inv_match = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="Dell India",
            invoice_number="INV-DELL-2",
            total_amount=decimal.Decimal("120000.00"),
            po_id=po.id,
        )
        self.session.add(inv_match)
        self.session.commit()
        finding_none = check_amount_mismatch(inv_match, self.session)
        self.assertIsNone(finding_none)

    def test_missing_evidence_rule(self):
        # Positive: no PO
        inv_no_po = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="Vendor X",
            invoice_number="INV-X",
            total_amount=decimal.Decimal("15000.00"),
            po_id=None,
        )
        finding = check_missing_evidence(inv_no_po, self.session)
        self.assertIsNotNone(finding)
        self.assertEqual(finding.rule, "missing_evidence")

        # Negative: with PO
        inv_with_po = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="Vendor X",
            invoice_number="INV-Y",
            total_amount=decimal.Decimal("15000.00"),
            po_id=uuid.uuid4(),
        )
        finding_none = check_missing_evidence(inv_with_po, self.session)
        self.assertIsNone(finding_none)

    def test_invalid_gstin_rule(self):
        # Negative: valid Indian GSTIN format
        inv_valid_gst = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="Tata Consultancy",
            invoice_number="INV-T1",
            total_amount=decimal.Decimal("10000.00"),
            vendor_gstin="27AABCA1234F1Z1",
        )
        self.assertIsNone(check_invalid_gstin(inv_valid_gst, self.session))

        # Positive 1: missing GSTIN
        inv_no_gst = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="Informal Vendor",
            invoice_number="INV-I1",
            total_amount=decimal.Decimal("10000.00"),
            vendor_gstin=None,
        )
        finding_no_gst = check_invalid_gstin(inv_no_gst, self.session)
        self.assertIsNotNone(finding_no_gst)
        self.assertEqual(finding_no_gst.rule, "invalid_gstin")

        # Positive 2: malformed GSTIN (wrong length or characters)
        inv_bad_gst = Invoice(
            tenant_id=self.tenant_id,
            vendor_name="Bad GST Vendor",
            invoice_number="INV-B1",
            total_amount=decimal.Decimal("10000.00"),
            vendor_gstin="123INVALID_GSTIN",
        )
        finding_bad_gst = check_invalid_gstin(inv_bad_gst, self.session)
        self.assertIsNotNone(finding_bad_gst)

    def test_unusual_amount_rule(self):
        vendor = "Regular Supplies Ltd"
        # Seed 3 historical invoices averaging 10,000
        for i in range(3):
            self.session.add(
                Invoice(
                    tenant_id=self.tenant_id,
                    vendor_name=vendor,
                    invoice_number=f"HIST-{i}",
                    total_amount=decimal.Decimal("10000.00"),
                )
            )
        self.session.commit()

        # Negative: invoice near average (12,000)
        inv_normal = Invoice(
            tenant_id=self.tenant_id,
            vendor_name=vendor,
            invoice_number="INV-NORM",
            total_amount=decimal.Decimal("12000.00"),
        )
        self.session.add(inv_normal)
        self.session.commit()
        self.assertIsNone(check_unusual_amount(inv_normal, self.session))

        # Positive: invoice 5x average (50,000)
        inv_spike = Invoice(
            tenant_id=self.tenant_id,
            vendor_name=vendor,
            invoice_number="INV-SPIKE",
            total_amount=decimal.Decimal("50000.00"),
        )
        self.session.add(inv_spike)
        self.session.commit()
        finding_spike = check_unusual_amount(inv_spike, self.session)
        self.assertIsNotNone(finding_spike)
        self.assertEqual(finding_spike.rule, "unusual_amount")
        self.assertEqual(finding_spike.severity, "high")


class TestFindingsAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await async_engine.dispose()

    async def test_findings_workflow_and_audit_trail(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            uid = uuid.uuid4().hex[:8]

            # Register tenant
            res_reg = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Findings Tenant {uid}",
                    "email": f"audit_lead_{uid}@company.com",
                    "password": "Password123!",
                },
            )
            token = res_reg.json()["access_token"]
            tenant_id = res_reg.json()["tenant_id"]

            # Create an invoice via direct sync session
            session = SyncSessionLocal()
            inv = Invoice(
                tenant_id=uuid.UUID(tenant_id),
                vendor_name="Flawed Vendor",
                invoice_number=f"INV-{uid}",
                total_amount=decimal.Decimal("75000.00"),
                vendor_gstin=None,  # triggers invalid_gstin
                po_id=None,  # triggers missing_evidence
            )
            session.add(inv)
            session.commit()

            # Run rules
            from app.rules.run_rules import run_all_rules
            run_all_rules(inv, session)
            session.close()

            # 1. Fetch findings list
            res_findings = await client.get(
                "/findings",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(res_findings.status_code, 200)
            findings = res_findings.json()
            self.assertGreaterEqual(len(findings), 1)
            target_finding = findings[0]
            finding_id = target_finding["id"]
            self.assertEqual(target_finding["status"], "open")

            # 2. Update finding to confirmed (PATCH /findings/{id})
            res_patch = await client.patch(
                f"/findings/{finding_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "confirmed", "notes": "Auditor approved"},
            )
            self.assertEqual(res_patch.status_code, 200)
            self.assertEqual(res_patch.json()["status"], "confirmed")

            # 3. Check audit log has recorded the action
            res_audit = await client.get(
                "/audit-logs",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(res_audit.status_code, 200)
            logs = res_audit.json()
            self.assertTrue(any(l["entity_id"] == finding_id for l in logs))
            log_entry = next(l for l in logs if l["entity_id"] == finding_id)
            self.assertEqual(log_entry["action"], "finding.confirmed")
            self.assertEqual(log_entry["before"]["status"], "open")
            self.assertEqual(log_entry["after"]["status"], "confirmed")


if __name__ == "__main__":
    unittest.main()
