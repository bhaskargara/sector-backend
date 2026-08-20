from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.audit_repository import (
    UPLOAD_ROOT,
    add_attachment,
    create_audit,
    delete_audit,
    ensure_audit_metadata,
    get_attachment,
    get_audit,
    list_attachments,
    list_audit_items_for_provision,
    list_audit_items,
    list_audit_law_summaries,
    list_audit_provision_summaries,
    list_audits,
    update_audit,
    update_audit_item,
)
from app.schemas.audit import (
    AuditEngagementCreate,
    AuditEngagementDetail,
    AuditEngagementItemRead,
    AuditLawSummary,
    AuditEngagementRead,
    AuditEngagementUpdate,
    AuditEvidenceAttachmentRead,
    AuditItemUpdate,
    AuditProvisionSummary,
)

router = APIRouter(tags=["audit"])


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get("/firms/{firm_id}/audits", response_model=list[AuditEngagementRead])
def get_firm_audits(firm_id: str, db: Session = Depends(get_db)):
    return list_audits(db, firm_id)


@router.post(
    "/firms/{firm_id}/audits",
    response_model=AuditEngagementRead,
    status_code=status.HTTP_201_CREATED,
)
def post_firm_audit(
    firm_id: str,
    payload: AuditEngagementCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_audit(db, firm_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/firms/{firm_id}/audits/{audit_id}", response_model=AuditEngagementDetail)
def get_firm_audit(firm_id: str, audit_id: str, db: Session = Depends(get_db)):
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        raise not_found(f"Audit not found: {audit_id}")

    return AuditEngagementDetail(**engagement.__dict__, items=[])


@router.get(
    "/firms/{firm_id}/audits/{audit_id}/laws",
    response_model=list[AuditLawSummary],
)
def get_firm_audit_laws(firm_id: str, audit_id: str, db: Session = Depends(get_db)):
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        raise not_found(f"Audit not found: {audit_id}")
    ensure_audit_metadata(db, audit_id)
    return [AuditLawSummary(**law) for law in list_audit_law_summaries(db, audit_id)]


@router.get(
    "/firms/{firm_id}/audits/{audit_id}/laws/{law_id}/provisions",
    response_model=list[AuditProvisionSummary],
)
def get_firm_audit_provisions(
    firm_id: str,
    audit_id: str,
    law_id: str,
    db: Session = Depends(get_db),
):
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        raise not_found(f"Audit not found: {audit_id}")
    effective_law_id = None if law_id == "__none__" else law_id
    return [
        AuditProvisionSummary(**provision)
        for provision in list_audit_provision_summaries(db, audit_id, effective_law_id)
    ]


@router.get(
    "/firms/{firm_id}/audits/{audit_id}/laws/{law_id}/provisions/{provision_id}/items",
    response_model=list[AuditEngagementItemRead],
)
def get_firm_audit_provision_items(
    firm_id: str,
    audit_id: str,
    law_id: str,
    provision_id: str,
    db: Session = Depends(get_db),
):
    engagement = get_audit(db, firm_id, audit_id)
    if not engagement:
        raise not_found(f"Audit not found: {audit_id}")

    effective_law_id = None if law_id == "__none__" else law_id
    effective_provision_id = None if provision_id == "__none__" else provision_id
    items = list_audit_items_for_provision(db, audit_id, effective_law_id, effective_provision_id)
    attachment_map = list_attachments(db, [item.item_id for item in items])
    return [
        AuditEngagementItemRead(
            **item.__dict__,
            attachments=[
                AuditEvidenceAttachmentRead.model_validate(attachment)
                for attachment in attachment_map.get(item.item_id, [])
            ],
        )
        for item in items
    ]


@router.patch("/firms/{firm_id}/audits/{audit_id}", response_model=AuditEngagementRead)
def patch_firm_audit(
    firm_id: str,
    audit_id: str,
    payload: AuditEngagementUpdate,
    db: Session = Depends(get_db),
):
    engagement = update_audit(db, firm_id, audit_id, payload)
    if not engagement:
        raise not_found(f"Audit not found: {audit_id}")
    return engagement


@router.delete("/firms/{firm_id}/audits/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_firm_audit(firm_id: str, audit_id: str, db: Session = Depends(get_db)):
    if not delete_audit(db, firm_id, audit_id):
        raise not_found(f"Audit not found: {audit_id}")
    return None


@router.patch(
    "/firms/{firm_id}/audits/{audit_id}/items/{item_id}",
    response_model=AuditEngagementItemRead,
)
def patch_firm_audit_item(
    firm_id: str,
    audit_id: str,
    item_id: str,
    payload: AuditItemUpdate,
    db: Session = Depends(get_db),
):
    item = update_audit_item(db, firm_id, audit_id, item_id, payload)
    if not item:
        raise not_found(f"Audit item not found: {item_id}")
    return AuditEngagementItemRead(
        **item.__dict__,
        attachments=[
            AuditEvidenceAttachmentRead.model_validate(attachment)
            for attachment in list_attachments(db, [item.item_id]).get(item.item_id, [])
        ],
    )


@router.post(
    "/firms/{firm_id}/audits/{audit_id}/items/{item_id}/attachments",
    response_model=AuditEvidenceAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_firm_audit_attachment(
    firm_id: str,
    audit_id: str,
    item_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    file_name = request.headers.get("X-Filename", "attachment.bin")
    content_type = request.headers.get("Content-Type")
    content = await request.body()
    attachment = add_attachment(db, firm_id, audit_id, item_id, file_name, content_type, content)
    if not attachment:
        raise not_found(f"Audit item not found: {item_id}")
    return attachment


@router.get("/firms/{firm_id}/audits/{audit_id}/items/{item_id}/attachments/{attachment_id}")
def download_firm_audit_attachment(
    firm_id: str,
    audit_id: str,
    item_id: str,
    attachment_id: str,
    db: Session = Depends(get_db),
):
    attachment = get_attachment(db, firm_id, audit_id, item_id, attachment_id)
    if not attachment:
        raise not_found(f"Attachment not found: {attachment_id}")

    absolute_path = Path(UPLOAD_ROOT.parent.parent / attachment.relative_path)
    if not absolute_path.exists():
        raise not_found(f"Attachment file missing: {attachment.original_file_name}")

    return FileResponse(
        absolute_path,
        filename=attachment.original_file_name,
        media_type=attachment.content_type or "application/octet-stream",
    )
