from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AuditEngagementCreate(BaseModel):
    client_id: str
    engagement_id: str | None = None
    audit_type: str = "Secretarial Audit"
    audit_period_label: str = Field(min_length=1, max_length=120)
    period_start: date | None = None
    period_end: date | None = None
    remarks: str | None = None


class AuditEngagementUpdate(BaseModel):
    status: str | None = None
    remarks: str | None = None


class AuditItemUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(Pending|In Progress|Complied|Not Complied|Not Applicable)$",
    )
    auditor_remarks: str | None = None
    observation_notes: str | None = None
    evidence_notes: str | None = None


class AuditEvidenceAttachmentRead(ORMBase):
    attachment_id: str
    item_id: str
    original_file_name: str
    stored_file_name: str
    content_type: str | None = None
    file_size: int
    relative_path: str
    created_at: datetime


class AuditEngagementItemRead(ORMBase):
    item_id: str
    audit_id: str
    law_id: str | None = None
    law_name: str | None = None
    regulator: str | None = None
    authority_level: str | None = None
    document_type: str | None = None
    applicability_type: str | None = None
    applicability_trigger: str | None = None
    provision_id: str | None = None
    provision_name: str | None = None
    statutory_reference: str | None = None
    compliance_id: str | None = None
    compliance_requirement: str | None = None
    compliance_objective: str | None = None
    compliance_frequency: str | None = None
    audit_procedure_id: str | None = None
    audit_procedure: str | None = None
    audit_method: str | None = None
    audit_frequency: str | None = None
    evidence_template: str | None = None
    evidence_type: str | None = None
    evidence_mandatory: str | None = None
    observation_template: str | None = None
    priority: str | None = None
    risk_level: str | None = None
    origin: str | None = None
    status: str
    auditor_remarks: str | None = None
    observation_notes: str | None = None
    evidence_notes: str | None = None
    display_order: int
    attachments: list[AuditEvidenceAttachmentRead] = []


class AuditEngagementRead(ORMBase):
    audit_id: str
    firm_id: str
    client_id: str
    engagement_id: str | None = None
    audit_type: str
    audit_period_label: str
    period_start: date | None = None
    period_end: date | None = None
    status: str
    sector_id: str
    sub_sector_id: str
    client_name: str
    sector_name: str | None = None
    sub_sector_name: str | None = None
    total_items: int
    completed_items: int
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class AuditEngagementDetail(AuditEngagementRead):
    items: list[AuditEngagementItemRead]


class AuditLawSummary(BaseModel):
    law_id: str | None = None
    parent_law_id: str | None = None
    parent_law_name: str | None = None
    law_name: str
    origin_scope: str | None = None
    regulator: str | None = None
    authority_level: str | None = None
    document_type: str | None = None
    applicability_type: str | None = None
    total_items: int
    completed_items: int


class AuditProvisionSummary(BaseModel):
    provision_id: str | None = None
    provision_name: str
    statutory_reference: str | None = None
    origin_scope: str | None = None
    total_items: int
    completed_items: int
