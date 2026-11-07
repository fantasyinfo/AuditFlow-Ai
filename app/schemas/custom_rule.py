import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CustomRuleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Human readable rule name")
    code: str = Field(..., min_length=2, max_length=50, description="Unique machine identifier for rule")
    severity: str = Field("medium", description="critical | high | medium | low")
    rule_type: str = Field(..., description="amount_threshold | vendor_match | missing_field | date_check | keyword_check")
    field_to_evaluate: str = Field("total_amount", description="Field to inspect (e.g. total_amount, vendor_name, vendor_gstin)")
    operator: str = Field(">", description="Comparison operator (> | >= | < | <= | == | contains | is_empty)")
    threshold_value: str = Field(..., description="Comparison operand (number, string, or keyword)")
    reason_template: str = Field(
        "Invoice violates custom policy rule {name}.",
        description="Audit alert explanation template",
    )
    is_active: bool = Field(True, description="Whether rule is active during ingestion")


class CustomRuleCreate(CustomRuleBase):
    pass


class CustomRuleUpdate(BaseModel):
    name: str | None = None
    severity: str | None = None
    rule_type: str | None = None
    field_to_evaluate: str | None = None
    operator: str | None = None
    threshold_value: str | None = None
    reason_template: str | None = None
    is_active: bool | None = None


class CustomRuleResponse(CustomRuleBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleCatalogItem(BaseModel):
    code: str
    name: str
    severity: str
    description: str
    is_custom: bool
    is_active: bool = True
    custom_rule_id: uuid.UUID | None = None
    rule_type: str | None = None
    field_to_evaluate: str | None = None
    operator: str | None = None
    threshold_value: str | None = None
    reason_template: str | None = None

