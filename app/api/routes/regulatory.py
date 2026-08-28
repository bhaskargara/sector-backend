from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import regulatory_repository as repo
from app.schemas.regulatory import SectorRead, SubSectorRead

router = APIRouter()


@router.get("/sectors", response_model=list[SectorRead])
def get_sectors(dataset_key: str | None = None, db: Session = Depends(get_db)):
    return repo.list_sectors(db, dataset_key=dataset_key)


@router.get("/sub-sectors", response_model=list[SubSectorRead])
def get_sub_sectors(dataset_key: str, sector_id: str, db: Session = Depends(get_db)):
    return repo.list_sub_sectors(db, dataset_key=dataset_key, sector_id=sector_id)
