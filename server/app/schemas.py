import base64
import binascii
import re
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

RFC_PATTERN = re.compile(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$")
POSTAL_CODE_PATTERN = re.compile(r"^\d{5}$")
VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
PLATE_PATTERN = re.compile(r"^[A-Z0-9-]{4,10}$")
PHOTO_MAX_BYTES = 5 * 1024 * 1024
PHOTO_DATA_URL_PATTERN = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/]+={0,2})$")


def normalize_rfc(value: str) -> str:
    normalized = value.strip().upper().replace(" ", "")
    if not RFC_PATTERN.fullmatch(normalized):
        raise ValueError("usa un RFC válido de 12 o 13 caracteres, por ejemplo ABC010203AB1")
    return normalized


def normalize_address_text(value: str, field_name: str) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} es obligatorio")
    return normalized


def normalize_postal_code(value: str) -> str:
    normalized = value.strip()
    if not POSTAL_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("usa un código postal mexicano válido de 5 dígitos")
    return normalized


def decode_photo_data_url(value: str | None) -> tuple[bytes | None, str | None]:
    if value is None or not value.strip():
        return None, None
    match = PHOTO_DATA_URL_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError("La foto debe ser JPG, PNG o WebP en formato de imagen válido.")
    content_type, encoded_data = match.groups()
    try:
        image_data = base64.b64decode(encoded_data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("No fue posible leer la foto seleccionada.") from exc
    if not image_data or len(image_data) > PHOTO_MAX_BYTES:
        raise ValueError("La foto debe tener un tamaño máximo de 5 MB.")
    valid_signature = (
        content_type == "image/jpeg" and image_data.startswith(b"\xff\xd8\xff")
        or content_type == "image/png" and image_data.startswith(b"\x89PNG\r\n\x1a\n")
        or content_type == "image/webp" and len(image_data) >= 12 and image_data.startswith(b"RIFF") and image_data[8:12] == b"WEBP"
    )
    if not valid_signature:
        raise ValueError("El contenido de la foto no coincide con su formato. Elige un archivo JPG, PNG o WebP válido.")
    return image_data, content_type


class RegisterInput(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    workshop_name: str = Field(min_length=3, max_length=120)
    workshop_tax_id: str = Field(min_length=12, max_length=13)
    workshop_state: str = Field(min_length=2, max_length=120)
    workshop_municipality: str = Field(min_length=2, max_length=120)
    workshop_locality: str | None = Field(default=None, max_length=120)
    workshop_colony: str = Field(min_length=2, max_length=120)
    workshop_postal_code: str = Field(min_length=5, max_length=5)

    @field_validator("full_name", "workshop_name")
    @classmethod
    def normalize_registration_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("workshop_tax_id")
    @classmethod
    def validate_workshop_tax_id(cls, value: str) -> str:
        return normalize_rfc(value)

    @field_validator("workshop_state", "workshop_municipality", "workshop_colony")
    @classmethod
    def validate_workshop_address_text(cls, value: str, info) -> str:
        return normalize_address_text(value, info.field_name.replace("workshop_", "").replace("_", " "))

    @field_validator("workshop_locality")
    @classmethod
    def validate_optional_workshop_locality(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return normalize_address_text(value, "localidad")

    @field_validator("workshop_postal_code")
    @classmethod
    def validate_workshop_postal_code(cls, value: str) -> str:
        return normalize_postal_code(value)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(char.islower() for char in value) or not any(char.isupper() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("la contraseña debe incluir mayúscula, minúscula y número")
        return value


class CustomerAccountRegisterInput(BaseModel):
    full_name: str = Field(min_length=5, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    workshop_tax_id: str = Field(min_length=12, max_length=13)

    @field_validator("full_name")
    @classmethod
    def normalize_customer_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned.split()) < 2:
            raise ValueError("escribe el nombre y al menos un apellido")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+", cleaned):
            raise ValueError("solo puede contener letras, espacios, guiones y apóstrofes")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_customer_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("workshop_tax_id")
    @classmethod
    def validate_customer_workshop_tax_id(cls, value: str) -> str:
        return normalize_rfc(value)

    @field_validator("password")
    @classmethod
    def customer_password_strength(cls, value: str) -> str:
        if not any(char.islower() for char in value) or not any(char.isupper() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("la contraseña debe incluir mayúscula, minúscula y número")
        return value


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class WorkshopInput(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    tax_id: str = Field(min_length=12, max_length=13)
    state: str = Field(min_length=2, max_length=120)
    municipality: str = Field(min_length=2, max_length=120)
    locality: str = Field(min_length=2, max_length=120)
    colony: str = Field(min_length=2, max_length=120)
    postal_code: str = Field(min_length=5, max_length=5)
    photo_data_url: str | None = Field(default=None, max_length=7_000_000)

    @field_validator("name")
    @classmethod
    def normalize_workshop_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("tax_id")
    @classmethod
    def validate_tax_id(cls, value: str) -> str:
        return normalize_rfc(value)

    @field_validator("state", "municipality", "locality", "colony")
    @classmethod
    def validate_address_text(cls, value: str, info) -> str:
        return normalize_address_text(value, info.field_name)

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str) -> str:
        return normalize_postal_code(value)

    @field_validator("photo_data_url")
    @classmethod
    def validate_photo(cls, value: str | None) -> str | None:
        decode_photo_data_url(value)
        return value


class WorkshopUpdateInput(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    tax_id: str = Field(min_length=12, max_length=13)
    state: str = Field(min_length=2, max_length=120)
    municipality: str = Field(min_length=2, max_length=120)
    locality: str | None = Field(default=None, max_length=120)
    colony: str = Field(min_length=2, max_length=120)
    postal_code: str = Field(min_length=5, max_length=5)

    @field_validator("name")
    @classmethod
    def normalize_workshop_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("tax_id")
    @classmethod
    def validate_tax_id(cls, value: str) -> str:
        return normalize_rfc(value)

    @field_validator("state", "municipality", "colony")
    @classmethod
    def validate_address_text(cls, value: str, info) -> str:
        return normalize_address_text(value, info.field_name)

    @field_validator("locality")
    @classmethod
    def validate_optional_locality(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return normalize_address_text(value, "locality")

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str) -> str:
        return normalize_postal_code(value)


class WorkshopStatusInput(BaseModel):
    is_active: bool


class CustomerInput(BaseModel):
    full_name: str = Field(min_length=5, max_length=120)
    phone: str = Field(min_length=10, max_length=25)
    email: EmailStr
    confirm_registration: bool = False

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned.split(" ")) < 2:
            raise ValueError("escribe el nombre y al menos un apellido")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+", cleaned):
            raise ValueError("solo puede contener letras, espacios, guiones y apóstrofes")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("usa un teléfono válido de 10 a 15 dígitos")
        return digits

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("confirm_registration")
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if not value:
            raise ValueError("confirma que deseas crear el registro del cliente")
        return value


class CustomerUpdateInput(BaseModel):
    full_name: str = Field(min_length=5, max_length=120)
    phone: str = Field(min_length=10, max_length=25)
    email: EmailStr
    confirm_update: bool = False

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned.split(" ")) < 2:
            raise ValueError("escribe el nombre y al menos un apellido")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+", cleaned):
            raise ValueError("solo puede contener letras, espacios, guiones y apóstrofes")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("usa un teléfono válido de 10 a 15 dígitos")
        return digits

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("confirm_update")
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if not value:
            raise ValueError("confirma que deseas actualizar el registro del cliente")
        return value


class CustomerStatusInput(BaseModel):
    is_active: bool


class VehicleEditableInput(BaseModel):
    plate: str = Field(min_length=4, max_length=15)
    brand: str = Field(min_length=2, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int = Field(ge=1886, le=date.today().year + 1)
    version: str = Field(min_length=1, max_length=80)
    color: str = Field(min_length=2, max_length=50)
    mileage: int | None = Field(default=None, ge=0, le=2_000_000)

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: str) -> str:
        normalized = re.sub(r"\s+", "", value.strip().upper())
        if not PLATE_PATTERN.fullmatch(normalized):
            raise ValueError("usa una placa de 4 a 10 caracteres alfanuméricos")
        return normalized

    @field_validator("brand", "model", "version", "color")
    @classmethod
    def normalize_vehicle_text(cls, value: str) -> str:
        return " ".join(value.split())


class VehicleInput(VehicleEditableInput):
    vin: str = Field(min_length=17, max_length=17)
    mileage: int | None = Field(default=None, ge=0, le=2_000_000)
    photo_data_url: str | None = Field(default=None, max_length=7_000_000)

    @field_validator("photo_data_url")
    @classmethod
    def validate_photo(cls, value: str | None) -> str | None:
        decode_photo_data_url(value)
        return value

    @field_validator("vin")
    @classmethod
    def validate_vin(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "")
        if not VIN_PATTERN.fullmatch(normalized):
            raise ValueError("el VIN debe tener 17 caracteres y no usar I, O ni Q")
        return normalized


class VehicleUpdateInput(VehicleEditableInput):
    model_config = ConfigDict(extra="forbid")
    mileage: int = Field(ge=0, le=2_000_000)
    confirm_update: bool = False

    @field_validator("confirm_update")
    @classmethod
    def require_confirmation(cls, value: bool) -> bool:
        if not value:
            raise ValueError("confirma que deseas actualizar el vehículo")
        return value


class MembershipInput(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(admin|reception|service_advisor|technician|customer|system)$")


class RoleUpdateInput(BaseModel):
    role: str = Field(pattern="^(admin|reception|service_advisor|technician|customer|system)$")


class MembershipStatusInput(BaseModel):
    is_active: bool


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
