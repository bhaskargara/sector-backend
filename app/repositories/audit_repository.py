from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.orm import Session

from app.models.audit import AuditEngagement, AuditEngagementItem, AuditEvidenceAttachment
from app.models.organization import ClientMaster, FirmEnterpriseEngagement, FirmMaster
from app.models.regulatory import (
    AuditProcedureMaster,
    ComplianceRequirementMaster,
    EvidenceMaster,
    LawMaster,
    ObservationMaster,
    ProvisionMaster,
    SectorMaster,
)
from app.schemas.audit import AuditEngagementCreate, AuditEngagementUpdate, AuditItemUpdate

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "audit_evidence"
COMPLETED_STATUSES = {"Complied", "Not Applicable"}


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def _build_evidence_map(db: Session, audit_procedure_ids: set[str]) -> dict[str, list[str]]:
    if not audit_procedure_ids:
        return {}
    rows = db.scalars(
        select(EvidenceMaster)
        .where(EvidenceMaster.audit_id.in_(audit_procedure_ids))
        .order_by(EvidenceMaster.evidence_id)
    ).all()
    result: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        result[row.audit_id].append(row.evidence_required)
    return result


def _build_evidence_metadata_map(
    db: Session,
    audit_procedure_ids: set[str],
) -> dict[str, dict[str, str | None]]:
    if not audit_procedure_ids:
        return {}
    rows = db.scalars(
        select(EvidenceMaster)
        .where(EvidenceMaster.audit_id.in_(audit_procedure_ids))
        .order_by(EvidenceMaster.evidence_id)
    ).all()
    result: dict[str, dict[str, str | None]] = {}
    for row in rows:
        entry = result.setdefault(
            row.audit_id,
            {"evidence_type": None, "evidence_mandatory": None},
        )
        if row.evidence_type and not entry["evidence_type"]:
            entry["evidence_type"] = row.evidence_type
        if row.mandatory:
            if entry["evidence_mandatory"] in {None, "No"} and row.mandatory == "Yes":
                entry["evidence_mandatory"] = "Yes"
            elif entry["evidence_mandatory"] is None:
                entry["evidence_mandatory"] = row.mandatory
    return result


def _build_observation_map(db: Session, audit_procedure_ids: set[str]) -> dict[str, list[str]]:
    if not audit_procedure_ids:
        return {}
    rows = db.scalars(
        select(ObservationMaster)
        .where(ObservationMaster.audit_id.in_(audit_procedure_ids))
        .order_by(ObservationMaster.observation_id)
    ).all()
    result: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        result[row.audit_id].append(row.observation_template)
    return result


def _build_observation_risk_map(db: Session, audit_procedure_ids: set[str]) -> dict[str, str | None]:
    if not audit_procedure_ids:
        return {}
    rows = db.scalars(
        select(ObservationMaster)
        .where(ObservationMaster.audit_id.in_(audit_procedure_ids))
        .order_by(ObservationMaster.observation_id)
    ).all()
    severity_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    result: dict[str, str | None] = {}
    for row in rows:
        current = result.get(row.audit_id)
        next_level = row.risk_level
        if current is None or severity_rank.get(next_level, 0) > severity_rank.get(current, 0):
            result[row.audit_id] = next_level
    return result


def _serialize_engagement(engagement: AuditEngagement) -> AuditEngagement:
    return engagement


