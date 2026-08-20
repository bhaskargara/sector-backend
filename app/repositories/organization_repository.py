from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.audit import AuditEngagement
from app.models.organization import (
    ClientMaster,
    EnterpriseMaster,
    EnterpriseUser,
    FirmEnterpriseEngagement,
    FirmMaster,
    FirmUser,
    PlatformAdminUser,
)
from app.models.regulatory import SectorMaster, SubSectorMaster
from app.schemas.organization import (
    ClientCreate,
    ClientUpdate,
    EnterpriseCreate,
    EnterpriseUpdate,
    EnterpriseUserCreate,
    EnterpriseUserUpdate,
    FirmCreate,
    FirmEnterpriseEngagementCreate,
    FirmEnterpriseEngagementUpdate,
    FirmUpdate,
    FirmUserCreate,
    FirmUserUpdate,
    PlatformAdminUserCreate,
    PlatformAdminUserUpdate,
)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def _normalize_email(email: str | None) -> str | None:
    if email is None:
        return None
    normalized = email.strip().lower()
    return normalized or None


def _email_exists(
    db: Session,
    email: str | None,
    *,
    exclude_firm_user_id: str | None = None,
    exclude_enterprise_user_id: str | None = None,
    exclude_platform_admin_id: str | None = None,
) -> bool:
    normalized_email = _normalize_email(email)
    if not normalized_email:
        return False

    firm_user_stmt = select(FirmUser.user_id).where(FirmUser.email == normalized_email)
    if exclude_firm_user_id:
        firm_user_stmt = firm_user_stmt.where(FirmUser.user_id != exclude_firm_user_id)
    if db.scalar(firm_user_stmt.limit(1)):
        return True

    enterprise_user_stmt = select(EnterpriseUser.user_id).where(
        EnterpriseUser.email == normalized_email
    )
    if exclude_enterprise_user_id:
        enterprise_user_stmt = enterprise_user_stmt.where(
            EnterpriseUser.user_id != exclude_enterprise_user_id
        )
    if db.scalar(enterprise_user_stmt.limit(1)):
        return True

    platform_user_stmt = select(PlatformAdminUser.user_id).where(
        PlatformAdminUser.email == normalized_email
    )
    if exclude_platform_admin_id:
        platform_user_stmt = platform_user_stmt.where(
            PlatformAdminUser.user_id != exclude_platform_admin_id
        )
    return db.scalar(platform_user_stmt.limit(1)) is not None


def ensure_demo_firm(db: Session) -> FirmMaster:
    firm = db.get(FirmMaster, "FIRM-PCS")
    should_commit = False

    if not firm:
        firm = FirmMaster(
            firm_id="FIRM-PCS",
            firm_name="PCS",
            owner_name="PCS Owner",
            contact_email="owner@pcs.example",
            status="Active",
        )
        db.add(firm)
        should_commit = True

    demo_users = [
        FirmUser(
            user_id="USR-PCS-OWNER",
            firm_id="FIRM-PCS",
            full_name="PCS Owner",
            email="owner@pcs.example",
            role="Firm Owner",
            status="Active",
        ),
        FirmUser(
            user_id="USR-PCS-EMPLOYEE",
            firm_id="FIRM-PCS",
            full_name="PCS Compliance Executive",
            email="compliance@pcs.example",
            role="Firm Employee",
            status="Active",
        ),
    ]
    for user in demo_users:
        if not db.get(FirmUser, user.user_id):
            db.add(user)
            should_commit = True

    if should_commit:
        db.commit()
    db.refresh(firm)
    return firm


def ensure_demo_platform_admins(db: Session) -> None:
    demo_users = [
        PlatformAdminUser(
            user_id="ADM-PLATFORM-OWNER",
            full_name="Platform Admin",
            email="admin@sector.rocprompt.in",
            role="Platform Owner",
            status="Active",
        ),
        PlatformAdminUser(
            user_id="ADM-PLATFORM-EMPLOYEE",
            full_name="Platform Compliance Employee",
            email="platform.employee@sector.rocprompt.in",
            role="Platform Employee",
            status="Active",
        ),
    ]
    should_commit = False
    for user in demo_users:
        if not db.get(PlatformAdminUser, user.user_id):
            db.add(user)
            should_commit = True
    if should_commit:
        db.commit()


def list_platform_admin_users(db: Session) -> list[PlatformAdminUser]:
    return db.scalars(select(PlatformAdminUser).order_by(PlatformAdminUser.full_name)).all()


