import csv
import io
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
from pypdf import PdfReader


@dataclass
class ExtractedInvoiceData:
    vendor_name: str
    invoice_number: str
    total_amount: Decimal
    invoice_date: Optional[date] = None
    vendor_gstin: Optional[str] = None


@dataclass
class ParsedDocument:
    full_text: str
    pages: list[tuple[int, str]]  # list of (page_number, text)
    extracted_invoice: Optional[ExtractedInvoiceData] = None


GSTIN_REGEX = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b")
INVOICE_NUM_REGEX = re.compile(
    r"(?:invoice\s*(?:no|number|#|num|id)[\s:]*([A-Za-z0-9\-\/]+))",
    re.IGNORECASE,
)
DATE_REGEX = re.compile(
    r"(?:(?:invoice\s*)?date[\s:]*([0-9]{1,4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,4}))",
    re.IGNORECASE,
)
AMOUNT_REGEX = re.compile(
    r"(?:(?:total(?:\s*amount)?|grand\s*total|balance\s*due|net\s*amount)[\s:₹Rs\.]*([0-9,]+\.[0-9]{2}))",
    re.IGNORECASE,
)
VENDOR_REGEX = re.compile(
    r"(?:(?:from|vendor|supplier|seller|billed\s*by)[\s:]*([A-Za-z0-9\s,\.&]{3,50}))",
    re.IGNORECASE,
)


def _parse_date(date_str: str) -> Optional[date]:
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _clean_amount(amt_str: str) -> Optional[Decimal]:
    try:
        clean_str = amt_str.replace(",", "").replace("₹", "").replace("Rs.", "").strip()
        return Decimal(clean_str)
    except (InvalidOperation, ValueError):
        return None


def parse_csv(content: bytes) -> ParsedDocument:
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    pages: list[tuple[int, str]] = []
    extracted: Optional[ExtractedInvoiceData] = None

    row_texts = []
    for idx, row in enumerate(reader, start=1):
        # Normalize keys
        norm_row = {k.strip().lower().replace(" ", "_"): (v or "").strip() for k, v in row.items() if k}
        row_summary = ", ".join(f"{k}: {v}" for k, v in norm_row.items())
        row_line = f"Row {idx}: {row_summary}"
        row_texts.append(row_line)

        # Extract invoice fields from the first row that contains amount and vendor
        if extracted is None:
            vendor = (
                norm_row.get("vendor")
                or norm_row.get("vendor_name")
                or norm_row.get("supplier")
                or norm_row.get("company")
            )
            inv_no = (
                norm_row.get("invoice_number")
                or norm_row.get("invoice_no")
                or norm_row.get("invoice_#")
                or norm_row.get("inv_num")
                or norm_row.get("id")
            )
            amt_raw = (
                norm_row.get("amount")
                or norm_row.get("total_amount")
                or norm_row.get("total")
                or norm_row.get("net_amount")
            )
            gstin = (
                norm_row.get("gstin")
                or norm_row.get("vendor_gstin")
                or norm_row.get("tax_id")
            )
            date_raw = (
                norm_row.get("date")
                or norm_row.get("invoice_date")
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

    # Heuristic Regex Extraction
    vendor_match = VENDOR_REGEX.search(full_text)
    inv_num_match = INVOICE_NUM_REGEX.search(full_text)
    date_match = DATE_REGEX.search(full_text)
    amt_match = AMOUNT_REGEX.search(full_text)
    gstin_match = GSTIN_REGEX.search(full_text)

    extracted: Optional[ExtractedInvoiceData] = None

    # Fallback for vendor: if no "From: ...", check first non-empty lines
    vendor_name = None
    if vendor_match:
        vendor_name = vendor_match.group(1).strip()
    else:
        for line in full_text.splitlines():
            line_clean = line.strip()
            if line_clean and len(line_clean) > 2 and "invoice" not in line_clean.lower():
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
            )

    return ParsedDocument(full_text=full_text, pages=pages, extracted_invoice=extracted)


def parse_document(filename: str, content: bytes) -> ParsedDocument:
    _, ext = os.path.splitext(filename.lower())
    if ext == ".csv":
        return parse_csv(content)
    elif ext == ".pdf":
        return parse_pdf(content)
    else:
        # Fallback raw text representation
        txt = content.decode("utf-8", errors="replace")
        return ParsedDocument(full_text=txt, pages=[(1, txt)], extracted_invoice=None)
