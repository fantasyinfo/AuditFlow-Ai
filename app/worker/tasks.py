import uuid
import structlog
from app.database import SyncSessionLocal
from app.models.chunk import DocumentChunk
from app.models.document import Document, DocumentStatus
from app.models.invoice import Invoice
from app.rag.chunker import chunk_document
from app.rag.embedder import embed_texts
from app.rag.parser import parse_document
from app.services.storage import storage_backend
from app.worker.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.worker.tasks.process_document", bind=True, max_retries=3)
def process_document(self, document_id: str, tenant_id: str) -> dict[str, str]:
    """Background task to parse documents, extract invoice metadata, generate embeddings and store chunks."""
    session = SyncSessionLocal()
    try:
        doc_uuid = uuid.UUID(document_id)
        tenant_uuid = uuid.UUID(tenant_id)

        doc = session.query(Document).filter(
            Document.id == doc_uuid,
            Document.tenant_id == tenant_uuid,
        ).first()

        if not doc:
            logger.error(
                "Document not found for processing",
                document_id=document_id,
                tenant_id=tenant_id,
            )
            return {"status": "not_found", "document_id": document_id}

        # Idempotency check: if document already finished processing, return early
        if doc.status == DocumentStatus.DONE.value:
            logger.info("Document already processed, returning done", document_id=document_id)
            return {"status": "done", "document_id": document_id, "already_done": True}

        # Step 1: Mark as processing
        doc.status = DocumentStatus.PROCESSING.value
        session.commit()

        # Step 2: Read binary content from storage
        file_bytes = storage_backend.get_file(doc.storage_path)

        # Step 3: Parse document (PDF / CSV)
        parsed = parse_document(filename=doc.filename, content=file_bytes)

        # Step 4: Chunk document text
        chunks = chunk_document(parsed)

        # Step 5: Generate embeddings for chunks
        chunk_texts = [c.text for c in chunks]
        embeddings = embed_texts(chunk_texts) if chunk_texts else []

        # Step 6: Persist chunks with pgvector embeddings
        for chunk_item, vec in zip(chunks, embeddings):
            chunk_row = DocumentChunk(
                tenant_id=tenant_uuid,
                document_id=doc_uuid,
                chunk_index=chunk_item.chunk_index,
                page=chunk_item.page,
                text=chunk_item.text,
                embedding=vec,
            )
            session.add(chunk_row)

        # Step 7: Persist extracted invoice(s) and evaluate audit rules
        invoices_to_process = (
            parsed.extracted_invoices
            if parsed.extracted_invoices
            else ([parsed.extracted_invoice] if parsed.extracted_invoice else [])
        )

        for inv in invoices_to_process:
            existing_invoice = session.query(Invoice).filter(
                Invoice.tenant_id == tenant_uuid,
                Invoice.vendor_name == inv.vendor_name,
                Invoice.invoice_number == inv.invoice_number,
            ).first()

            target_invoice = existing_invoice
            if not existing_invoice:
                try:
                    with session.begin_nested():
                        invoice_row = Invoice(
                            tenant_id=tenant_uuid,
                            document_id=doc_uuid,
                            project_id=doc.project_id,
                            vendor_name=inv.vendor_name,
                            vendor_gstin=inv.vendor_gstin,
                            invoice_number=inv.invoice_number,
                            invoice_date=inv.invoice_date,
                            total_amount=inv.total_amount,
                            tax_amount=inv.tax_amount,
                            net_amount=inv.net_amount,
                            paid_amount=inv.paid_amount,
                            payment_status=inv.payment_status,
                        )
                        session.add(invoice_row)
                        session.flush()
                        target_invoice = invoice_row
                    logger.info(
                        "Invoice record extracted and saved",
                        vendor=inv.vendor_name,
                        invoice_number=inv.invoice_number,
                        amount=str(inv.total_amount),
                        paid_amount=str(inv.paid_amount),
                        status=inv.payment_status,
                        tenant_id=tenant_id,
                    )
                except Exception as insert_exc:
                    logger.warning("Invoice insert conflict fallback to query", exc=str(insert_exc))
                    target_invoice = session.query(Invoice).filter(
                        Invoice.tenant_id == tenant_uuid,
                        Invoice.vendor_name == inv.vendor_name,
                        Invoice.invoice_number == inv.invoice_number,
                    ).first()
            else:
                if doc.project_id and not existing_invoice.project_id:
                    existing_invoice.project_id = doc.project_id
                if not existing_invoice.document_id:
                    existing_invoice.document_id = doc_uuid
                if inv.net_amount > 0 and existing_invoice.net_amount == 0:
                    existing_invoice.net_amount = inv.net_amount
                if inv.tax_amount > 0 and existing_invoice.tax_amount == 0:
                    existing_invoice.tax_amount = inv.tax_amount
                if inv.paid_amount > 0 and existing_invoice.paid_amount == 0:
                    existing_invoice.paid_amount = inv.paid_amount
                    existing_invoice.payment_status = inv.payment_status
                session.flush()
                target_invoice = existing_invoice

            if target_invoice:
                # Evaluate audit detection rules
                from app.rules.run_rules import run_all_rules
                findings = run_all_rules(target_invoice, session)
                logger.info(
                    "Audit rules evaluated",
                    findings_count=len(findings),
                    invoice_id=str(target_invoice.id),
                    tenant_id=tenant_id,
                )

        # Step 8: Mark document processing complete and record extraction diagnostics
        doc.status = DocumentStatus.DONE.value
        doc.extracted_count = len(invoices_to_process)
        doc.detected_document_type = getattr(parsed, "detected_document_type", None) or doc.type
        doc.ai_model_used = getattr(parsed, "ai_model_used", None) or ("Heuristic Parser" if len(invoices_to_process) > 0 else None)

        if len(invoices_to_process) > 0:
            total_sum = sum(i.total_amount for i in invoices_to_process)
            doc.extraction_summary = (
                f"Successfully extracted {len(invoices_to_process)} commercial record(s) "
                f"totaling ₹{total_sum:.2f} using {doc.ai_model_used or 'parser'}."
            )
            doc.error_message = None
        else:
            doc.extraction_summary = "0 commercial records extracted."
            doc.error_message = (
                "No valid invoice, quotation, or PO line items could be recognized in this file. "
                "Ensure the document contains visible vendor name, invoice reference number, and total amount. "
                "Connect your Google AI Studio Gemini API key to enable universal understanding on arbitrary non-standard formats."
            )

        session.commit()

        logger.info(
            "Document parsing and embedding pipeline complete",
            document_id=document_id,
            chunks_count=len(chunks),
            invoices_extracted_count=len(invoices_to_process),
            model_used=doc.ai_model_used,
            tenant_id=tenant_id,
        )
        return {
            "status": "done",
            "document_id": document_id,
            "chunks": str(len(chunks)),
        }

    except Exception as exc:
        session.rollback()
        logger.exception("Document parsing pipeline failed", exc=exc, document_id=document_id)
        try:
            doc = session.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
            if doc:
                doc.status = DocumentStatus.FAILED.value
                doc.error_message = str(exc)[:1000]
                session.commit()
        except Exception:
            session.rollback()
        raise exc
    finally:
        session.close()
