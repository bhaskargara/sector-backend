from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    role: str = Field(pattern="^(platform_admin|firm_user|enterprise_user)$")
    email: str = Field(min_length=3, max_length=250)
    password: str = Field(min_length=1)
    firm_code: str | None = None
    enterprise_code: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "development"
    role: str
    display_name: str
    email: str
    firm_id: str | None = None
    firm_name: str | None = None
    enterprise_id: str | None = None
    enterprise_name: str | None = None
    landing_route: str | None = None