def ensure_audit_metadata(db: Session, audit_id: str) -> None:
    missing_metadata_filter = or_(
        AuditEngagementItem.regulator.is_(None),
        AuditEngagementItem.authority_level.is_(None),
        AuditEngagementItem.document_type.is_(None),
        AuditEngagementItem.applicability_type.is_(None),
        AuditEngagementItem.statutory_reference.is_(None),
        AuditEngagementItem.compliance_frequency.is_(None),
        AuditEngagementItem.audit_frequency.is_(None),
        AuditEngagementItem.evidence_type.is_(None),
        AuditEngagementItem.evidence_mandatory.is_(None),
        AuditEngagementItem.risk_level.is_(None),
    )
    missing_item_ids = db.scalars(
        select(AuditEngagementItem.item_id).where(
            AuditEngagementItem.audit_id == audit_id,
            missing_metadata_filter,
        )
    ).all()
    if not missing_item_ids:
        return

    items = db.scalars(
        select(AuditEngagementItem).where(AuditEngagementItem.item_id.in_(missing_item_ids))
    ).all()

    law_ids = {item.law_id for item in items if item.law_id}
    provision_ids = {item.provision_id for item in items if item.provision_id}
    compliance_ids = {item.compliance_id for item in items if item.compliance_id}
    audit_procedure_ids = {item.audit_procedure_id for item in items if item.audit_procedure_id}

    laws = {
        row.law_id: row
        for row in db.scalars(select(LawMaster).where(LawMaster.law_id.in_(law_ids))).all()
    } if law_ids else {}
    provisions = {
        row.provision_id: row
        for row in db.scalars(select(ProvisionMaster).where(ProvisionMaster.provision_id.in_(provision_ids))).all()
    } if provision_ids else {}
    compliances = {
        row.compliance_id: row
        for row in db.scalars(
            select(ComplianceRequirementMaster).where(
                ComplianceRequirementMaster.compliance_id.in_(compliance_ids)
            )
        ).all()
    } if compliance_ids else {}
    audit_procedures = {
        row.audit_id: row
        for row in db.scalars(
            select(AuditProcedureMaster).where(AuditProcedureMaster.audit_id.in_(audit_procedure_ids))
        ).all()
    } if audit_procedure_ids else {}

    evidence_map = _build_evidence_map(db, set(audit_procedure_ids))
    evidence_metadata_map = _build_evidence_metadata_map(db, set(audit_procedure_ids))
    observation_map = _build_observation_map(db, set(audit_procedure_ids))
    observation_risk_map = _build_observation_risk_map(db, set(audit_procedure_ids))

    updated = False
    for item in items:
        law = laws.get(item.law_id or "")
        provision = provisions.get(item.provision_id or "")
        compliance = compliances.get(item.compliance_id or "")
        audit_procedure = audit_procedures.get(item.audit_procedure_id or "")
        audit_procedure_id = item.audit_procedure_id or ""

        next_values = {
            "regulator": law.regulator if law else item.regulator,
            "authority_level": law.authority_level if law else item.authority_level,
            "document_type": law.document_type if law else item.document_type,
            "applicability_type": law.applicability_type if law else item.applicability_type,
            "applicability_trigger": law.applicability_trigger if law else item.applicability_trigger,
            "statutory_reference": provision.statutory_reference if provision else item.statutory_reference,
            "compliance_frequency": compliance.frequency if compliance else item.compliance_frequency,
            "audit_frequency": audit_procedure.audit_frequency if audit_procedure else item.audit_frequency,
            "evidence_template": "\n".join(evidence_map.get(audit_procedure_id, [])) or item.evidence_template,
            "evidence_type": (evidence_metadata_map.get(audit_procedure_id, {}) or {}).get("evidence_type") or item.evidence_type,
            "evidence_mandatory": (evidence_metadata_map.get(audit_procedure_id, {}) or {}).get("evidence_mandatory") or item.evidence_mandatory,
            "observation_template": "\n".join(observation_map.get(audit_procedure_id, [])) or item.observation_template,
            "risk_level": observation_risk_map.get(audit_procedure_id) or item.risk_level,
            "priority": compliance.priority if compliance and compliance.priority else item.priority,
        }

        for field, value in next_values.items():
            if getattr(item, field) != value and value is not None:
                setattr(item, field, value)
                updated = True

    if updated:
        db.commit()


def _recalculate_progress(db: Session, engagement: AuditEngagement) -> None:
    items = db.scalars(
        select(AuditEngagementItem).where(AuditEngagementItem.audit_id == engagement.audit_id)
    ).all()
    engagement.total_items = len(items)
    engagement.completed_items = sum(1 for item in items if item.status in COMPLETED_STATUSES)
    db.commit()
    db.refresh(engagement)


