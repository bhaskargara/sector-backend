from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class RegulatoryDataset(TimestampMixin, Base):
    __tablename__ = "regulatory_dataset"

    dataset_key: Mapped[str] = mapped_column(primary_key=True)
    schema_name: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(nullable=False, index=True)
    dataset_type: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[str] = mapped_column(nullable=False, index=True, default="Yes")
    workbook_path: Mapped[str | None] = mapped_column(Text)

