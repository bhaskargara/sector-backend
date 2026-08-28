"""Regulatory selection API backed only by the parallel dataset schemas."""

from sqlalchemy.orm import Session

from app.repositories.regulatory_runtime import list_sectors as runtime_list_sectors
from app.repositories.regulatory_runtime import list_sub_sectors as runtime_list_sub_sectors


def list_sectors(db: Session, dataset_key: str | None = None):
    return runtime_list_sectors(db, dataset_key)


def list_sub_sectors(db: Session, dataset_key: str, sector_id: str):
    return runtime_list_sub_sectors(db, dataset_key, sector_id)
