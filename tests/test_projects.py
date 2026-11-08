import decimal
import unittest
import uuid
import httpx

from app.database import SyncSessionLocal
from app.models.invoice import Invoice
from app.models.project import Project
from app.models.tenant import Tenant
from app.rules.run_rules import run_all_rules


class TestProjectWorkspacesAndReconciliation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = SyncSessionLocal()
        self.uid = uuid.uuid4().hex[:8]
        self.tenant_name = f"ProjectOrg_{self.uid}"
        self.tenant_slug = f"proj-slug-{self.uid}"
        self.admin_email = f"project_auditor_{self.uid}@test.com"
        self.admin_password = "SecurePassword123!"

    def tearDown(self):
        self.db.close()

    async def test_create_and_list_projects(self):
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=15.0) as client:
            # Register tenant
            reg_res = await client.post(
                "/auth/register",
                json={
                    "tenant_name": self.tenant_name,
                    "tenant_slug": self.tenant_slug,
                    "email": self.admin_email,
                    "password": self.admin_password,
                },
            )
            self.assertEqual(reg_res.status_code, 201)
            token = reg_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create Project
            res = await client.post(
                "/projects",
                headers=headers,
                json={
                    "name": "Cloud Infrastructure ERP Upgrade",
                    "code": f"PRJ-CLOUD-{self.uid}",
                    "vendor_name": "TechNova Cloud Systems",
                    "vendor_gstin": "27AAACT2941Q1ZS",
                    "budget_amount": "1000000.00",
                    "budget_currency": "INR",
                    "gst_rate_percent": "18.00",
                    "over_billing_tolerance_percent": "5.00",
                    "single_invoice_cap": "500000.00",
                },
            )
            self.assertEqual(res.status_code, 201)
            data = res.json()
            self.assertEqual(data["name"], "Cloud Infrastructure ERP Upgrade")
            project_id = data["id"]

            # List Projects
            list_res = await client.get("/projects", headers=headers)
            self.assertEqual(list_res.status_code, 200)
            items = list_res.json()["projects"]
            self.assertGreaterEqual(len(items), 1)
            p = next(p for p in items if p["id"] == project_id)
            self.assertEqual(p["vendor_name"], "TechNova Cloud Systems")
            self.assertEqual(float(p["budget_amount"]), 1000000.00)

    async def test_reconciliation_math_and_gst_dissection(self):
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=15.0) as client:
            # Register tenant
            reg_res = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Org Recon {self.uid}",
                    "tenant_slug": f"recon-slug-{self.uid}",
                    "email": f"recon_{self.uid}@test.com",
                    "password": self.admin_password,
                },
            )
            self.assertEqual(reg_res.status_code, 201)
            token = reg_res.json()["access_token"]
            tenant_uuid = uuid.UUID(reg_res.json()["tenant_id"])
            headers = {"Authorization": f"Bearer {token}"}

            # 1. Create Project with ₹10,00,000 budget and 18% GST
            proj_res = await client.post(
                "/projects",
                headers=headers,
                json={
                    "name": "Logistics Master Contract",
                    "code": f"PRJ-LOG-{self.uid}",
                    "vendor_name": "Apex Cargo Ltd",
                    "vendor_gstin": "27AABCA1234Z1ZA",
                    "budget_amount": "1000000.00",
                    "gst_rate_percent": "18.00",
                },
            )
            self.assertEqual(proj_res.status_code, 201)
            project_id = proj_res.json()["id"]
            proj_uuid = uuid.UUID(project_id)

            # 2. Add 2 Invoices in DB directly
            inv1 = Invoice(
                tenant_id=tenant_uuid,
                project_id=proj_uuid,
                vendor_name="Apex Cargo Ltd",
                invoice_number=f"INV-APX-101-{self.uid}",
                total_amount=decimal.Decimal("600000.00"),
                net_amount=decimal.Decimal("508474.58"),
                tax_amount=decimal.Decimal("91525.42"),
                paid_amount=decimal.Decimal("0.00"),
            )
            inv2 = Invoice(
                tenant_id=tenant_uuid,
                project_id=proj_uuid,
                vendor_name="Apex Cargo Ltd",
                invoice_number=f"INV-APX-102-{self.uid}",
                total_amount=decimal.Decimal("500000.00"),
                net_amount=decimal.Decimal("423728.81"),
                tax_amount=decimal.Decimal("76271.19"),
                paid_amount=decimal.Decimal("0.00"),
            )
            self.db.add_all([inv1, inv2])
            self.db.commit()
            inv1_id = str(inv1.id)

            # 3. Fetch Reconciliation
            recon_res = await client.get(f"/projects/{project_id}/reconciliation", headers=headers)
            self.assertEqual(recon_res.status_code, 200)
            recon = recon_res.json()

            # Total Invoiced = 6,00,000 + 5,00,000 = 11,00,000
            self.assertEqual(float(recon["total_invoiced_gross"]), 1100000.00)
            # Quoted Gross = 10,00,000
            self.assertEqual(float(recon["quoted_gross"]), 1000000.00)
            # Over-logged by 1,00,000 (+10.0%)
            self.assertTrue(recon["is_over_logged"])
            self.assertEqual(float(recon["over_logged_amount"]), 100000.00)
            self.assertEqual(float(recon["variance_percent"]), 10.0)
            self.assertEqual(float(recon["burn_rate_percent"]), 110.0)

            # Base amount without GST total = 508474.58 + 423728.81 = 932203.39
            self.assertAlmostEqual(float(recon["total_invoiced_net"]), 932203.39, places=1)
            # Tax total = 91525.42 + 76271.19 = 167796.61
            self.assertAlmostEqual(float(recon["total_invoiced_gst"]), 167796.61, places=1)

            # 4. Record Payment of ₹4,00,000 against INV-APX-101
            pay_res = await client.post(
                f"/projects/{project_id}/invoices/{inv1_id}/payments",
                headers=headers,
                json={"paid_amount": "400000.00"},
            )
            self.assertEqual(pay_res.status_code, 200)
            self.assertEqual(pay_res.json()["payment_status"], "partially_paid")
            self.assertEqual(float(pay_res.json()["paid_amount"]), 400000.00)
            self.assertEqual(float(pay_res.json()["remaining_unpaid"]), 200000.00)

            # 5. Verify remaining balance in reconciliation
            recon2 = (await client.get(f"/projects/{project_id}/reconciliation", headers=headers)).json()
            self.assertEqual(float(recon2["total_paid_gross"]), 400000.00)
            # Remaining under quotation = 10,00,000 - 4,00,000 = 6,00,000
            self.assertEqual(float(recon2["remaining_balance_under_quotation"]), 600000.00)

    async def test_project_multitenancy_isolation(self):
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=15.0) as client:
            # Tenant A registers
            reg_a = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Org A {self.uid}",
                    "email": f"tenant_a_{self.uid}@test.com",
                    "password": self.admin_password,
                },
            )
            token_a = reg_a.json()["access_token"]
            headers_a = {"Authorization": f"Bearer {token_a}"}

            # Tenant A creates project
            res_a = await client.post(
                "/projects",
                headers=headers_a,
                json={
                    "name": "Secret Project Tenant A",
                    "code": f"PRJ-SEC-A-{self.uid}",
                    "vendor_name": "Vendor A",
                    "budget_amount": "50000.00",
                },
            )
            project_id = res_a.json()["id"]

            # Tenant B registers
            reg_b = await client.post(
                "/auth/register",
                json={
                    "tenant_name": f"Org B {self.uid}",
                    "email": f"tenant_b_{self.uid}@test.com",
                    "password": self.admin_password,
                },
            )
            token_b = reg_b.json()["access_token"]
            headers_b = {"Authorization": f"Bearer {token_b}"}

            # Tenant B attempts to fetch Tenant A's project -> 404
            cross_res = await client.get(f"/projects/{project_id}", headers=headers_b)
            self.assertEqual(cross_res.status_code, 404)

            # Tenant B listing does not include Project A
            list_b = await client.get("/projects", headers=headers_b)
            self.assertEqual(len(list_b.json()["projects"]), 0)

    def test_sync_project_rules_overbudget_and_caps(self):
        """Test synchronous rule execution for project over-budget and cap violations."""
        session = SyncSessionLocal()
        try:
            tenant = Tenant(name=f"Test Sync Rules Org {uuid.uuid4().hex[:6]}")
            session.add(tenant)
            session.flush()

            project = Project(
                tenant_id=tenant.id,
                name="Hardware Fleet Rollout",
                code=f"PRJ-HW-{uuid.uuid4().hex[:6]}",
                vendor_name="Hardware Corp",
                budget_amount=decimal.Decimal("200000.00"),
                over_billing_tolerance_percent=decimal.Decimal("5.00"),
                single_invoice_cap=decimal.Decimal("150000.00"),
            )
            session.add(project)
            session.flush()

            # Invoice 1: Exceeds single cap (160,000 > 150,000)
            inv1 = Invoice(
                tenant_id=tenant.id,
                project_id=project.id,
                vendor_name="Hardware Corp",
                invoice_number="INV-HW-1",
                total_amount=decimal.Decimal("160000.00"),
            )
            session.add(inv1)
            session.flush()

            findings = run_all_rules(inv1, session)
            cap_findings = [f for f in findings if f.rule == "project_cap_exceeded"]
            self.assertEqual(len(cap_findings), 1)

            # Invoice 2: Pushes cumulative total to 240,000 (> 200,000 * 1.05 = 210,000)
            inv2 = Invoice(
                tenant_id=tenant.id,
                project_id=project.id,
                vendor_name="Hardware Corp",
                invoice_number="INV-HW-2",
                total_amount=decimal.Decimal("80000.00"),
            )
            session.add(inv2)
            session.flush()

            findings2 = run_all_rules(inv2, session)
            overbudget_findings = [f for f in findings2 if f.rule == "project_overbudget"]
            self.assertEqual(len(overbudget_findings), 1)
            self.assertIn("over-logging the agreed quotation baseline", overbudget_findings[0].reason)

        finally:
            session.rollback()
            session.close()
