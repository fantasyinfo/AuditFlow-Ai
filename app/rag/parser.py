import csv
import io
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
import structlog
from pypdf import PdfReader

from app.agent.llm import get_chat_model, is_live_llm_configured

logger = structlog.get_logger()


@dataclass
class ExtractedInvoiceData:
    vendor_name: str
    invoice_number: str
    total_amount: Decimal
    invoice_date: Optional[date] = None
    vendor_gstin: Optional[str] = None
    currency: str = "USD"
    document_type: str = "invoice"
    customer_name: Optional[str] = None
    summary: Optional[str] = None
    net_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    paid_amount: Decimal = Decimal("0.00")
    payment_status: str = "unpaid"
    due_date: Optional[date] = None
    description: Optional[str] = None


@dataclass
class ParsedDocument:
    full_text: str
    pages: list[tuple[int, str]]  # list of (page_number, text)
    extracted_invoice: Optional[ExtractedInvoiceData] = None
    extracted_invoices: list[ExtractedInvoiceData] = field(default_factory=list)


# International and Indian Tax ID / GSTIN
GSTIN_REGEX = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b")
EU_VAT_REGEX = re.compile(r"\b([A-Z]{2}[0-9A-Za-z\+\*\.]{2,12})\b")
US_EIN_REGEX = re.compile(r"\b([0-9]{2}\-[0-9]{7})\b")

# Multi-format reference numbers (Invoices, Quotations, Agreements, POs)
INVOICE_NUM_REGEX = re.compile(
    r"(?:(?:invoice|quotation|quote|estimate|agreement|contract|order|po|bill)\s*(?:no|number|#|num|id|ref)[\s:]*([A-Za-z0-9\-\/]+))",
    re.IGNORECASE,
)

DATE_REGEX = re.compile(
    r"(?:(?:invoice|document|quote|agreement)?\s*date[\s:]*([0-9]{1,4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,4}))",
    re.IGNORECASE,
)

# Textual date (e.g. 12 August 2026, Aug 12, 2026)
TEXT_DATE_REGEX = re.compile(
    r"\b((?:[0-9]{1,2}\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+[0-9]{1,2}[\s,]+[0-9]{4})\b",
    re.IGNORECASE,
)

# International amounts with symbols ($, €, £, ₹, Rs., CHF, ¥, etc.)
AMOUNT_REGEX = re.compile(
    r"(?:(?:total(?:\s*amount)?|grand\s*total|balance\s*due|net\s*amount|contract\s*value|quoted\s*price|amount\s*payable)[\s:₹Rs\.\$€£¥A-Z]*([0-9,]+\.[0-9]{2}))",
    re.IGNORECASE,
)

VENDOR_REGEX = re.compile(
    r"(?:(?:from|vendor|supplier|seller|billed\s*by|service\s*provider|contractor|issued\s*by)[\s:]*([A-Za-z0-9\s,\.&]{3,60}))",
    re.IGNORECASE,
)


def _parse_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d.%m.%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _clean_amount(amt_str: str) -> Optional[Decimal]:
    if not amt_str:
        return None
    try:
        clean_str = re.sub(r"[^0-9\.]", "", amt_str.strip())
        return Decimal(clean_str)
    except (InvalidOperation, ValueError):
        return None


def _detect_currency(text: str) -> str:
    text_sample = text[:1500]
    if "₹" in text_sample or "INR" in text_sample or "Rs." in text_sample:
        return "INR"
    if "€" in text_sample or "EUR" in text_sample:
        return "EUR"
    if "£" in text_sample or "GBP" in text_sample:
        return "GBP"
    if "¥" in text_sample or "JPY" in text_sample or "CNY" in text_sample:
        return "JPY"
    if "CAD" in text_sample:
        return "CAD"
    if "AUD" in text_sample:
        return "AUD"
    return "USD"


def _detect_document_type(text: str) -> str:
    t_lower = text[:1500].lower()
    if any(k in t_lower for k in ("quotation", "price quote", "estimate", "quotation #")):
        return "quotation"
    if any(k in t_lower for k in ("agreement", "contract", "master services", "statement of work", "sow", "service level")):
        return "agreement"
    if any(k in t_lower for k in ("purchase order", "po number", "p.o. #")):
        return "purchase_order"
    return "invoice"


