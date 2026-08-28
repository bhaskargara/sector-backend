from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FirmCreate(BaseModel):
    firm_name: str = Field(min_length=1, max_length=200)
    owner_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    status: str = "Active"
    remarks: str | None = None
    initial_user: "FirmUserCreate | None" = None


class FirmUpdate(BaseModel):
    firm_name: str | None = Field(default=None, min_length=1, max_length=200)
    owner_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    status: str | None = None
    remarks: str | None = None


class FirmRead(ORMBase):
    firm_id: str
    firm_name: str
    owner_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    status: str
    remarks: str | None = None


class FirmUserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=250)
    password: str = Field(min_length=8, max_length=250)
    role: str = "Firm Employee"
    status: str = "Active"


class FirmUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, min_length=3, max_length=250)
    password: str | None = Field(default=None, min_length=8, max_length=250)
    role: str | None = None
    status: str | None = None


class FirmUserRead(ORMBase):
    user_id: str
    firm_id: str
    full_name: str
    email: str
    role: str
    status: str


class PlatformAdminUserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=250)
    password: str = Field(min_length=8, max_length=250)
    role: str = "Platform Employee"
    status: str = "Active"


class PlatformAdminUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, min_length=3, max_length=250)
    password: str | None = Field(default=None, min_length=8, max_length=250)
    role: str | None = None
    status: str | None = None


class PlatformAdminUserRead(ORMBase):
    user_id: str
    full_name: str
    email: str
    role: str
    status: str


class ClientCreate(BaseModel):
    client_name: str = Field(min_length=1, max_length=200)
    legal_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    city: str | None = None
    dataset_key: str
    sector_id: str
    sub_sector_id: str
    status: str = "Draft"
    remarks: str | None = None


class ClientUpdate(BaseModel):
    client_name: str | None = Field(default=None, min_length=1, max_length=200)
    legal_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    city: str | None = None
    dataset_key: str | None = None
    sector_id: str | None = None
    sub_sector_id: str | None = None
    status: str | None = None
    remarks: str | None = None


class ClientRead(ORMBase):
    client_id: str
    firm_id: str
    client_name: str
    legal_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    city: str | None = None
    dataset_key: str
    sector_id: str
    sub_sector_id: str
    status: str
    remarks: str | None = None
    sector_name: str | None = None
    sub_sector_name: str | None = None
    enterprise_id: str | None = None


class EnterpriseCreate(BaseModel):
    enterprise_name: str = Field(min_length=1, max_length=200)
    legal_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    city: str | None = None
    status: str = "Active"
    remarks: str | None = None
    initial_user: "EnterpriseUserCreate | None" = None


class EnterpriseUpdate(BaseModel):
    enterprise_name: str | None = Field(default=None, min_length=1, max_length=200)
    legal_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    city: str | None = None
    status: str | None = None
    remarks: str | None = None


class EnterpriseRead(ORMBase):
    enterprise_id: str
    enterprise_name: str
    legal_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    city: str | None = None
    status: str
    remarks: str | None = None


class EnterpriseUserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=250)
    password: str = Field(min_length=8, max_length=250)
    role: str = "Enterprise Owner"
    status: str = "Active"


class EnterpriseUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, min_length=3, max_length=250)
    password: str | None = Field(default=None, min_length=8, max_length=250)
    role: str | None = None
    status: str | None = None


class EnterpriseUserRead(ORMBase):
    user_id: str
    enterprise_id: str
    full_name: str
    email: str
    role: str
    status: str


class FirmEnterpriseEngagementCreate(BaseModel):
    firm_id: str
    enterprise_id: str
    status: str = "Pending"
    invited_by_side: str | None = None
    invited_by_user_id: str | None = None
    engagement_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    remarks: str | None = None


class FirmEnterpriseEngagementUpdate(BaseModel):
    status: str | None = None
    invited_by_side: str | None = None
    invited_by_user_id: str | None = None
    engagement_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    remarks: str | None = None


class FirmEnterpriseEngagementRead(ORMBase):
    engagement_id: str
    firm_id: str
    enterprise_id: str
    status: str
    invited_by_side: str | None = None
    invited_by_user_id: str | None = None
    engagement_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime
    firm_name: str | None = None
    enterprise_name: str | None = None


FirmCreate.model_rebuild()
EnterpriseCreate.model_rebuild()
