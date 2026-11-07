import structlog
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.invoice import Invoice
from app.rules.amount_mismatch import check_amount_mismatch
from app.rules.custom_rule_evaluator import evaluate_custom_rules
from app.rules.duplicate_invoice import check_duplicate_invoice
from app.rules.gstin_check import check_invalid_gstin
from app.rules.missing_evidence import check_missing_evidence
from app.rules.unusual_amount import check_unusual_amount
from app.schemas.finding import FindingCreate

logger = structlog.get_logger()

# Registered audit detection rules list
RULES_REGISTRY = [
    ("duplicate_invoice", check_duplicate_invoice),
    ("amount_mismatch", check_amount_mismatch),
    ("missing_evidence", check_missing_evidence),
    ("invalid_gstin", check_invalid_gstin),
    ("unusual_amount", check_unusual_amount),
]


def run_all_rules(invoice: Invoice, db: Session) -> list[Finding]:
    """Execute all registered deterministic audit rules and tenant custom rules against an invoice."""
    created_findings: list[Finding] = []

    # 1. Run built-in core audit rules
    for rule_name, rule_func in RULES_REGISTRY:
        try:
            result: FindingCreate | None = rule_func(invoice, db)
            if result:
                # Check if this rule finding already exists for this invoice to prevent duplication
                existing = (
                    db.query(Finding)
                    .filter(
                        Finding.tenant_id == invoice.tenant_id,
                        Finding.invoice_id == invoice.id,
                        Finding.rule == result.rule,
                    )
                    .first()
                )

                if not existing:
                    finding_row = Finding(
                        tenant_id=invoice.tenant_id,
                        invoice_id=invoice.id,
                        rule=result.rule,
                        severity=result.severity,
                        reason=result.reason,
                        evidence=result.evidence,
                        status="open",
                    )
                    db.add(finding_row)
                    created_findings.append(finding_row)
                    logger.info(
                        "Audit finding triggered",
                        rule=result.rule,
                        severity=result.severity,
                        invoice_id=str(invoice.id),
                        tenant_id=str(invoice.tenant_id),
                    )
        except Exception as exc:
            logger.exception("Error executing audit rule", rule=rule_name, exc=str(exc))

    # 2. Run tenant-defined custom rules
    try:
        custom_results: list[FindingCreate] = evaluate_custom_rules(invoice, db)
        for c_res in custom_results:
            existing = (
                db.query(Finding)
                .filter(
                    Finding.tenant_id == invoice.tenant_id,
                    Finding.invoice_id == invoice.id,
                    Finding.rule == c_res.rule,
                )
                .first()
            )
            if not existing:
                finding_row = Finding(
                    tenant_id=invoice.tenant_id,
                    invoice_id=invoice.id,
                    rule=c_res.rule,
                    severity=c_res.severity,
                    reason=c_res.reason,
                    evidence=c_res.evidence,
                    status="open",
                )
                db.add(finding_row)
                created_findings.append(finding_row)
                logger.info(
                    "Custom audit rule finding triggered",
                    rule=c_res.rule,
                    severity=c_res.severity,
                    invoice_id=str(invoice.id),
                    tenant_id=str(invoice.tenant_id),
                )
    except Exception as exc:
        logger.exception("Error evaluating custom rules", invoice_id=str(invoice.id), exc=str(exc))

    if created_findings:
        db.commit()

    return created_findings
