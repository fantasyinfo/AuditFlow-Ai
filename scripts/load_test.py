import json
import random
import uuid
from locust import HttpUser, between, task


class AuditFlowAuditorUser(HttpUser):
    """Simulates an accounts payable auditor concurrently uploading documents and reviewing findings."""

    wait_time = between(0.5, 2.0)

    def on_start(self):
        """Register an isolated test tenant and authenticate to obtain JWT bearer token."""
        self.tenant_uid = uuid.uuid4().hex[:8]
        self.email = f"loadtest_{self.tenant_uid}@auditflow.internal"
        self.password = "LoadTestPass123!"

        res = self.client.post(
            "/auth/register",
            json={
                "tenant_name": f"LoadTest Corp {self.tenant_uid}",
                "email": self.email,
                "password": self.password,
            },
        )
        if res.status_code == 201:
            token = res.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(3)
    def upload_invoice_document(self):
        """Tests API 202 accept rate with idempotency key under concurrent burst traffic."""
        if not self.headers:
            return

        inv_num = f"INV-LT-{random.randint(1000, 99999)}"
        amount = random.randint(5000, 500000)
        vendor = random.choice(["Acme Hardware Ltd", "TechFlow Solutions", "Sharma Global Supplies"])

        csv_content = f"invoice_number,vendor_name,date,total_amount,vendor_gstin\n{inv_num},{vendor},2026-11-07,{amount}.00,27AAACT2727Q1ZB\n"
        files = {
            "file": (f"{inv_num}.csv", csv_content.encode("utf-8"), "text/csv"),
        }
        data = {"document_type": "invoice"}
        headers = dict(self.headers)
        headers["Idempotency-Key"] = f"idemp_{uuid.uuid4().hex}"

        self.client.post("/documents", files=files, data=data, headers=headers)

    @task(5)
    def query_audit_findings(self):
        """Tests high-frequency reads on tenant-scoped findings table."""
        if not self.headers:
            return
        self.client.get("/findings?status=open&limit=20", headers=self.headers)

    @task(3)
    def list_commercial_invoices(self):
        """Tests metadata retrieval for extracted commercial records."""
        if not self.headers:
            return
        self.client.get("/invoices?limit=20", headers=self.headers)

    @task(1)
    def ask_ai_assistant(self):
        """Tests RAG query endpoint under bounded load."""
        if not self.headers:
            return
        payload = {"query": "Are there any duplicate invoices or missing POs?"}
        self.client.post("/agent/ask", json=payload, headers=self.headers, timeout=15.0)