def extract_with_gemini_or_llm(text: str) -> Optional[ExtractedInvoiceData]:
    """Uses Google AI Studio (Gemini) or configured LLM to understand any arbitrary invoice, quotation, or agreement."""
    if not is_live_llm_configured():
        return None

    try:
        llm = get_chat_model(temperature=0.0, max_tokens=500, timeout=12.0)
        if llm is None:
            return None

        prompt = (
            "You are an expert financial and contract parser. "
            "Extract structured metadata from the following international document (which could be an invoice, quotation, contract agreement, or purchase order with any custom layout).\n\n"
            "Return ONLY a valid JSON object with NO markdown ticks, comments, or preamble:\n"
            "{\n"
            '  "document_type": "invoice | quotation | agreement | purchase_order",\n'
            '  "vendor_name": "Entity or vendor name issuing the document",\n'
            '  "customer_name": "Billed party, counterparty or client name",\n'
            '  "reference_number": "Invoice #, Quotation #, Agreement #, or PO #",\n'
            '  "document_date": "YYYY-MM-DD or null",\n'
            '  "total_amount": "numeric string with 2 decimals e.g. 118000.00 or null",\n'
            '  "currency": "USD, EUR, GBP, INR, CAD, AUD, etc.",\n'
            '  "tax_id": "GSTIN, VAT, or EIN if present or null",\n'
            '  "summary": "1-sentence summary of services, goods, or agreement scope"\n'
            "}\n\n"
            f"Document text:\n{text[:4000]}"
        )
        resp = llm.invoke(prompt)
        raw = str(resp.content).strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        data = json.loads(raw)
        vendor = data.get("vendor_name")
        ref_no = data.get("reference_number")
        amt_str = data.get("total_amount")

        if vendor and ref_no and amt_str:
            clean_amt = _clean_amount(str(amt_str))
            if clean_amt is not None:
                inv_date = _parse_date(data.get("document_date", "")) if data.get("document_date") else None
                return ExtractedInvoiceData(
                    vendor_name=str(vendor).strip(),
                    invoice_number=str(ref_no).strip(),
                    total_amount=clean_amt,
                    invoice_date=inv_date,
                    vendor_gstin=data.get("tax_id"),
                    currency=data.get("currency", "USD"),
                    document_type=data.get("document_type", "invoice"),
                    customer_name=data.get("customer_name"),
                    summary=data.get("summary"),
                )
    except Exception as exc:
        logger.warning("LLM entity extraction fallback to heuristics", exc=str(exc))

    return None


