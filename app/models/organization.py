from datetime import date

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class FirmMaster(TimestampMixin, Base):
    __tablename__ = "firm_master"

    firm_id: Mapped[str] = mapped_column(primary_key=True)
    firm_name: Mapped[str] = mapped_column(nullable=False, index=True)
    owner_name: Mapped[str | None]
    contact_email: Mapped[str | None] = mapped_column(index=True)
    phone: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="Active", nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)


class FirmUser(TimestampMixin, Base):
    __tablename__ = "firm_user"

    user_id: Mapped[str] = mapped_column(primary_key=True)
    firm_id: Mapped[str] = mapped_column(
        ForeignKey("firm_master.firm_id"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password_hash: Mapped[str | None]
    role: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(default="Active", nullable=False, index=True)

    firm: Mapped[FirmMaster] = relationship()


class PlatformAdminUser(TimestampMixin, Base):
    __tablename__ = "platform_admin_user"

    user_id: Mapped[str] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password_hash: Mapped[str | None]
    role: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(default="Active", nullable=False, index=True)


class EnterpriseMaster(TimestampMixin, Base):
    __tablename__ = "enterprise_master"

    enterprise_id: Mapped[str] = mapped_column(primary_key=True)
    enterprise_name: Mapped[str] = mapped_column(nullable=False, index=True)
    legal_name: Mapped[str | None] = mapped_column(index=True)
    contact_email: Mapped[str | None] = mapped_column(index=True)
    phone: Mapped[str | None]
    city: Mapped[str | None] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(default="Active", nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)


class EnterpriseUser(TimestampMixin, Base):
    __tablename__ = "enterprise_user"

    user_id: Mapped[str] = mapped_column(primary_key=True)
    enterprise_id: Mapped[str] = mapped_column(
        ForeignKey("enterprise_master.enterprise_id"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password_hash: Mapped[str | None]
    role: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(default="Active", nullable=False, index=True)

    enterprise: Mapped[EnterpriseMaster] = relationship()


class FirmEnterpriseEngagement(TimestampMixin, Base):
    __tablename__ = "firm_enterprise_engagement"

    engagement_id: Mapped[str] = mapped_column(primary_key=True)
    firm_id: Mapped[str] = mapped_column(
        ForeignKey("firm_master.firm_id"),
        nullable=False,
        index=True,
    )
    enterprise_id: Mapped[str] = mapped_column(
        ForeignKey("enterprise_master.enterprise_id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(default="Pending", nullable=False, index=True)
    invited_by_side: Mapped[str | None] = mapped_column(index=True)
    invited_by_user_id: Mapped[str | None] = mapped_column(index=True)
    engagement_name: Mapped[str | None] = mapped_column(index=True)
    start_date: Mapped[date | None]
    end_date: Mapped[date | None]
    remarks: Mapped[str | None] = mapped_column(Text)

    firm: Mapped[FirmMaster] = relationship()
    enterprise: Mapped[EnterpriseMaster] = relationship()


class ClientMaster(TimestampMixin, Base):
    __tablename__ = "client_master"

    client_id: Mapped[str] = mapped_column(primary_key=True)
    firm_id: Mapped[str] = mapped_column(
        ForeignKey("firm_master.firm_id"),
        nullable=False,
        index=True,
    )
    client_name: Mapped[str] = mapped_column(nullable=False, index=True)
    enterprise_id: Mapped[str | None] = mapped_column(
        ForeignKey("enterprise_master.enterprise_id"),
        index=True,
    )
    legal_name: Mapped[str | None] = mapped_column(index=True)
    contact_email: Mapped[str | None] = mapped_column(index=True)
    phone: Mapped[str | None]
    city: Mapped[str | None] = mapped_column(index=True)
    # Regulatory IDs are local to an independently owned dataset schema.
    dataset_key: Mapped[str] = mapped_column(
        ForeignKey("regulatory_dataset.dataset_key"), nullable=False, index=True
    )
    sector_id: Mapped[str] = mapped_column(nullable=False, index=True)
    sub_sector_id: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(default="Draft", nullable=False, index=True)
    remarks: Mapped[str | None] = mapped_column(Text)

    firm: Mapped[FirmMaster] = relationship()
    enterprise: Mapped[EnterpriseMaster | None] = relationship()
