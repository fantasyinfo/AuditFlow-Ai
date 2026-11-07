import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.custom_rule import CustomRule
from app.schemas.custom_rule import CustomRuleCreate, CustomRuleUpdate, RuleCatalogItem

# Static list of built-in deterministic audit rules
BUILTIN_RULES: list[RuleCatalogItem] = [
    RuleCatalogItem(
        code="duplicate_invoice",
        name="Duplicate Invoice Detection",
        severity="critical",
        description="Flags invoices submitted with identical vendor + invoice number, or matching vendor + amount + date.",
        is_custom=False,
        is_active=True,
    ),
    RuleCatalogItem(
        code="amount_mismatch",
        name="PO Amount Mismatch",
        severity="high",
        description="Flags difference between invoice total and linked purchase order total exceeding ₹1.00 tolerance.",
        is_custom=False,
        is_active=True,
    ),
    RuleCatalogItem(
        code="missing_evidence",
        name="Missing Evidence / No PO",
        severity="medium",
        description="Flags commercial invoices exceeding ₹10,000 / $1,000 lacking linked purchase order or contract.",
        is_custom=False,
        is_active=True,
    ),
    RuleCatalogItem(
        code="invalid_gstin",
        name="GSTIN / Tax ID Format Check",
        severity="high",
        description="Validates supplier tax numbers against statutory checksum regexes (e.g. Indian 15-char GSTIN, EU VAT).",
        is_custom=False,
        is_active=True,
    ),
    RuleCatalogItem(
        code="unusual_amount",
        name="Unusual Amount Spike",
        severity="medium",
        description="Flags invoices exceeding 2.5x the vendor's historical average billing amount.",
        is_custom=False,
        is_active=True,
    ),
]


class RuleService:
    @staticmethod
    async def list_all_rules(db: AsyncSession, tenant_id: uuid.UUID) -> list[RuleCatalogItem]:
        """Returns all built-in rules plus active and inactive custom rules for the tenant."""
        result = await db.execute(
            select(CustomRule)
            .where(CustomRule.tenant_id == tenant_id)
            .order_by(CustomRule.created_at.desc())
        )
        custom_rows = result.scalars().all()

        catalog: list[RuleCatalogItem] = list(BUILTIN_RULES)

        for cr in custom_rows:
            catalog.append(
                RuleCatalogItem(
                    code=cr.code,
                    name=cr.name,
                    severity=cr.severity,
                    description=f"{cr.rule_type}: {cr.field_to_evaluate} {cr.operator} {cr.threshold_value}",
                    is_custom=True,
                    is_active=cr.is_active,
                    custom_rule_id=cr.id,
                    rule_type=cr.rule_type,
                    field_to_evaluate=cr.field_to_evaluate,
                    operator=cr.operator,
                    threshold_value=cr.threshold_value,
                    reason_template=cr.reason_template,
                )
            )

        return catalog

    @staticmethod
    async def list_custom_rules(db: AsyncSession, tenant_id: uuid.UUID) -> list[CustomRule]:
        result = await db.execute(
            select(CustomRule)
            .where(CustomRule.tenant_id == tenant_id)
            .order_by(CustomRule.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_custom_rule(
        db: AsyncSession, tenant_id: uuid.UUID, payload: CustomRuleCreate
    ) -> CustomRule:
        # Check code uniqueness in tenant
        existing = await db.execute(
            select(CustomRule).where(
                CustomRule.tenant_id == tenant_id,
                CustomRule.code == payload.code.strip(),
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Rule with code '{payload.code}' already exists for your organization.",
            )

        rule = CustomRule(
            tenant_id=tenant_id,
            name=payload.name.strip(),
            code=payload.code.strip(),
            severity=payload.severity.lower().strip(),
            rule_type=payload.rule_type.strip(),
            field_to_evaluate=payload.field_to_evaluate.strip(),
            operator=payload.operator.strip(),
            threshold_value=payload.threshold_value.strip(),
            reason_template=payload.reason_template.strip(),
            is_active=payload.is_active,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def get_custom_rule(
        db: AsyncSession, tenant_id: uuid.UUID, rule_id: uuid.UUID
    ) -> CustomRule:
        result = await db.execute(
            select(CustomRule).where(
                CustomRule.tenant_id == tenant_id,
                CustomRule.id == rule_id,
            )
        )
        rule = result.scalars().first()
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Custom rule not found in your organization.",
            )
        return rule

    @staticmethod
    async def update_custom_rule(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        rule_id: uuid.UUID,
        payload: CustomRuleUpdate,
    ) -> CustomRule:
        rule = await RuleService.get_custom_rule(db, tenant_id, rule_id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(rule, key, val)

        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def delete_custom_rule(
        db: AsyncSession, tenant_id: uuid.UUID, rule_id: uuid.UUID
    ) -> bool:
        rule = await RuleService.get_custom_rule(db, tenant_id, rule_id)
        await db.delete(rule)
        await db.commit()
        return True

