from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


PERSISTED_SCHEMA_VERSION = 1


class BirthData(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    schema_version: int = PERSISTED_SCHEMA_VERSION
    title: str
    subject_name: str | None = None
    birth_date: date
    birth_time: time
    timezone: str
    dst_mode: Literal["auto", "on", "off"]
    latitude: float
    longitude: float
    country: str | None = None
    city: str
    note: str | None = None

    @field_validator("title", "city")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("note")
    @classmethod
    def validate_note_length(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) > 2000:
            raise ValueError("note must be at most 2000 characters")
        return value

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if not -180 <= value <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return value

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("schema version must be at least 1")
        return value
