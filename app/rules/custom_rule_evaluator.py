from datetime import date, datetime
from decimal import Decimal
import structlog
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.custom_rule import CustomRule
from app.models.invoice import Invoice
from app.schemas.finding import FindingCreate

logger = structlog.get_logger()


def evaluate_custom_rules(invoice: Invoice, db: Session) -> list[FindingCreate]:
    """Evaluates all active tenant-defined custom rules against an extracted invoice."""
    findings: list[FindingCreate] = []

    try:
        active_rules: list[CustomRule] = (
            db.query(CustomRule)
            .filter(
                CustomRule.tenant_id == invoice.tenant_id,
                CustomRule.is_active == True,
            )
            .all()
        )
    except Exception as exc:
        logger.exception("Failed to query custom rules", tenant_id=str(invoice.tenant_id), error=str(exc))
        return findings

    if not active_rules:
        return findings

    # Cache document text if any keyword_check rule exists
    doc_text_cache: str | None = None

    for rule in active_rules:
        try:
            triggered = False
            details = {}

            if rule.rule_type == "amount_threshold":
                if invoice.total_amount is not None:
                    try:
                        threshold = Decimal(str(rule.threshold_value).replace(",", "").strip())
                        val = invoice.total_amount
                        op = rule.operator.strip()

                        if op == ">" and val > threshold:
                            triggered = True
                        elif op == ">=" and val >= threshold:
                            triggered = True
                        elif op == "<" and val < threshold:
                            triggered = True
                        elif op == "<=" and val <= threshold:
                            triggered = True
                        elif op in ("==", "=") and val == threshold:
                            triggered = True
                        elif op == "!=" and val != threshold:
                            triggered = True

                        details = {
                            "invoice_amount": str(val),
                            "threshold": str(threshold),
                            "operator": op,
                        }
                    except Exception as e:
                        logger.warning("Error evaluating amount threshold rule", rule_id=str(rule.id), error=str(e))

            elif rule.rule_type == "vendor_match":
                v_name = (invoice.vendor_name or "").strip().lower()
                target = rule.threshold_value.strip().lower()
                op = rule.operator.strip().lower()

                if op == "contains" and target in v_name:
                    triggered = True
                elif op in ("==", "equals", "=") and target == v_name:
                    triggered = True
                elif op == "starts_with" and v_name.startswith(target):
                    triggered = True
                elif op in ("!=", "not_equals") and target != v_name:
                    triggered = True

                details = {"vendor_name": invoice.vendor_name, "target": rule.threshold_value, "operator": op}

            elif rule.rule_type == "missing_field":
                field_name = rule.field_to_evaluate.strip()
                val = getattr(invoice, field_name, None)
                if val is None or str(val).strip() in ("", "None", "none", "null"):
                    triggered = True
                    details = {"missing_field": field_name}

            elif rule.rule_type == "date_check":
                if invoice.invoice_date:
                    try:
                        inv_date = date.fromisoformat(str(invoice.invoice_date).split("T")[0])
                        op = rule.operator.strip().lower()
                        if op == "weekend" and inv_date.weekday() in (5, 6):
                            triggered = True
                            details = {"invoice_date": str(inv_date), "weekday": inv_date.strftime("%A")}
                        elif op == "future" and inv_date > date.today():
                            triggered = True
                            details = {"invoice_date": str(inv_date), "today": str(date.today())}
                    except Exception:
                        pass

            elif rule.rule_type == "keyword_check":
                if doc_text_cache is None:
                    chunks = (
                        db.query(DocumentChunk)
                        .filter(
                            DocumentChunk.tenant_id == invoice.tenant_id,
                            DocumentChunk.document_id == invoice.document_id,
                        )
                        .all()
                    )
                    doc_text_cache = " ".join(c.text for c in chunks).lower()

                target_keyword = rule.threshold_value.strip().lower()
                if target_keyword in doc_text_cache:
                    triggered = True
                    details = {"matched_keyword": rule.threshold_value}

            if triggered:
                # Format custom reason template with dictionary merge
                format_args = {
                    "name": rule.name,
                    "code": rule.code,
                    "vendor": invoice.vendor_name or "Unknown Vendor",
                    "amount": f"₹{invoice.total_amount:,.2f}" if invoice.total_amount else "0.00",
                    "threshold": rule.threshold_value,
                    "invoice_number": invoice.invoice_number or "N/A",
                }
                format_args.update(details)
                try:
                    reason_msg = rule.reason_template.format(**format_args)
                except Exception as format_err:
                    logger.warning("Formatting custom reason template failed", error=str(format_err))
                    reason_msg = f"Custom rule alert: {rule.name} triggered for invoice {invoice.invoice_number or ''} ({rule.threshold_value})."

                findings.append(
                    FindingCreate(
                        rule=rule.code,
                        severity=rule.severity,
                        reason=reason_msg,
                        evidence={
                            "custom_rule_id": str(rule.id),
                            "custom_rule_name": rule.name,
                            "rule_type": rule.rule_type,
                            "details": details,
                        },
                    )
                )
        except Exception as exc:
            logger.exception("Failed evaluating custom rule", rule_code=rule.code, error=str(exc))

    return findings