def list_audits(db: Session, firm_id: str) -> list[AuditEngagement]:
    stmt = (
        select(AuditEngagement)
        .where(AuditEngagement.firm_id == firm_id)
        .order_by(AuditEngagement.created_at.desc())
    )
    return db.scalars(stmt).all()


def get_audit(db: Session, firm_id: str, audit_id: str) -> AuditEngagement | None:
    stmt = select(AuditEngagement).where(
        AuditEngagement.firm_id == firm_id,
        AuditEngagement.audit_id == audit_id,
    )
    return db.scalar(stmt)


def get_audit_item(db: Session, audit_id: str, item_id: str) -> AuditEngagementItem | None:
    stmt = select(AuditEngagementItem).where(
        AuditEngagementItem.audit_id == audit_id,
        AuditEngagementItem.item_id == item_id,
    )
    return db.scalar(stmt)


def create_audit(db: Session, firm_id: str, payload: AuditEngagementCreate) -> AuditEngagement:
    firm = db.get(FirmMaster, firm_id)
    if not firm:
        raise ValueError(f"Unknown firm_id: {firm_id}")

    client = db.get(ClientMaster, payload.client_id)
    if not client or client.firm_id != firm_id:
        raise ValueError(f"Unknown client_id for firm {firm_id}: {payload.client_id}")

    engagement_id = payload.engagement_id
    if not engagement_id and client.enterprise_id:
        linked_engagement = db.scalar(
            select(FirmEnterpriseEngagement).where(
                FirmEnterpriseEngagement.firm_id == firm_id,
                FirmEnterpriseEngagement.enterprise_id == client.enterprise_id,
            )
        )
        if linked_engagement:
            engagement_id = linked_engagement.engagement_id

    if engagement_id:
        engagement = db.get(FirmEnterpriseEngagement, engagement_id)
        if not engagement or engagement.firm_id != firm_id:
            raise ValueError(f"Unknown engagement_id for firm {firm_id}: {engagement_id}")
        if client.enterprise_id and engagement.enterprise_id != client.enterprise_id:
            raise ValueError(
                f"Engagement {engagement_id} is not linked to client {client.client_id}"
            )

    existing = db.scalar(
        select(AuditEngagement).where(
            AuditEngagement.firm_id == firm_id,
            AuditEngagement.client_id == client.client_id,
            AuditEngagement.audit_period_label == payload.audit_period_label,
        )
    )
    if existing:
        raise ValueError(
            f"Audit already exists for {client.client_name} in {payload.audit_period_label}"
        )

    rows = db.execute(
        select(
            LawMaster,
            ProvisionMaster,
            ComplianceRequirementMaster,
            AuditProcedureMaster,
        )
        .join(SectorMaster, SectorMaster.sector_name == LawMaster.sector)
        .join(
            ProvisionMaster,
            and_(
                ProvisionMaster.law_id == LawMaster.law_id,
                or_(
                    ProvisionMaster.sub_sector_id == client.sub_sector_id,
                    ProvisionMaster.sub_sector_id.is_(None),
                ),
            ),
        )
        .outerjoin(
            ComplianceRequirementMaster,
            ComplianceRequirementMaster.provision_id == ProvisionMaster.provision_id,
        )
        .outerjoin(
            AuditProcedureMaster,
            AuditProcedureMaster.compliance_id == ComplianceRequirementMaster.compliance_id,
        )
        .where(
            SectorMaster.sector_id == client.sector_id,
        )
        .order_by(
            LawMaster.law_id,
            ProvisionMaster.provision_id,
            ComplianceRequirementMaster.compliance_id,
            AuditProcedureMaster.audit_id,
        )
    ).all()

    if not rows:
        raise ValueError(
            f"No regulatory master data found for sector/sub-sector {client.sector_id}/{client.sub_sector_id}"
        )

    engagement = AuditEngagement(
        audit_id=_new_id("AUD"),
        firm_id=firm_id,
        client_id=client.client_id,
        engagement_id=engagement_id,
        audit_type=payload.audit_type,
        audit_period_label=payload.audit_period_label,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status="In Progress",
        sector_id=client.sector_id,
        sub_sector_id=client.sub_sector_id,
        client_name=client.client_name,
        sector_name=client.sector.sector_name if client.sector else None,
        sub_sector_name=client.sub_sector.sub_sector_name if client.sub_sector else None,
        remarks=payload.remarks,
    )
    db.add(engagement)
    db.commit()
    db.refresh(engagement)

    audit_procedure_ids = {
        audit_procedure.audit_id
        for _, _, _, audit_procedure in rows
        if audit_procedure is not None
    }
    evidence_map = _build_evidence_map(db, audit_procedure_ids)
    evidence_metadata_map = _build_evidence_metadata_map(db, audit_procedure_ids)
    observation_map = _build_observation_map(db, audit_procedure_ids)
    observation_risk_map = _build_observation_risk_map(db, audit_procedure_ids)

    items: list[AuditEngagementItem] = []
    for index, (law, provision, compliance, audit_procedure) in enumerate(rows, start=1):
        audit_procedure_id = audit_procedure.audit_id if audit_procedure else None
        items.append(
            AuditEngagementItem(
                item_id=_new_id("AIT"),
                audit_id=engagement.audit_id,
                law_id=law.law_id,
                law_name=law.law_name,
                regulator=law.regulator,
                authority_level=law.authority_level,
                document_type=law.document_type,
                applicability_type=law.applicability_type,
                applicability_trigger=law.applicability_trigger,
                provision_id=provision.provision_id,
                provision_name=provision.provision_name,
                statutory_reference=provision.statutory_reference,
                compliance_id=compliance.compliance_id if compliance else None,
                compliance_requirement=compliance.compliance_requirement if compliance else None,
                compliance_objective=compliance.compliance_objective if compliance else None,
                compliance_frequency=compliance.frequency if compliance else None,
                audit_procedure_id=audit_procedure_id,
                audit_procedure=audit_procedure.audit_procedure if audit_procedure else None,
                audit_method=audit_procedure.audit_method if audit_procedure else None,
                audit_frequency=audit_procedure.audit_frequency if audit_procedure else None,
                evidence_template="\n".join(evidence_map.get(audit_procedure_id, [])) or None,
                evidence_type=(evidence_metadata_map.get(audit_procedure_id, {}) or {}).get("evidence_type"),
                evidence_mandatory=(evidence_metadata_map.get(audit_procedure_id, {}) or {}).get("evidence_mandatory"),
                observation_template="\n".join(observation_map.get(audit_procedure_id, [])) or None,
                priority=compliance.priority if compliance else None,
                risk_level=observation_risk_map.get(audit_procedure_id),
                origin=compliance.origin if compliance else provision.origin,
                status="Pending",
                display_order=index,
            )
        )

    db.add_all(items)
    db.commit()
    _recalculate_progress(db, engagement)
    return _serialize_engagement(engagement)


