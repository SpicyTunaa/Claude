from pydantic import BaseModel, field_validator
import re


class NewHuntRequest(BaseModel):
    seed_domain: str
    vertical: str
    validate_domains: bool = True

    @field_validator("seed_domain")
    @classmethod
    def valid_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]{0,61}[a-zA-Z0-9])?$", v):
            raise ValueError("Invalid domain")
        return v

    @field_validator("vertical")
    @classmethod
    def non_empty_vertical(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("vertical cannot be empty")
        return v
