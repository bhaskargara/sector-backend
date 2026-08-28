from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditEngagement, AuditEngagementItem, AuditEvidenceAttachment
from app.models.organization import ClientMaster, FirmEnterpriseEngagement, FirmMaster
from app.repositories.regulatory_runtime import compose_control_rows, get_scope
from app.schemas.audit import AuditEngagementCreate, AuditEngagementUpdate, AuditItemUpdate

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "audit_evidence"
COMPLETED_STATUSES = {"Complied", "Not Applicable"}


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def _serialize_engagement(engagement: AuditEngagement) -> AuditEngagement:
    return engagement


def ensure_audit_metadata(db: Session, audit_id: str) -> None:
    # New audit snapshots are complete at creation time; no legacy enrichment.
    return None


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

    scope = get_scope(db, client.dataset_key, client.sector_id, client.sub_sector_id)
    if not scope:
        raise ValueError("This client does not have a valid regulatory dataset scope")
    rows = compose_control_rows(db, scope)

    if not rows:
        raise ValueError(
            "No regulatory master data was found for this client scope"
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
        dataset_key=client.dataset_key,
        sector_id=client.sector_id,
        sub_sector_id=client.sub_sector_id,
        client_name=client.client_name,
        sector_name=scope.sector_name,
        sub_sector_name=scope.sub_sector_name,
        remarks=payload.remarks,
    )
    db.add(engagement)
    db.commit()
    db.refresh(engagement)

    items: list[AuditEngagementItem] = []
    for index, row in enumerate(rows, start=1):
        items.append(
            AuditEngagementItem(
                item_id=_new_id("AIT"),
                audit_id=engagement.audit_id,
                law_id=row["law_id"], parent_law_id=row["parent_law_id"], parent_law_name=row["parent_law_name"], law_name=row["law_name"],
                regulator=row["regulator"], authority_level=row["authority_level"], document_type=row["document_type"],
                applicability_type=row["applicability_type"], applicability_trigger=row["applicability_trigger"],
                provision_id=row["provision_id"], provision_name=row["provision_name"], statutory_reference=row["statutory_reference"],
                compliance_id=row["compliance_id"], compliance_requirement=row["compliance_requirement"], compliance_objective=row["compliance_objective"], compliance_frequency=row["compliance_frequency"],
                audit_procedure_id=row["audit_procedure_id"], audit_procedure=row["audit_procedure"], audit_method=row["audit_method"], audit_frequency=row["audit_frequency"],
                evidence_template=row["evidence_template"], evidence_type=row["evidence_type"], evidence_mandatory=row["evidence_mandatory"], observation_template=row["observation_template"],
                priority=row["priority"], risk_level=row["risk_level"], origin=row["origin"],
                source_scope=row["source_scope"], applicability_scope=row["applicability_scope"], dataset_key=row["dataset_key"],
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
    applicability_scope = case(
        (func.count(func.distinct(AuditEngagementItem.applicability_scope)) > 1, "Mixed"),
        else_=func.max(AuditEngagementItem.applicability_scope),
    ).label("applicability_scope")
    rows = db.execute(
        select(
            AuditEngagementItem.law_id,
            func.max(AuditEngagementItem.parent_law_id).label("parent_law_id"),
            func.max(AuditEngagementItem.parent_law_name).label("parent_law_name"),
            func.coalesce(AuditEngagementItem.law_name, "Law").label("law_name"),
            func.max(AuditEngagementItem.source_scope).label("origin_scope"),
            applicability_scope,
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
    stmt = select(
        AuditEngagementItem.provision_id,
        func.coalesce(AuditEngagementItem.provision_name, "Provision").label("provision_name"),
        func.max(AuditEngagementItem.statutory_reference).label("statutory_reference"),
        func.max(AuditEngagementItem.source_scope).label("origin_scope"),
        case(
            (func.count(func.distinct(AuditEngagementItem.applicability_scope)) > 1, "Mixed"),
            else_=func.max(AuditEngagementItem.applicability_scope),
        ).label("applicability_scope"),
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