def update_audit(
    db: Session,
    firm_id: str,
    audit_id: str,
    payload: AuditEngagementUpdate,
) -> AuditEngagement | None:
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(engagement, field, value)
    db.commit()
    db.refresh(engagement)
    return engagement


def delete_audit(db: Session, firm_id: str, audit_id: str) -> bool:
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        return False

    items = db.scalars(
        select(AuditEngagementItem).where(AuditEngagementItem.audit_id == audit_id)
    ).all()
    item_ids = [item.item_id for item in items]

    attachments = []
    if item_ids:
        attachments = db.scalars(
            select(AuditEvidenceAttachment).where(AuditEvidenceAttachment.item_id.in_(item_ids))
        ).all()

    for attachment in attachments:
        absolute_path = UPLOAD_ROOT.parent.parent / attachment.relative_path
        try:
            if absolute_path.exists():
                absolute_path.unlink()
        except OSError:
            pass
        db.delete(attachment)

    for item in items:
        db.delete(item)

    audit_upload_dir = UPLOAD_ROOT / audit_id
    if audit_upload_dir.exists():
        for path in sorted(audit_upload_dir.rglob("*"), reverse=True):
            try:
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            except OSError:
                pass
        try:
            audit_upload_dir.rmdir()
        except OSError:
            pass

    db.delete(engagement)
    db.commit()
    return True


