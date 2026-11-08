import asyncio
from datetime import date, timedelta
from decimal import Decimal
import random
import uuid
import httpx


VENDORS = [
    ("Sharma Traders", "27AAACT2727Q1ZB", 35000),
    ("TechNova Global Ltd", "06AAACT0000Q1Z1", 120000),
    ("Apex Logistics Corp", "29AAACT9999Q1Z9", 85000),
    ("CloudScale Infrastructure", "36AAACT8888Q1Z8", 250000),
    ("Precision Stationery & Supplies", "07AAACT7777Q1Z7", 12000),
    ("Nexus Consulting Partners", "19AAACT6666Q1Z6", 180000),
]


async def seed_demo_data(base_url="http://localhost:8000"):
    """Seeds a rich demonstration tenant with 50 commercial records and planted anomalies."""
    print("\n--- Seeding AuditFlow AI Demo Environment ---")

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # 1. Register Acme Global Enterprise tenant
        uid = uuid.uuid4().hex[:6]
        tenant_name = f"Acme Global Enterprises ({uid})"
        admin_email = f"demo_auditor_{uid}@acme.com"
        admin_password = "AuditFlowDemo2026!"

        res = await client.post(
            "/auth/register",
            json={
                "tenant_name": tenant_name,
                "email": admin_email,
                "password": admin_password,
            },
        )
        if res.status_code != 201:
            print("Registration failed:", res.text)
            return

        token_data = res.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Created Tenant: '{tenant_name}'")
        print(f"Admin Credentials: {admin_email} / {admin_password}")

        # 2. Configure 2 Custom Rules for the tenant
        print("\nConfiguring tenant custom audit rules...")
        await client.post(
            "/rules/custom",
            headers=headers,
            json={
                "name": "Executive Approval Required (> ₹3,00,000)",
                "code": "director_approval_limit",
                "severity": "high",
                "rule_type": "amount_threshold",
                "field_to_evaluate": "total_amount",
                "operator": ">",
                "threshold_value": "300000.00",
                "reason_template": "High-value invoice for {amount} from {vendor} requires Chief Procurement Officer sign-off.",
                "is_active": True,
            },
        )
        await client.post(
            "/rules/custom",
            headers=headers,
            json={
                "name": "Strict Tax Audit Flag",
                "code": "strict_gstin_mandatory",
                "severity": "medium",
                "rule_type": "missing_field",
                "field_to_evaluate": "vendor_gstin",
                "operator": "is_empty",
                "threshold_value": "mandatory",
                "reason_template": "Invoice {invoice_number} from {vendor} is missing statutory tax identification (GSTIN).",
                "is_active": True,
            },
        )
        print("Configured 2 custom rules: [director_approval_limit, strict_gstin_mandatory]")

        # 3. Create 2 Audit Projects with Quotation Baselines
        print("\nConfiguring audit project workspaces with quotation baselines...")
        p1_res = await client.post(
            "/projects",
            headers=headers,
            json={
                "name": "TechNova ERP Cloud Migration",
                "code": "PRJ-TECHNOVA-ERP",
                "description": "Master Service Agreement & hardware/cloud migration procurement engagement.",
                "vendor_name": "TechNova Global Ltd",
                "vendor_gstin": "06AAACT0000Q1Z1",
                "budget_amount": "1500000.00",
                "budget_currency": "INR",
                "gst_rate_percent": "18.00",
                "over_billing_tolerance_percent": "5.00",
                "single_invoice_cap": "500000.00",
            },
        )
        p2_res = await client.post(
            "/projects",
            headers=headers,
            json={
                "name": "Apex Global Fleet Logistics 2026",
                "code": "PRJ-APEX-LOGISTICS",
                "description": "Corporate logistics, freight forwarding and retainer contract.",
                "vendor_name": "Apex Logistics Corp",
                "vendor_gstin": "29AAACT9999Q1Z9",
                "budget_amount": "500000.00",
                "budget_currency": "INR",
                "gst_rate_percent": "18.00",
                "over_billing_tolerance_percent": "5.00",
                "single_invoice_cap": "200000.00",
            },
        )
        print("Created 2 audit projects: [TechNova ERP Cloud Migration, Apex Global Fleet Logistics 2026]")

        # 4. Seed 50 Commercial Invoices with planted anomalies
        print("\nUploading 50 commercial documents across all 4 categories...")
        base_date = date.today() - timedelta(days=60)
        uploaded_count = 0

        # Create master PO for Sharma Traders to test mismatch
        po_number = "PO-2026-SHARMA-01"
        po_amount = Decimal("100000.00")

        # Duplicate anchor invoice
        dup_inv_num = f"INV-ANCHOR-{uid}"
        dup_vendor = "Sharma Traders"
        dup_amount = "118000.00"
        dup_date = (base_date + timedelta(days=5)).isoformat()

        # Generate 50 items
        for i in range(1, 51):
            vendor, gstin, avg_amt = random.choice(VENDORS)
            inv_date = (base_date + timedelta(days=i)).isoformat()
            inv_num = f"INV-2026-{1000 + i}"
            amount = f"{avg_amt + random.randint(-2000, 5000)}.00"
            doc_type = "invoice"

            # Plant anomaly #1: Duplicate invoice
            if i == 10:
                inv_num = dup_inv_num
                vendor = dup_vendor
                amount = dup_amount
                inv_date = dup_date
            elif i == 11:
                # The exact duplicate
                inv_num = dup_inv_num
                vendor = dup_vendor
                amount = dup_amount
                inv_date = dup_date

            # Plant anomaly #2: Massive Amount Spike
            elif i == 20:
                vendor = "Precision Stationery & Supplies"  # avg is 12k
                amount = "480000.00"  # 40x spike!

            # Plant anomaly #3: Invalid GSTIN
            elif i == 30:
                vendor = "Nexus Consulting Partners"
                gstin = "99INVALID0000X9Z"  # checksum / format violation

            # Plant anomaly #4: Missing Tax ID
            elif i == 40:
                gstin = ""  # will trigger custom rule 'strict_gstin_mandatory'

            # Plant anomaly #5: High value threshold
            elif i == 45:
                amount = "550000.00"  # triggers custom rule 'director_approval_limit'

            # Plant quotation
            elif i == 48:
                doc_type = "quotation"
                inv_num = f"QUOTE-DELL-901"
                vendor = "Dell Enterprise Systems"

            # Plant agreement
            elif i == 49:
                doc_type = "agreement"
                inv_num = f"MSA-APEX-2026"
                vendor = "Apex Logistics Corp"

            csv_text = f"invoice_number,vendor_name,date,total_amount,vendor_gstin\n{inv_num},{vendor},{inv_date},{amount},{gstin}\n"
            files = {"file": (f"{inv_num}.csv", csv_text.encode("utf-8"), "text/csv")}
            data = {"document_type": doc_type}
            req_headers = dict(headers)
            req_headers["Idempotency-Key"] = f"seed_{uid}_{i}"

            res = await client.post("/documents", files=files, data=data, headers=req_headers)
            if res.status_code == 202:
                uploaded_count += 1

        print(f"Successfully enqueued {uploaded_count} commercial documents in Redis queue!")
        print("Background Celery workers are now parsing, embedding, and executing rules.")
        print(f"\nSign in to view demo tenant:")
        print(f"URL:      http://localhost:3000 (or http://localhost:8000/app)")
        print(f"Email:    {admin_email}")
        print(f"Password: {admin_password}")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())