def parse_csv(content: bytes) -> ParsedDocument:
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    pages: list[tuple[int, str]] = []
    extracted_invoices: list[ExtractedInvoiceData] = []

    row_texts = []
    for idx, row in enumerate(reader, start=1):
        norm_row = {
            k.strip().lower().replace(" ", "_").replace("-", "_"): (v or "").strip()
            for k, v in row.items()
            if k
        }
        row_summary = ", ".join(f"{k}: {v}" for k, v in norm_row.items())
        row_line = f"Row {idx}: {row_summary}"
        row_texts.append(row_line)

        # 1. Vendor
        vendor = (
            norm_row.get("vendor_name")
            or norm_row.get("vendor")
            or norm_row.get("supplier_name")
            or norm_row.get("supplier")
            or norm_row.get("company_name")
            or norm_row.get("company")
            or norm_row.get("contractor")
            or norm_row.get("service_provider")
            or norm_row.get("billed_by")
            or norm_row.get("seller")
            or norm_row.get("merchant")
        )
        if not vendor:
            for k, v in norm_row.items():
                if ("vendor" in k or "supplier" in k) and v:
                    vendor = v
                    break

        # 2. Customer
        customer = (
            norm_row.get("customer_name")
            or norm_row.get("customer")
            or norm_row.get("client_name")
            or norm_row.get("client")
            or norm_row.get("billed_to")
        )

        # 3. Invoice Number / Reference
        inv_no = (
            norm_row.get("invoice_id")
            or norm_row.get("invoice_no")
            or norm_row.get("invoice_num")
            or norm_row.get("invoice_number")
            or norm_row.get("inv_id")
            or norm_row.get("inv_no")
            or norm_row.get("inv_num")
            or norm_row.get("inv_number")
            or norm_row.get("invoice_#")
            or norm_row.get("bill_no")
            or norm_row.get("bill_num")
            or norm_row.get("bill_id")
            or norm_row.get("reference_no")
            or norm_row.get("reference_number")
            or norm_row.get("quote_number")
            or norm_row.get("quote_id")
            or norm_row.get("agreement_number")
            or norm_row.get("po_number")
            or norm_row.get("po_id")
            or norm_row.get("id")
        )
        if not inv_no:
            for k, v in norm_row.items():
                if ("invoice" in k or "bill" in k or "inv" in k) and any(x in k for x in ("id", "no", "num")) and v:
                    inv_no = v
                    break

        # 4. Total Amount
        amt_raw = (
            norm_row.get("total_amount_inr")
            or norm_row.get("total_amount_usd")
            or norm_row.get("total_amount_eur")
            or norm_row.get("total_amount")
            or norm_row.get("total_inr")
            or norm_row.get("total_usd")
            or norm_row.get("total")
            or norm_row.get("grand_total")
            or norm_row.get("gross_amount")
            or norm_row.get("amount_inr")
            or norm_row.get("amount_usd")
            or norm_row.get("amount")
            or norm_row.get("net_amount")
            or norm_row.get("contract_value")
            or norm_row.get("balance_due")
        )
        if not amt_raw:
            for k, v in norm_row.items():
                if "total" in k and any(x in k for x in ("amount", "inr", "usd", "val")) and v:
                    amt_raw = v
                    break

        # 5. Net Amount (Subtotal)
        net_raw = (
            norm_row.get("subtotal_inr")
            or norm_row.get("subtotal_usd")
            or norm_row.get("subtotal")
            or norm_row.get("net_amount_inr")
            or norm_row.get("net_amount_usd")
            or norm_row.get("net_amount")
            or norm_row.get("base_amount")
            or norm_row.get("taxable_amount")
        )

        # 6. Tax Amount
        tax_raw = (
            norm_row.get("tax_amount_inr")
            or norm_row.get("tax_amount_usd")
            or norm_row.get("tax_amount")
            or norm_row.get("tax_inr")
            or norm_row.get("tax")
            or norm_row.get("gst_amount")
            or norm_row.get("gst")
            or norm_row.get("vat_amount")
            or norm_row.get("vat")
        )

        # 7. Tax Rate
        tax_rate_raw = (
            norm_row.get("tax_rate_percent")
            or norm_row.get("tax_rate")
            or norm_row.get("gst_rate")
            or norm_row.get("tax_percent")
        )

        # 8. GSTIN / Tax ID
        gstin = (
            norm_row.get("vendor_gstin")
            or norm_row.get("gstin")
            or norm_row.get("tax_id")
            or norm_row.get("vat_number")
            or norm_row.get("vat")
            or norm_row.get("ein")
        )

        # 9. Dates
        date_raw = (
            norm_row.get("invoice_date")
            or norm_row.get("bill_date")
            or norm_row.get("doc_date")
            or norm_row.get("date")
            or norm_row.get("created_date")
            or norm_row.get("effective_date")
        )
        due_date_raw = norm_row.get("due_date") or norm_row.get("payment_due_date")

        # 10. Payment Status & Paid Amount
        status_raw = (
            norm_row.get("payment_status")
            or norm_row.get("paid_status")
            or norm_row.get("status")
            or norm_row.get("payment")
        )
        paid_amt_raw = (
            norm_row.get("paid_amount_inr")
            or norm_row.get("paid_amount_usd")
            or norm_row.get("paid_amount")
            or norm_row.get("amount_paid")
            or norm_row.get("paid")
        )

        currency = norm_row.get("currency") or _detect_currency(text)
        description = norm_row.get("description") or norm_row.get("summary") or norm_row.get("item_description")

        if vendor and inv_no and amt_raw:
            dec_amt = _clean_amount(amt_raw)
            if dec_amt is not None and dec_amt > Decimal("0.00"):
                parsed_dt = _parse_date(date_raw) if date_raw else None
                parsed_due_dt = _parse_date(due_date_raw) if due_date_raw else None
                dec_net = _clean_amount(net_raw) if net_raw else Decimal("0.00")
                dec_tax = _clean_amount(tax_raw) if tax_raw else Decimal("0.00")

                # If net/tax missing but tax rate given, compute net and tax
                if (dec_net == 0 or dec_tax == 0) and tax_rate_raw:
                    clean_rate = _clean_amount(tax_rate_raw)
                    if clean_rate and clean_rate > 0:
                        factor = Decimal("1.00") + (clean_rate / Decimal("100.00"))
                        dec_net = (dec_amt / factor).quantize(Decimal("0.01"))
                        dec_tax = dec_amt - dec_net

                # Payment calculations
                dec_paid = _clean_amount(paid_amt_raw) if paid_amt_raw else None
                norm_status = status_raw.strip().lower() if status_raw else "unpaid"

                if dec_paid is not None:
                    if dec_paid >= dec_amt:
                        final_status = "paid"
                    elif dec_paid > Decimal("0.00"):
                        final_status = "partially_paid"
                    else:
                        final_status = "unpaid"
                else:
                    if norm_status in ("paid", "completed", "settled"):
                        final_status = "paid"
                        dec_paid = dec_amt
                    elif norm_status in ("partially paid", "partially_paid", "partial"):
                        final_status = "partially_paid"
                        if dec_net and Decimal("0.00") < dec_net < dec_amt:
                            dec_paid = dec_net
                        else:
                            dec_paid = (dec_amt / Decimal("2.00")).quantize(Decimal("0.01"))
                    else:
                        final_status = "unpaid"
                        dec_paid = Decimal("0.00")

                invoice_obj = ExtractedInvoiceData(
                    vendor_name=vendor,
                    invoice_number=inv_no,
                    total_amount=dec_amt,
                    invoice_date=parsed_dt,
                    vendor_gstin=gstin,
                    currency=currency,
                    document_type="invoice",
                    customer_name=customer,
                    summary=description,
                    net_amount=dec_net or Decimal("0.00"),
                    tax_amount=dec_tax or Decimal("0.00"),
                    paid_amount=dec_paid or Decimal("0.00"),
                    payment_status=final_status,
                    due_date=parsed_due_dt,
                    description=description,
                )
                extracted_invoices.append(invoice_obj)

    full_text = "\n".join(row_texts)
    pages.append((1, full_text))
    primary_extracted = extracted_invoices[0] if extracted_invoices else None
    return ParsedDocument(
        full_text=full_text,
        pages=pages,
        extracted_invoice=primary_extracted,
        extracted_invoices=extracted_invoices,
    )


