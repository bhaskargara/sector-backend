from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password
from app.models.organization import EnterpriseMaster, EnterpriseUser, FirmMaster, FirmUser
from app.repositories.organization_repository import (
    find_enterprise_user_by_email,
    find_platform_admin_user_by_email,
)
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _invalid_login() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid login credentials",
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if payload.role == "platform_admin":
        admin_user = find_platform_admin_user_by_email(db, payload.email)
        if not admin_user or not verify_password(payload.password, admin_user.password_hash):
            raise _invalid_login()
        return LoginResponse(
            access_token=f"dev-platform-admin-token-{admin_user.user_id}",
            role="platform_admin",
            display_name=admin_user.full_name,
            email=admin_user.email,
            landing_route="/admin/dashboard",
        )

    if payload.role == "enterprise_user":
        stmt = (
            select(EnterpriseUser, EnterpriseMaster)
            .join(
                EnterpriseMaster,
                EnterpriseMaster.enterprise_id == EnterpriseUser.enterprise_id,
            )
            .where(
                EnterpriseUser.email == payload.email.lower(),
                EnterpriseUser.status == "Active",
            )
        )
        result = db.execute(stmt).first()
        if not result:
            result_user = find_enterprise_user_by_email(db, payload.email)
            if not result_user:
                raise _invalid_login()
            enterprise = db.get(EnterpriseMaster, result_user.enterprise_id)
            if not enterprise:
                raise _invalid_login()
            user = result_user
        else:
            user, enterprise = result

        if not verify_password(payload.password, user.password_hash):
            raise _invalid_login()

        enterprise_code = (payload.enterprise_code or "").strip().lower()
        if enterprise_code and enterprise_code not in {
            enterprise.enterprise_id.lower(),
            enterprise.enterprise_name.lower(),
        }:
            raise _invalid_login()

        return LoginResponse(
            access_token=f"dev-enterprise-user-token-{user.user_id}",
            role="enterprise_user",
            display_name=user.full_name,
            email=user.email,
            enterprise_id=enterprise.enterprise_id,
            enterprise_name=enterprise.enterprise_name,
            landing_route="/enterprise/dashboard",
        )

    stmt = (
        select(FirmUser, FirmMaster)
        .join(FirmMaster, FirmMaster.firm_id == FirmUser.firm_id)
        .where(
            FirmUser.email == payload.email.lower().strip(),
            FirmUser.status == "Active",
        )
    )
    result = db.execute(stmt).first()
    if not result:
        raise _invalid_login()

    user, firm = result
    if not verify_password(payload.password, user.password_hash):
        raise _invalid_login()

    firm_code = (payload.firm_code or "").strip().lower()
    if firm_code and firm_code not in {firm.firm_id.lower(), firm.firm_name.lower()}:
        raise _invalid_login()

    return LoginResponse(
        access_token=f"dev-firm-user-token-{user.user_id}",
        role="firm_user",
        display_name=user.full_name,
        email=user.email,
        firm_id=firm.firm_id,
        firm_name=firm.firm_name,
        landing_route="/firm/dashboard",
    )
