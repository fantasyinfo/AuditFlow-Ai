import csv
import io
import json
import os
import re
from dataclasses import dataclass
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


@dataclass
class ParsedDocument:
    full_text: str
    pages: list[tuple[int, str]]  # list of (page_number, text)
    extracted_invoice: Optional[ExtractedInvoiceData] = None


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
    extracted: Optional[ExtractedInvoiceData] = None

    row_texts = []
    for idx, row in enumerate(reader, start=1):
        norm_row = {k.strip().lower().replace(" ", "_"): (v or "").strip() for k, v in row.items() if k}
        row_summary = ", ".join(f"{k}: {v}" for k, v in norm_row.items())
        row_line = f"Row {idx}: {row_summary}"
        row_texts.append(row_line)

        if extracted is None:
            vendor = (
                norm_row.get("vendor")
                or norm_row.get("vendor_name")
                or norm_row.get("supplier")
                or norm_row.get("company")
                or norm_row.get("contractor")
            )
            inv_no = (
                norm_row.get("invoice_number")
                or norm_row.get("invoice_no")
                or norm_row.get("invoice_#")
                or norm_row.get("quote_number")
                or norm_row.get("agreement_number")
                or norm_row.get("po_number")
                or norm_row.get("inv_num")
                or norm_row.get("id")
            )
            amt_raw = (
                norm_row.get("amount")
                or norm_row.get("total_amount")
                or norm_row.get("total")
                or norm_row.get("net_amount")
                or norm_row.get("contract_value")
            )
            gstin = (
                norm_row.get("gstin")
                or norm_row.get("vendor_gstin")
                or norm_row.get("tax_id")
                or norm_row.get("vat")
            )
            date_raw = (
                norm_row.get("date")
                or norm_row.get("invoice_date")
                or norm_row.get("effective_date")
            )

            if vendor and inv_no and amt_raw:
                dec_amt = _clean_amount(amt_raw)
                if dec_amt is not None:
                    parsed_dt = _parse_date(date_raw) if date_raw else None
                    extracted = ExtractedInvoiceData(
                        vendor_name=vendor,
                        invoice_number=inv_no,
                        total_amount=dec_amt,
                        invoice_date=parsed_dt,
                        vendor_gstin=gstin,
                        currency=_detect_currency(text),
                        document_type=_detect_document_type(text),
                    )

    full_text = "\n".join(row_texts)
    pages.append((1, full_text))
    return ParsedDocument(full_text=full_text, pages=pages, extracted_invoice=extracted)


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
        return ParsedDocument(full_text=full_text, pages=pages, extracted_invoice=extracted)

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

    return ParsedDocument(full_text=full_text, pages=pages, extracted_invoice=extracted)


def parse_document(filename: str, content: bytes) -> ParsedDocument:
    _, ext = os.path.splitext(filename.lower())
    if ext == ".csv":
        return parse_csv(content)
    elif ext == ".pdf":
        return parse_pdf(content)
    else:
        txt = content.decode("utf-8", errors="replace")
        return ParsedDocument(full_text=txt, pages=[(1, txt)], extracted_invoice=None)
