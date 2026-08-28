from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SectorRead(ORMBase):
    dataset_key: str
    sector_id: str
    sector_name: str
    description: str | None = None
    active: str
    remark: str | None = None


class SubSectorRead(ORMBase):
    dataset_key: str
    sub_sector_id: str
    sector_id: str
    sub_sector_name: str
    description: str | None = None
    active: str


class LawRead(ORMBase):
    law_id: str
    domain: str
    sector: str
    sub_sector: str
    regulator: str
    authority_level: str | None = None
    document_type: str
    parent_law: str | None = None
    law_name: str
    applicability_type: str
    applicability_trigger: str | None = None
    active: str
    review_frequency: str | None = None
    remarks: str | None = None


class ProvisionRead(ORMBase):
    provision_id: str
    law_id: str
    sub_sector_id: str | None = None
    provision_category: str
    statutory_reference: str | None = None
    provision_name: str
    provision_description: str | None = None
    origin: str
    active: str
    remarks: str | None = None


class ComplianceRequirementRead(ORMBase):
    compliance_id: str
    provision_id: str
    compliance_area_id: str
    compliance_requirement: str
    compliance_objective: str | None = None
    applicability: str | None = None
    frequency: str | None = None
    due_timeline: str | None = None
    responsible_person: str | None = None
    non_compliance_consequence: str | None = None
    priority: str | None = None
    origin: str
    active: str
    remarks: str | None = None


class AuditProcedureRead(ORMBase):
    audit_id: str
    compliance_id: str
    audit_procedure: str
    audit_method: str | None = None
    audit_frequency: str | None = None
    origin: str
    risk_focus: str | None = None
    active: str
    remarks: str | None = None


class EvidenceRead(ORMBase):
    evidence_id: str
    audit_id: str
    evidence_required: str
    evidence_type: str | None = None
    mandatory: str
    retention_category: str | None = None
    origin: str
    active: str
    remarks: str | None = None


class ObservationRead(ORMBase):
    observation_id: str
    audit_id: str
    observation_template: str
    risk_level: str
    recommendation: str | None = None
    observation_category: str | None = None
    origin: str
    active: str
    remarks: str | None = None
