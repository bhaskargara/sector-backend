"""Shared cleanup for audit snapshots and their uploaded evidence."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditEngagement, AuditEngagementItem, AuditEvidenceAttachment


UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "audit_evidence"


def delete_audit_snapshot(db: Session, engagement: AuditEngagement) -> None:
    """Delete one audit and every dependent database and uploaded-file record."""
    items = db.scalars(
        select(AuditEngagementItem).where(
            AuditEngagementItem.audit_id == engagement.audit_id
        )
    ).all()
    item_ids = [item.item_id for item in items]

    attachments = []
    if item_ids:
        attachments = db.scalars(
            select(AuditEvidenceAttachment).where(
                AuditEvidenceAttachment.item_id.in_(item_ids)
            )
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
    db.flush()

    audit_upload_dir = UPLOAD_ROOT / engagement.audit_id
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
