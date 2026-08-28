from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.organization_repository import (
    create_client,
    create_enterprise,
    create_enterprise_user,
    create_engagement,
    create_firm,
    create_firm_user,
    create_platform_admin_user,
    delete_client,
    delete_enterprise,
    delete_enterprise_user,
    delete_engagement,
    delete_firm,
    delete_firm_user,
    delete_platform_admin_user,
    get_client,
    get_enterprise,
    get_enterprise_user,
    get_engagement,
    get_firm,
    get_firm_user,
    get_platform_admin_user,
    list_clients,
    list_enterprise_users,
    list_enterprises,
    list_engagements,
    list_firm_users,
    list_firms,
    list_platform_admin_users,
    serialize_client,
    serialize_engagement,
    update_enterprise,
    update_enterprise_user,
    update_engagement,
    update_client,
    update_firm,
    update_firm_user,
    update_platform_admin_user,
)
from app.schemas.organization import (
    ClientCreate,
    ClientRead,
    ClientUpdate,
    EnterpriseCreate,
    EnterpriseRead,
    EnterpriseUpdate,
    EnterpriseUserCreate,
    EnterpriseUserRead,
    EnterpriseUserUpdate,
    FirmCreate,
    FirmEnterpriseEngagementCreate,
    FirmEnterpriseEngagementRead,
    FirmEnterpriseEngagementUpdate,
    FirmRead,
    FirmUpdate,
    FirmUserCreate,
    FirmUserRead,
    FirmUserUpdate,
    PlatformAdminUserCreate,
    PlatformAdminUserRead,
    PlatformAdminUserUpdate,
)

router = APIRouter(tags=["organization"])


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get("/platform-admin-users", response_model=list[PlatformAdminUserRead])
def get_platform_admin_users(db: Session = Depends(get_db)):
    return list_platform_admin_users(db)


