import uuid
from typing import Optional
from langchain_core.tools import BaseTool, tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.finding import Finding
from app.models.invoice import Invoice
from app.models.purchase_order import PurchaseOrder
from app.rag.retriever import search_chunks, search_chunks_sync


def get_agent_tools(db: AsyncSession, tenant_id: uuid.UUID) -> list[BaseTool]:
    """Create tenant-scoped, strictly read-only LangChain tools for async agent execution."""

    @tool
    async def search_documents(query: str) -> str:
        """Search uploaded financial documents (invoices, POs, contracts) using vector semantic search.
        Returns relevant text excerpts along with mandatory [filename.pdf p.X] citation references.
        """
        chunks = await search_chunks(db=db, tenant_id=tenant_id, query=query, limit=5)
        if not chunks:
            return "No matching document chunks found in your documents."

        formatted = []
        for c in chunks:
            formatted.append(f"Citation: {c.citation}\nScore: {c.similarity_score}\nText:\n{c.text}\n")
        return "\n---\n".join(formatted)

    @tool
    async def list_findings(status: Optional[str] = None, rule: Optional[str] = None) -> str:
        """Retrieve audit detection findings for the organization.
        Optional filters:
        - status: 'open', 'confirmed', 'dismissed'
        - rule: 'duplicate_invoice', 'amount_mismatch', 'missing_evidence', 'invalid_gstin', 'unusual_amount'
        Returns findings with [finding #ID] citations.
        """
        stmt = (
            select(Finding, Invoice.invoice_number, Invoice.vendor_name)
            .outerjoin(Invoice, Invoice.id == Finding.invoice_id)
            .where(Finding.tenant_id == tenant_id)
            .order_by(Finding.created_at.desc())
        )
        if status:
            stmt = stmt.where(Finding.status == status.lower())
        if rule:
            stmt = stmt.where(Finding.rule == rule.lower())

        result = await db.execute(stmt.limit(20))
        rows = result.all()

        if not rows:
            return "No audit findings found matching the criteria."

        items = []
        for finding, inv_number, vendor in rows:
            inv_str = f"Invoice: {inv_number or 'N/A'} (Vendor: {vendor or 'N/A'})"
            items.append(
                f"[finding #{finding.id}] - Rule: {finding.rule}, Severity: {finding.severity}, "
                f"Status: {finding.status}, {inv_str}. Reason: {finding.reason}"
            )
        return "\n".join(items)

    @tool
    async def get_invoice(invoice_number: str) -> str:
        """Look up structured invoice details by invoice number or vendor name.
        Returns vendor, invoice number, amount, date, GSTIN, and linked PO details.
        """
        clean_no = invoice_number.strip().lower()
        stmt = (
            select(Invoice, Document.filename, PurchaseOrder.po_number)
            .outerjoin(Document, Document.id == Invoice.document_id)
            .outerjoin(PurchaseOrder, PurchaseOrder.id == Invoice.po_id)
            .where(
                Invoice.tenant_id == tenant_id,
                (Invoice.invoice_number.ilike(f"%{clean_no}%"))
                | (Invoice.vendor_name.ilike(f"%{clean_no}%")),
            )
            .limit(5)
        )
        result = await db.execute(stmt)
        rows = result.all()

        if not rows:
            return f"Invoice '{invoice_number}' not found in your tenant records."

        details = []
        for inv, filename, po_num in rows:
            doc_cite = f"[{filename} p.1]" if filename else "[document p.1]"
            po_str = po_num or "None (Missing PO)"
            amount_str = f"₹{inv.total_amount:,.2f}" if inv.total_amount is not None else "Unknown"
            details.append(
                f"Source: {doc_cite} | Invoice Number: {inv.invoice_number} | Vendor: {inv.vendor_name} | "
                f"Date: {inv.invoice_date} | Amount: {amount_str} | GSTIN: {inv.vendor_gstin or 'None'} | Linked PO: {po_str}"
            )
        return "\n".join(details)

    return [search_documents, list_findings, get_invoice]


def get_sync_agent_tools(db: Session, tenant_id: uuid.UUID) -> list[BaseTool]:
    """Create tenant-scoped, strictly read-only LangChain tools for synchronous execution."""

    @tool
    def search_documents(query: str) -> str:
        """Search uploaded financial documents using vector semantic search."""
        chunks = search_chunks_sync(db=db, tenant_id=tenant_id, query=query, limit=5)
        if not chunks:
            return "No matching document chunks found in your documents."

        formatted = []
        for c in chunks:
            formatted.append(f"Citation: {c.citation}\nScore: {c.similarity_score}\nText:\n{c.text}\n")
        return "\n---\n".join(formatted)

    @tool
    def list_findings(status: Optional[str] = None, rule: Optional[str] = None) -> str:
        """Retrieve audit detection findings for the organization."""
        stmt = (
            select(Finding, Invoice.invoice_number, Invoice.vendor_name)
            .outerjoin(Invoice, Invoice.id == Finding.invoice_id)
            .where(Finding.tenant_id == tenant_id)
            .order_by(Finding.created_at.desc())
        )
        if status:
            stmt = stmt.where(Finding.status == status.lower())
        if rule:
            stmt = stmt.where(Finding.rule == rule.lower())

        rows = db.execute(stmt.limit(20)).all()
        if not rows:
            return "No audit findings found matching the criteria."

        items = []
        for finding, inv_number, vendor in rows:
            inv_str = f"Invoice: {inv_number or 'N/A'} (Vendor: {vendor or 'N/A'})"
            items.append(
                f"[finding #{finding.id}] - Rule: {finding.rule}, Severity: {finding.severity}, "
                f"Status: {finding.status}, {inv_str}. Reason: {finding.reason}"
            )
        return "\n".join(items)

    @tool
    def get_invoice(invoice_number: str) -> str:
        """Look up structured invoice details by invoice number or vendor name."""
        clean_no = invoice_number.strip().lower()
        stmt = (
            select(Invoice, Document.filename, PurchaseOrder.po_number)
            .outerjoin(Document, Document.id == Invoice.document_id)
            .outerjoin(PurchaseOrder, PurchaseOrder.id == Invoice.po_id)
            .where(
                Invoice.tenant_id == tenant_id,
                (Invoice.invoice_number.ilike(f"%{clean_no}%"))
                | (Invoice.vendor_name.ilike(f"%{clean_no}%")),
            )
            .limit(5)
        )
        rows = db.execute(stmt).all()
        if not rows:
            return f"Invoice '{invoice_number}' not found in your tenant records."

        details = []
        for inv, filename, po_num in rows:
            doc_cite = f"[{filename} p.1]" if filename else "[document p.1]"
            po_str = po_num or "None (Missing PO)"
            amount_str = f"₹{inv.total_amount:,.2f}" if inv.total_amount is not None else "Unknown"
            details.append(
                f"Source: {doc_cite} | Invoice Number: {inv.invoice_number} | Vendor: {inv.vendor_name} | "
                f"Date: {inv.invoice_date} | Amount: {amount_str} | GSTIN: {inv.vendor_gstin or 'None'} | Linked PO: {po_str}"
            )
        return "\n".join(details)

    return [search_documents, list_findings, get_invoice]