def list_audit_items(db: Session, audit_id: str) -> list[AuditEngagementItem]:
    stmt = (
        select(AuditEngagementItem)
        .where(AuditEngagementItem.audit_id == audit_id)
        .order_by(AuditEngagementItem.display_order)
    )
    return db.scalars(stmt).all()


def list_audit_law_summaries(db: Session, audit_id: str) -> list[dict[str, int | str | None]]:
    parent_law = aliased(LawMaster)
    origin_scope = case(
        (
            func.bool_and(
                case((AuditEngagementItem.origin == "CORE", True), else_=False)
            ),
            "CORE",
        ),
        (
            func.bool_or(
                case(
                    (
                        and_(
                            AuditEngagementItem.origin.is_not(None),
                            AuditEngagementItem.origin != "CORE",
                        ),
                        True,
                    ),
                    else_=False,
                )
            )
            & func.bool_or(
                case((AuditEngagementItem.origin == "CORE", True), else_=False)
            ),
            "Mixed",
        ),
        (
            func.bool_or(
                case(
                    (
                        and_(
                            AuditEngagementItem.origin.is_not(None),
                            AuditEngagementItem.origin != "CORE",
                        ),
                        True,
                    ),
                    else_=False,
                )
            ),
            "Sub-sector",
        ),
        else_=None,
    )
    rows = db.execute(
        select(
            AuditEngagementItem.law_id,
            func.max(LawMaster.parent_law).label("parent_law_id"),
            func.max(parent_law.law_name).label("parent_law_name"),
            func.coalesce(AuditEngagementItem.law_name, "Law").label("law_name"),
            origin_scope.label("origin_scope"),
            func.max(AuditEngagementItem.regulator).label("regulator"),
            func.max(AuditEngagementItem.authority_level).label("authority_level"),
            func.max(AuditEngagementItem.document_type).label("document_type"),
            func.max(AuditEngagementItem.applicability_type).label("applicability_type"),
            func.count(AuditEngagementItem.item_id).label("total_items"),
            func.sum(
                case(
                    (AuditEngagementItem.status.in_(tuple(COMPLETED_STATUSES)), 1),
                    else_=0,
                )
            ).label("completed_items"),
        )
        .outerjoin(LawMaster, LawMaster.law_id == AuditEngagementItem.law_id)
        .outerjoin(parent_law, parent_law.law_id == LawMaster.parent_law)
        .where(AuditEngagementItem.audit_id == audit_id)
        .group_by(AuditEngagementItem.law_id, AuditEngagementItem.law_name)
        .order_by(
            func.coalesce(AuditEngagementItem.law_id, ""),
            func.coalesce(AuditEngagementItem.law_name, "Law"),
        )
    ).all()
    return [dict(row._mapping) for row in rows]


def list_audit_provision_summaries(
    db: Session,
    audit_id: str,
    law_id: str | None,
) -> list[dict[str, int | str | None]]:
    origin_scope = case(
        (
            func.bool_and(
                case((AuditEngagementItem.origin == "CORE", True), else_=False)
            ),
            "CORE",
        ),
        (
            func.bool_or(
                case(
                    (
                        and_(
                            AuditEngagementItem.origin.is_not(None),
                            AuditEngagementItem.origin != "CORE",
                        ),
                        True,
                    ),
                    else_=False,
                )
            )
            & func.bool_or(
                case((AuditEngagementItem.origin == "CORE", True), else_=False)
            ),
            "Mixed",
        ),
        (
            func.bool_or(
                case(
                    (
                        and_(
                            AuditEngagementItem.origin.is_not(None),
                            AuditEngagementItem.origin != "CORE",
                        ),
                        True,
                    ),
                    else_=False,
                )
            ),
            "Sub-sector",
        ),
        else_=None,
    )
    stmt = select(
        AuditEngagementItem.provision_id,
        func.coalesce(AuditEngagementItem.provision_name, "Provision").label("provision_name"),
        func.max(AuditEngagementItem.statutory_reference).label("statutory_reference"),
        origin_scope.label("origin_scope"),
        func.count(AuditEngagementItem.item_id).label("total_items"),
        func.sum(
            case(
                (AuditEngagementItem.status.in_(tuple(COMPLETED_STATUSES)), 1),
                else_=0,
            )
        ).label("completed_items"),
    ).where(AuditEngagementItem.audit_id == audit_id)
    if law_id:
        stmt = stmt.where(AuditEngagementItem.law_id == law_id)
    else:
        stmt = stmt.where(AuditEngagementItem.law_id.is_(None))
    rows = db.execute(
        stmt.group_by(AuditEngagementItem.provision_id, AuditEngagementItem.provision_name).order_by(
            func.coalesce(AuditEngagementItem.provision_id, ""),
            func.coalesce(AuditEngagementItem.provision_name, "Provision"),
        )
    ).all()
    return [dict(row._mapping) for row in rows]


