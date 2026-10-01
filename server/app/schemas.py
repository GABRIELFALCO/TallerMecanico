from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterInput(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    workshop_name: str = Field(min_length=3, max_length=120)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(char.islower() for char in value) or not any(char.isupper() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("la contraseña debe incluir mayúscula, minúscula y número")
        return value


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class WorkshopInput(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    tax_id: str | None = Field(default=None, max_length=32)


class CustomerInput(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    phone: str = Field(min_length=7, max_length=25)
    email: EmailStr | None = None


class MembershipInput(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(owner|manager|reception|mechanic)$")


class MembershipView(BaseModel):
    workshop_id: str
    workshop_name: str
    workshop_active: bool
    role: str


class MeView(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    is_verified: bool
    memberships: list[MembershipView]
