from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from open_jyotish.domain.enums.ayanamsha import AyanamshaId
from open_jyotish.domain.rules.vargas import DEFAULT_ENABLED_VARGAS
from open_jyotish.domain.rules.vargas import normalize_enabled_vargas


PERSISTED_SCHEMA_VERSION = 1


class CalculationProfile(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    schema_version: int = PERSISTED_SCHEMA_VERSION
    ayanamsha_id: AyanamshaId
    custom_ayanamsha_t0_jd: float | None = None
    custom_ayanamsha_value: float | None = None
    custom_ayanamsha_is_ut: bool = False
    house_system: str = "whole_sign"
    node_mode: Literal["true", "mean"] = "true"
    include_outer_planets: bool = False
    enabled_vargas: list[str] = DEFAULT_ENABLED_VARGAS.copy()

    @field_validator("enabled_vargas")
    @classmethod
    def validate_enabled_vargas(cls, value: list[str]) -> list[str]:
        return normalize_enabled_vargas(value)

    @field_validator("custom_ayanamsha_value")
    @classmethod
    def validate_custom_ayanamsha_value(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not -360 <= value <= 360:
            raise ValueError("custom ayanamsha value must be between -360 and 360")
        return value

    @field_validator("custom_ayanamsha_t0_jd")
    @classmethod
    def validate_custom_ayanamsha_t0_jd(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not 0 <= value <= 4_000_000:
            raise ValueError("custom ayanamsha t0 jd must be between 0 and 4000000")
        return value

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("schema version must be at least 1")
        return value

    def model_post_init(self, __context) -> None:
        if self.ayanamsha_id == AyanamshaId.CUSTOM:
            if self.custom_ayanamsha_t0_jd is None or self.custom_ayanamsha_value is None:
                raise ValueError("custom ayanamsha requires both t0 jd and ayanamsha value")