def list_audit_items_for_provision(
    db: Session,
    audit_id: str,
    law_id: str | None,
    provision_id: str | None,
) -> list[AuditEngagementItem]:
    stmt = select(AuditEngagementItem).where(AuditEngagementItem.audit_id == audit_id)
    if law_id:
        stmt = stmt.where(AuditEngagementItem.law_id == law_id)
    else:
        stmt = stmt.where(AuditEngagementItem.law_id.is_(None))
    if provision_id:
        stmt = stmt.where(AuditEngagementItem.provision_id == provision_id)
    else:
        stmt = stmt.where(AuditEngagementItem.provision_id.is_(None))
    stmt = stmt.order_by(AuditEngagementItem.display_order)
    return db.scalars(stmt).all()


def list_attachments(db: Session, item_ids: list[str]) -> dict[str, list[AuditEvidenceAttachment]]:
    if not item_ids:
        return {}
    rows = db.scalars(
        select(AuditEvidenceAttachment)
        .where(AuditEvidenceAttachment.item_id.in_(item_ids))
        .order_by(AuditEvidenceAttachment.created_at.desc())
    ).all()
    result: dict[str, list[AuditEvidenceAttachment]] = defaultdict(list)
    for row in rows:
        result[row.item_id].append(row)
    return result


def update_audit_item(
    db: Session,
    firm_id: str,
    audit_id: str,
    item_id: str,
    payload: AuditItemUpdate,
) -> AuditEngagementItem | None:
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        return None
    item = get_audit_item(db, audit_id, item_id)
    if not item:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    _recalculate_progress(db, engagement)
    return item


def add_attachment(
    db: Session,
    firm_id: str,
    audit_id: str,
    item_id: str,
    file_name: str,
    content_type: str | None,
    content: bytes,
) -> AuditEvidenceAttachment | None:
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        return None
    item = get_audit_item(db, audit_id, item_id)
    if not item:
        return None

    target_dir = UPLOAD_ROOT / audit_id / item_id
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file_name).name or "attachment.bin"
    stored_file_name = f"{uuid4().hex}_{safe_name}"
    target_path = target_dir / stored_file_name

    with target_path.open("wb") as handle:
        handle.write(content)

    attachment = AuditEvidenceAttachment(
        attachment_id=_new_id("ATC"),
        item_id=item_id,
        original_file_name=safe_name,
        stored_file_name=stored_file_name,
        content_type=content_type,
        file_size=target_path.stat().st_size,
        relative_path=str(target_path.relative_to(UPLOAD_ROOT.parent.parent)),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def get_attachment(
    db: Session,
    firm_id: str,
    audit_id: str,
    item_id: str,
    attachment_id: str,
) -> AuditEvidenceAttachment | None:
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        return None
    item = get_audit_item(db, audit_id, item_id)
    if not item:
        return None
    stmt = select(AuditEvidenceAttachment).where(
        AuditEvidenceAttachment.item_id == item_id,
        AuditEvidenceAttachment.attachment_id == attachment_id,
    )
    return db.scalar(stmt)