@router.post(
    "/platform-admin-users",
    response_model=PlatformAdminUserRead,
    status_code=status.HTTP_201_CREATED,
)
def post_platform_admin_user(
    payload: PlatformAdminUserCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_platform_admin_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/platform-admin-users/{user_id}", response_model=PlatformAdminUserRead)
def get_platform_admin_user_by_id(user_id: str, db: Session = Depends(get_db)):
    user = get_platform_admin_user(db, user_id)
    if not user:
        raise not_found(f"Platform admin user not found: {user_id}")
    return user


@router.patch("/platform-admin-users/{user_id}", response_model=PlatformAdminUserRead)
def patch_platform_admin_user(
    user_id: str,
    payload: PlatformAdminUserUpdate,
    db: Session = Depends(get_db),
):
    try:
        user = update_platform_admin_user(db, user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not user:
        raise not_found(f"Platform admin user not found: {user_id}")
    return user


@router.delete("/platform-admin-users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_platform_admin_user(user_id: str, db: Session = Depends(get_db)):
    if not delete_platform_admin_user(db, user_id):
        raise not_found(f"Platform admin user not found: {user_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/firms", response_model=list[FirmRead])
def get_firms(db: Session = Depends(get_db)):
    return list_firms(db)


@router.post("/firms", response_model=FirmRead, status_code=status.HTTP_201_CREATED)
def post_firm(payload: FirmCreate, db: Session = Depends(get_db)):
    try:
        return create_firm(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/firms/{firm_id}", response_model=FirmRead)
def get_firm_by_id(firm_id: str, db: Session = Depends(get_db)):
    firm = get_firm(db, firm_id)
    if not firm:
        raise not_found(f"Firm not found: {firm_id}")
    return firm


@router.patch("/firms/{firm_id}", response_model=FirmRead)
def patch_firm(firm_id: str, payload: FirmUpdate, db: Session = Depends(get_db)):
    firm = update_firm(db, firm_id, payload)
    if not firm:
        raise not_found(f"Firm not found: {firm_id}")
    return firm


@router.delete("/firms/{firm_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_firm(firm_id: str, db: Session = Depends(get_db)):
    if not delete_firm(db, firm_id):
        raise not_found(f"Firm not found: {firm_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/enterprises", response_model=list[EnterpriseRead])
def get_enterprises(db: Session = Depends(get_db)):
    return list_enterprises(db)


@router.post("/enterprises", response_model=EnterpriseRead, status_code=status.HTTP_201_CREATED)
def post_enterprise(payload: EnterpriseCreate, db: Session = Depends(get_db)):
    try:
        return create_enterprise(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/enterprises/{enterprise_id}", response_model=EnterpriseRead)
def get_enterprise_by_id(enterprise_id: str, db: Session = Depends(get_db)):
    enterprise = get_enterprise(db, enterprise_id)
    if not enterprise:
        raise not_found(f"Enterprise not found: {enterprise_id}")
    return enterprise


@router.patch("/enterprises/{enterprise_id}", response_model=EnterpriseRead)
def patch_enterprise(
    enterprise_id: str,
    payload: EnterpriseUpdate,
    db: Session = Depends(get_db),
):
    enterprise = update_enterprise(db, enterprise_id, payload)
    if not enterprise:
        raise not_found(f"Enterprise not found: {enterprise_id}")
    return enterprise


@router.delete("/enterprises/{enterprise_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_enterprise(enterprise_id: str, db: Session = Depends(get_db)):
    if not delete_enterprise(db, enterprise_id):
        raise not_found(f"Enterprise not found: {enterprise_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/enterprises/{enterprise_id}/users", response_model=list[EnterpriseUserRead])
def get_enterprise_users(enterprise_id: str, db: Session = Depends(get_db)):
    return list_enterprise_users(db, enterprise_id)


@router.post(
    "/enterprises/{enterprise_id}/users",
    response_model=EnterpriseUserRead,
    status_code=status.HTTP_201_CREATED,
)
def post_enterprise_user(
    enterprise_id: str,
    payload: EnterpriseUserCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_enterprise_user(db, enterprise_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/enterprises/{enterprise_id}/users/{user_id}", response_model=EnterpriseUserRead)
def get_enterprise_user_by_id(
    enterprise_id: str,
    user_id: str,
    db: Session = Depends(get_db),
):
    user = get_enterprise_user(db, enterprise_id, user_id)
    if not user:
        raise not_found(f"Enterprise user not found: {user_id}")
    return user


@router.patch("/enterprises/{enterprise_id}/users/{user_id}", response_model=EnterpriseUserRead)
def patch_enterprise_user(
    enterprise_id: str,
    user_id: str,
    payload: EnterpriseUserUpdate,
    db: Session = Depends(get_db),
):
    try:
        user = update_enterprise_user(db, enterprise_id, user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not user:
        raise not_found(f"Enterprise user not found: {user_id}")
    return user


@router.delete("/enterprises/{enterprise_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_enterprise_user(
    enterprise_id: str,
    user_id: str,
    db: Session = Depends(get_db),
):
    if not delete_enterprise_user(db, enterprise_id, user_id):
        raise not_found(f"Enterprise user not found: {user_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/engagements", response_model=list[FirmEnterpriseEngagementRead])
def get_all_engagements(
    firm_id: str | None = None,
    enterprise_id: str | None = None,
    db: Session = Depends(get_db),
):
    return [
        serialize_engagement(engagement)
        for engagement in list_engagements(db, firm_id=firm_id, enterprise_id=enterprise_id)
    ]


@router.post(
    "/engagements",
    response_model=FirmEnterpriseEngagementRead,
    status_code=status.HTTP_201_CREATED,
)
def post_engagement(
    payload: FirmEnterpriseEngagementCreate,
    db: Session = Depends(get_db),
):
    try:
        engagement = create_engagement(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return serialize_engagement(engagement)


@router.get("/engagements/{engagement_id}", response_model=FirmEnterpriseEngagementRead)
def get_engagement_by_id(engagement_id: str, db: Session = Depends(get_db)):
    engagement = get_engagement(db, engagement_id)
    if not engagement:
        raise not_found(f"Engagement not found: {engagement_id}")
    return serialize_engagement(engagement)


@router.patch("/engagements/{engagement_id}", response_model=FirmEnterpriseEngagementRead)
def patch_engagement(
    engagement_id: str,
    payload: FirmEnterpriseEngagementUpdate,
    db: Session = Depends(get_db),
):
    engagement = update_engagement(db, engagement_id, payload)
    if not engagement:
        raise not_found(f"Engagement not found: {engagement_id}")
    return serialize_engagement(engagement)


@router.delete("/engagements/{engagement_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_engagement(engagement_id: str, db: Session = Depends(get_db)):
    if not delete_engagement(db, engagement_id):
        raise not_found(f"Engagement not found: {engagement_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/firms/{firm_id}/users", response_model=list[FirmUserRead])
def get_users(firm_id: str, db: Session = Depends(get_db)):
    return list_firm_users(db, firm_id)


@router.post(
    "/firms/{firm_id}/users",
    response_model=FirmUserRead,
    status_code=status.HTTP_201_CREATED,
)
def post_user(firm_id: str, payload: FirmUserCreate, db: Session = Depends(get_db)):
    try:
        return create_firm_user(db, firm_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/firms/{firm_id}/users/{user_id}", response_model=FirmUserRead)
def get_user(firm_id: str, user_id: str, db: Session = Depends(get_db)):
    user = get_firm_user(db, firm_id, user_id)
    if not user:
        raise not_found(f"Firm user not found: {user_id}")
    return user


@router.patch("/firms/{firm_id}/users/{user_id}", response_model=FirmUserRead)
def patch_user(
    firm_id: str,
    user_id: str,
    payload: FirmUserUpdate,
    db: Session = Depends(get_db),
):
    try:
        user = update_firm_user(db, firm_id, user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not user:
        raise not_found(f"Firm user not found: {user_id}")
    return user


@router.delete("/firms/{firm_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(firm_id: str, user_id: str, db: Session = Depends(get_db)):
    if not delete_firm_user(db, firm_id, user_id):
        raise not_found(f"Firm user not found: {user_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/firms/{firm_id}/clients", response_model=list[ClientRead])
def get_firm_clients(firm_id: str, db: Session = Depends(get_db)):
    return [serialize_client(db, client) for client in list_clients(db, firm_id)]


@router.post(
    "/firms/{firm_id}/clients",
    response_model=ClientRead,
    status_code=status.HTTP_201_CREATED,
)
def post_firm_client(
    firm_id: str,
    payload: ClientCreate,
    db: Session = Depends(get_db),
):
    try:
        client = create_client(db, firm_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return serialize_client(db, client)


@router.get("/firms/{firm_id}/clients/{client_id}", response_model=ClientRead)
def get_firm_client(firm_id: str, client_id: str, db: Session = Depends(get_db)):
    client = get_client(db, firm_id, client_id)
    if not client:
        raise not_found(f"Client not found: {client_id}")
    return serialize_client(db, client)


@router.patch("/firms/{firm_id}/clients/{client_id}", response_model=ClientRead)
def patch_firm_client(
    firm_id: str,
    client_id: str,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
):
    try:
        client = update_client(db, firm_id, client_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not client:
        raise not_found(f"Client not found: {client_id}")
    return serialize_client(db, client)


@router.delete("/firms/{firm_id}/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_firm_client(firm_id: str, client_id: str, db: Session = Depends(get_db)):
    if not delete_client(db, firm_id, client_id):
        raise not_found(f"Client not found: {client_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