def get_platform_admin_user(db: Session, user_id: str) -> PlatformAdminUser | None:
    return db.get(PlatformAdminUser, user_id)


def find_platform_admin_user_by_email(db: Session, email: str) -> PlatformAdminUser | None:
    stmt = select(PlatformAdminUser).where(
        PlatformAdminUser.email == _normalize_email(email),
        PlatformAdminUser.status == "Active",
    )
    return db.scalar(stmt)


def create_platform_admin_user(
    db: Session,
    payload: PlatformAdminUserCreate,
) -> PlatformAdminUser:
    payload_data = payload.model_dump()
    payload_data["email"] = _normalize_email(payload_data["email"])
    payload_data["password_hash"] = hash_password(payload_data.pop("password"))
    if _email_exists(db, payload_data["email"]):
        raise ValueError(f"Email already exists: {payload_data['email']}")

    user = PlatformAdminUser(user_id=_new_id("ADM"), **payload_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_platform_admin_user(
    db: Session,
    user_id: str,
    payload: PlatformAdminUserUpdate,
) -> PlatformAdminUser | None:
    user = get_platform_admin_user(db, user_id)
    if not user:
        return None
    values = payload.model_dump(exclude_unset=True)
    if "email" in values:
        values["email"] = _normalize_email(values["email"])
        if _email_exists(
            db,
            values["email"],
            exclude_platform_admin_id=user_id,
        ):
            raise ValueError(f"Email already exists: {values['email']}")
    if "password" in values:
        values["password_hash"] = hash_password(values.pop("password"))
    for field, value in values.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_platform_admin_user(db: Session, user_id: str) -> bool:
    user = get_platform_admin_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def list_firms(db: Session) -> list[FirmMaster]:
    return db.scalars(select(FirmMaster).order_by(FirmMaster.firm_name)).all()


def get_firm(db: Session, firm_id: str) -> FirmMaster | None:
    return db.get(FirmMaster, firm_id)


def create_firm(db: Session, payload: FirmCreate) -> FirmMaster:
    payload_data = payload.model_dump(exclude={"initial_user"})
    initial_user = payload.initial_user
    if initial_user:
        initial_user.email = _normalize_email(initial_user.email)
        if _email_exists(db, initial_user.email):
            raise ValueError(f"Email already exists: {initial_user.email}")

    firm = FirmMaster(firm_id=_new_id("FIRM"), **payload_data)
    db.add(firm)
    db.flush()

    if initial_user:
        user = FirmUser(
            user_id=_new_id("USR"),
            firm_id=firm.firm_id,
            password_hash=hash_password(initial_user.password),
            **initial_user.model_dump(exclude={"password"}),
        )
        db.add(user)

    db.commit()
    db.refresh(firm)
    return firm


def update_firm(db: Session, firm_id: str, payload: FirmUpdate) -> FirmMaster | None:
    firm = get_firm(db, firm_id)
    if not firm:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(firm, field, value)
    db.commit()
    db.refresh(firm)
    return firm


def delete_firm(db: Session, firm_id: str) -> bool:
    firm = get_firm(db, firm_id)
    if not firm:
        return False
    db.delete(firm)
    db.commit()
    return True


def list_firm_users(db: Session, firm_id: str) -> list[FirmUser]:
    stmt = select(FirmUser).where(FirmUser.firm_id == firm_id).order_by(FirmUser.full_name)
    return db.scalars(stmt).all()


def get_firm_user(db: Session, firm_id: str, user_id: str) -> FirmUser | None:
    stmt = select(FirmUser).where(
        FirmUser.firm_id == firm_id,
        FirmUser.user_id == user_id,
    )
    return db.scalar(stmt)


def create_firm_user(db: Session, firm_id: str, payload: FirmUserCreate) -> FirmUser:
    firm = db.get(FirmMaster, firm_id)
    if not firm:
        raise ValueError(f"Unknown firm_id: {firm_id}")

    payload_data = payload.model_dump()
    payload_data["email"] = _normalize_email(payload_data["email"])
    payload_data["password_hash"] = hash_password(payload_data.pop("password"))
    if _email_exists(db, payload_data["email"]):
        raise ValueError(f"Email already exists: {payload_data['email']}")

    user = FirmUser(user_id=_new_id("USR"), firm_id=firm_id, **payload_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_firm_user(
    db: Session,
    firm_id: str,
    user_id: str,
    payload: FirmUserUpdate,
) -> FirmUser | None:
    user = get_firm_user(db, firm_id, user_id)
    if not user:
        return None
    values = payload.model_dump(exclude_unset=True)
    if "email" in values:
        values["email"] = _normalize_email(values["email"])
        if _email_exists(db, values["email"], exclude_firm_user_id=user_id):
            raise ValueError(f"Email already exists: {values['email']}")
    if "password" in values:
        values["password_hash"] = hash_password(values.pop("password"))
    for field, value in values.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_firm_user(db: Session, firm_id: str, user_id: str) -> bool:
    user = get_firm_user(db, firm_id, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def list_enterprises(db: Session) -> list[EnterpriseMaster]:
    return db.scalars(select(EnterpriseMaster).order_by(EnterpriseMaster.enterprise_name)).all()


def get_enterprise(db: Session, enterprise_id: str) -> EnterpriseMaster | None:
    return db.get(EnterpriseMaster, enterprise_id)


def create_enterprise(db: Session, payload: EnterpriseCreate) -> EnterpriseMaster:
    payload_data = payload.model_dump(exclude={"initial_user"})
    initial_user = payload.initial_user
    if initial_user:
        initial_user.email = _normalize_email(initial_user.email)
        if _email_exists(db, initial_user.email):
            raise ValueError(f"Email already exists: {initial_user.email}")

    enterprise = EnterpriseMaster(
        enterprise_id=_new_id("ENT"),
        **payload_data,
    )
    db.add(enterprise)
    db.flush()

    if initial_user:
        user = EnterpriseUser(
            user_id=_new_id("ENU"),
            enterprise_id=enterprise.enterprise_id,
            password_hash=hash_password(initial_user.password),
            **initial_user.model_dump(exclude={"password"}),
        )
        db.add(user)

    db.commit()
    db.refresh(enterprise)
    return enterprise


def update_enterprise(
    db: Session,
    enterprise_id: str,
    payload: EnterpriseUpdate,
) -> EnterpriseMaster | None:
    enterprise = get_enterprise(db, enterprise_id)
    if not enterprise:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(enterprise, field, value)
    db.commit()
    db.refresh(enterprise)
    return enterprise


def delete_enterprise(db: Session, enterprise_id: str) -> bool:
    enterprise = get_enterprise(db, enterprise_id)
    if not enterprise:
        return False
    db.delete(enterprise)
    db.commit()
    return True


def list_enterprise_users(db: Session, enterprise_id: str) -> list[EnterpriseUser]:
    stmt = (
        select(EnterpriseUser)
        .where(EnterpriseUser.enterprise_id == enterprise_id)
        .order_by(EnterpriseUser.full_name)
    )
    return db.scalars(stmt).all()


def get_enterprise_user(db: Session, enterprise_id: str, user_id: str) -> EnterpriseUser | None:
    stmt = select(EnterpriseUser).where(
        EnterpriseUser.enterprise_id == enterprise_id,
        EnterpriseUser.user_id == user_id,
    )
    return db.scalar(stmt)


def find_enterprise_user_by_email(db: Session, email: str) -> EnterpriseUser | None:
    normalized_email = _normalize_email(email)
    if not normalized_email:
        return None
    stmt = select(EnterpriseUser).where(
        EnterpriseUser.email == normalized_email,
        EnterpriseUser.status == "Active",
    )
    return db.scalar(stmt)


def create_enterprise_user(
    db: Session,
    enterprise_id: str,
    payload: EnterpriseUserCreate,
) -> EnterpriseUser:
    enterprise = db.get(EnterpriseMaster, enterprise_id)
    if not enterprise:
        raise ValueError(f"Unknown enterprise_id: {enterprise_id}")

    payload_data = payload.model_dump()
    payload_data["email"] = _normalize_email(payload_data["email"])
    payload_data["password_hash"] = hash_password(payload_data.pop("password"))
    if _email_exists(db, payload_data["email"]):
        raise ValueError(f"Email already exists: {payload_data['email']}")

    user = EnterpriseUser(
        user_id=_new_id("ENU"),
        enterprise_id=enterprise_id,
        **payload_data,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_enterprise_user(
    db: Session,
    enterprise_id: str,
    user_id: str,
    payload: EnterpriseUserUpdate,
) -> EnterpriseUser | None:
    user = get_enterprise_user(db, enterprise_id, user_id)
    if not user:
        return None
    values = payload.model_dump(exclude_unset=True)
    if "email" in values:
        values["email"] = _normalize_email(values["email"])
        if _email_exists(
            db,
            values["email"],
            exclude_enterprise_user_id=user_id,
        ):
            raise ValueError(f"Email already exists: {values['email']}")
    if "password" in values:
        values["password_hash"] = hash_password(values.pop("password"))
    for field, value in values.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_enterprise_user(db: Session, enterprise_id: str, user_id: str) -> bool:
    user = get_enterprise_user(db, enterprise_id, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def list_engagements(
    db: Session,
    *,
    firm_id: str | None = None,
    enterprise_id: str | None = None,
) -> list[FirmEnterpriseEngagement]:
    stmt = select(FirmEnterpriseEngagement).order_by(FirmEnterpriseEngagement.created_at.desc())
    if firm_id:
        stmt = stmt.where(FirmEnterpriseEngagement.firm_id == firm_id)
    if enterprise_id:
        stmt = stmt.where(FirmEnterpriseEngagement.enterprise_id == enterprise_id)
    return db.scalars(stmt).all()


def get_engagement(db: Session, engagement_id: str) -> FirmEnterpriseEngagement | None:
    return db.get(FirmEnterpriseEngagement, engagement_id)


def create_engagement(
    db: Session,
    payload: FirmEnterpriseEngagementCreate,
) -> FirmEnterpriseEngagement:
    firm = db.get(FirmMaster, payload.firm_id)
    if not firm:
        raise ValueError(f"Unknown firm_id: {payload.firm_id}")

    enterprise = db.get(EnterpriseMaster, payload.enterprise_id)
    if not enterprise:
        raise ValueError(f"Unknown enterprise_id: {payload.enterprise_id}")

    existing = db.scalar(
        select(FirmEnterpriseEngagement).where(
            FirmEnterpriseEngagement.firm_id == payload.firm_id,
            FirmEnterpriseEngagement.enterprise_id == payload.enterprise_id,
        )
    )
    if existing:
        raise ValueError(
            f"Engagement already exists for firm {payload.firm_id} and enterprise {payload.enterprise_id}"
        )

    engagement = FirmEnterpriseEngagement(
        engagement_id=_new_id("ENG"),
        **payload.model_dump(),
    )
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return engagement


def update_engagement(
    db: Session,
    engagement_id: str,
    payload: FirmEnterpriseEngagementUpdate,
) -> FirmEnterpriseEngagement | None:
    engagement = get_engagement(db, engagement_id)
    if not engagement:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(engagement, field, value)
    db.commit()
    db.refresh(engagement)
    return engagement


def delete_engagement(db: Session, engagement_id: str) -> bool:
    engagement = get_engagement(db, engagement_id)
    if not engagement:
        return False
    db.delete(engagement)
    db.commit()
    return True


def list_clients(db: Session, firm_id: str) -> list[ClientMaster]:
    stmt = (
        select(ClientMaster)
        .where(ClientMaster.firm_id == firm_id)
        .order_by(ClientMaster.created_at.desc())
    )
    return db.scalars(stmt).all()


def get_client(db: Session, firm_id: str, client_id: str) -> ClientMaster | None:
    stmt = select(ClientMaster).where(
        ClientMaster.firm_id == firm_id,
        ClientMaster.client_id == client_id,
    )
    return db.scalar(stmt)


def _validate_client_scope(
    db: Session,
    sector_id: str,
    sub_sector_id: str,
) -> None:
    sector = db.get(SectorMaster, sector_id)
    if not sector:
        raise ValueError(f"Unknown sector_id: {sector_id}")

    sub_sector = db.get(SubSectorMaster, sub_sector_id)
    if not sub_sector or sub_sector.sector_id != sector_id:
        raise ValueError(f"Unknown sub_sector_id for sector {sector_id}: {sub_sector_id}")


def create_client(db: Session, firm_id: str, payload: ClientCreate) -> ClientMaster:
    firm = db.get(FirmMaster, firm_id)
    if not firm:
        raise ValueError(f"Unknown firm_id: {firm_id}")

    _validate_client_scope(db, payload.sector_id, payload.sub_sector_id)
    client = ClientMaster(
        client_id=_new_id("CLT"),
        firm_id=firm_id,
        **payload.model_dump(),
    )
    db.add(client)
    db.flush()

    enterprise = EnterpriseMaster(
        enterprise_id=_new_id("ENT"),
        enterprise_name=client.client_name,
        legal_name=client.legal_name,
        contact_email=client.contact_email,
        phone=client.phone,
        city=client.city,
        status=client.status if client.status else "Active",
        remarks=client.remarks,
    )
    db.add(enterprise)
    db.flush()

    engagement = FirmEnterpriseEngagement(
        engagement_id=_new_id("ENG"),
        firm_id=firm_id,
        enterprise_id=enterprise.enterprise_id,
        status="Active",
        invited_by_side="Firm",
        invited_by_user_id=None,
        engagement_name=client.client_name,
        remarks="Auto-created from firm client onboarding",
    )
    db.add(engagement)
    client.enterprise_id = enterprise.enterprise_id
    db.commit()
    db.refresh(client)
    return client


def update_client(
    db: Session,
    firm_id: str,
    client_id: str,
    payload: ClientUpdate,
) -> ClientMaster | None:
    client = get_client(db, firm_id, client_id)
    if not client:
        return None

    values = payload.model_dump(exclude_unset=True)
    next_sector_id = values.get("sector_id", client.sector_id)
    next_sub_sector_id = values.get("sub_sector_id", client.sub_sector_id)
    if "sector_id" in values or "sub_sector_id" in values:
        audit_exists = db.scalar(
            select(AuditEngagement.audit_id).where(AuditEngagement.client_id == client.client_id).limit(1)
        )
        scope_changed = (
            next_sector_id != client.sector_id or next_sub_sector_id != client.sub_sector_id
        )
        if audit_exists and scope_changed:
            raise ValueError(
                "Sector and sub-sector cannot be changed after an audit has been created for this client"
            )
    if "sector_id" in values or "sub_sector_id" in values:
        _validate_client_scope(db, next_sector_id, next_sub_sector_id)

    previous_client_name = client.client_name
    for field, value in values.items():
        setattr(client, field, value)

    if client.enterprise_id:
        enterprise = db.get(EnterpriseMaster, client.enterprise_id)
        if enterprise:
            enterprise.enterprise_name = client.client_name
            enterprise.legal_name = client.legal_name
            enterprise.contact_email = client.contact_email
            enterprise.phone = client.phone
            enterprise.city = client.city
            enterprise.status = client.status
            enterprise.remarks = client.remarks

    if client.client_name != previous_client_name:
        audit_rows = db.scalars(
            select(AuditEngagement).where(
                AuditEngagement.firm_id == firm_id,
                AuditEngagement.client_id == client.client_id,
            )
        ).all()
        for audit in audit_rows:
            audit.client_name = client.client_name

        if client.enterprise_id:
            engagement_rows = db.scalars(
                select(FirmEnterpriseEngagement).where(
                    FirmEnterpriseEngagement.firm_id == firm_id,
                    FirmEnterpriseEngagement.enterprise_id == client.enterprise_id,
                )
            ).all()
            for engagement in engagement_rows:
                if engagement.engagement_name == previous_client_name:
                    engagement.engagement_name = client.client_name
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, firm_id: str, client_id: str) -> bool:
    client = get_client(db, firm_id, client_id)
    if not client:
        return False
    db.delete(client)
    db.commit()
    return True


def serialize_client(client: ClientMaster) -> dict[str, str | None]:
    return {
        "client_id": client.client_id,
        "firm_id": client.firm_id,
        "client_name": client.client_name,
        "legal_name": client.legal_name,
        "contact_email": client.contact_email,
        "phone": client.phone,
        "city": client.city,
        "sector_id": client.sector_id,
        "sub_sector_id": client.sub_sector_id,
        "status": client.status,
        "remarks": client.remarks,
        "sector_name": client.sector.sector_name if client.sector else None,
        "sub_sector_name": client.sub_sector.sub_sector_name if client.sub_sector else None,
        "enterprise_id": client.enterprise_id,
    }


def serialize_engagement(
    engagement: FirmEnterpriseEngagement,
) -> dict[str, str | date | datetime | None]:
    return {
        "engagement_id": engagement.engagement_id,
        "firm_id": engagement.firm_id,
        "enterprise_id": engagement.enterprise_id,
        "status": engagement.status,
        "invited_by_side": engagement.invited_by_side,
        "invited_by_user_id": engagement.invited_by_user_id,
        "engagement_name": engagement.engagement_name,
        "start_date": engagement.start_date,
        "end_date": engagement.end_date,
        "remarks": engagement.remarks,
        "created_at": engagement.created_at,
        "updated_at": engagement.updated_at,
        "firm_name": engagement.firm.firm_name if engagement.firm else None,
        "enterprise_name": engagement.enterprise.enterprise_name if engagement.enterprise else None,
    }