def parse_pdf(content: bytes) -> ParsedDocument:
    stream = io.BytesIO(content)
    reader = PdfReader(stream)
    pages: list[tuple[int, str]] = []
    full_text_parts = []

    for idx, page in enumerate(reader.pages, start=1):
        txt = page.extract_text() or ""
        pages.append((idx, txt))
        full_text_parts.append(txt)

    full_text = "\n\n".join(full_text_parts)

    # First attempt: Google AI Studio / LLM extraction for flexible non-fixed markups
    extracted = extract_with_gemini_or_llm(full_text)
    if extracted is not None:
        return ParsedDocument(
            full_text=full_text,
            pages=pages,
            extracted_invoice=extracted,
            extracted_invoices=[extracted],
        )

    # Fallback: Robust Multi-Pattern Regex Extraction
    vendor_match = VENDOR_REGEX.search(full_text)
    inv_num_match = INVOICE_NUM_REGEX.search(full_text)
    date_match = DATE_REGEX.search(full_text) or TEXT_DATE_REGEX.search(full_text)
    amt_match = AMOUNT_REGEX.search(full_text)
    gstin_match = GSTIN_REGEX.search(full_text) or EU_VAT_REGEX.search(full_text) or US_EIN_REGEX.search(full_text)

    vendor_name = None
    if vendor_match:
        vendor_name = vendor_match.group(1).strip()
    else:
        for line in full_text.splitlines():
            line_clean = line.strip()
            if line_clean and len(line_clean) > 2 and not any(k in line_clean.lower() for k in ("invoice", "tax", "page", "date")):
                vendor_name = line_clean[:100]
                break

    if inv_num_match and amt_match and vendor_name:
        inv_no = inv_num_match.group(1).strip()
        amt_dec = _clean_amount(amt_match.group(1))
        if amt_dec is not None:
            inv_date = _parse_date(date_match.group(1)) if date_match else None
            gstin = gstin_match.group(1) if gstin_match else None
            extracted = ExtractedInvoiceData(
                vendor_name=vendor_name,
                invoice_number=inv_no,
                total_amount=amt_dec,
                invoice_date=inv_date,
                vendor_gstin=gstin,
                currency=_detect_currency(full_text),
                document_type=_detect_document_type(full_text),
            )

    invoices_list = [extracted] if extracted else []
    return ParsedDocument(
        full_text=full_text,
        pages=pages,
        extracted_invoice=extracted,
        extracted_invoices=invoices_list,
    )


def parse_document(filename: str, content: bytes) -> ParsedDocument:
    _, ext = os.path.splitext(filename.lower())
    if ext == ".csv":
        return parse_csv(content)
    elif ext == ".pdf":
        return parse_pdf(content)
    else:
        txt = content.decode("utf-8", errors="replace")
        return ParsedDocument(full_text=txt, pages=[(1, txt)], extracted_invoice=None, extracted_invoices=[])
