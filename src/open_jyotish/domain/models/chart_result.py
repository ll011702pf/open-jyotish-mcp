from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from open_jyotish.domain.models.birth_data import BirthData
from open_jyotish.domain.models.calculation_profile import CalculationProfile


PERSISTED_SCHEMA_VERSION = 1


class PlanetPosition(BaseModel):
    planet: str
    longitude_sidereal: float
    sign: str
    degree_in_sign: float
    nakshatra: str
    nakshatra_lord: str = ""
    pada: int
    house: int | None = None
    retrograde: bool = False
    dignity: str = "Neutral"
    speed_value: float | None = None


class VargaChart(BaseModel):
    name: str
    lagna_longitude: float
    planets: list[PlanetPosition]


class DashaPeriod(BaseModel):
    level: str
    lord: str
    start_at: datetime
    end_at: datetime
    duration_years: float
    parent_lord: str | None = None


class PanchangaDetails(BaseModel):
    vedic_weekday: str = ""
    tithi_name: str = ""
    tithi_number: int = 0
    tithi_progress_percent: float = 0.0
    yoga_name: str = ""
    yoga_number: int = 0
    yoga_progress_percent: float = 0.0
    karana_name: str = ""
    karana_number: int = 0
    karana_progress_percent: float = 0.0


class SolarContext(BaseModel):
    sidereal_time_hours: float = 0.0
    sidereal_time_text: str = ""
    sunrise_at: datetime | None = None
    sunset_at: datetime | None = None


class PlanetStrengthProfile(BaseModel):
    planet: str
    uchcha_bala: float
    saptavargaja_bala: float = 0.0
    ojhayugma_bala: float = 0.0
    kendradi_bala: float = 0.0
    drekkana_bala: float = 0.0
    sthana_bala: float = 0.0
    dig_bala: float
    natonnata_bala: float = 0.0
    paksha_bala: float = 0.0
    hora_bala: float = 0.0
    kala_bala: float = 0.0
    naisargika_bala: float
    motion_bala: float
    cheshta_bala: float = 0.0
    drik_bala: float = 0.0
    ishta_phala: float = 0.0
    kashta_phala: float = 0.0
    total_bala: float
    classification: str


class AshtakavargaRow(BaseModel):
    label: str
    sign_values: list[int]


class AshtakavargaPinda(BaseModel):
    label: str
    rasi_pinda: int
    graha_pinda: int
    sodhya_pinda: int


class AshtakavargaDetails(BaseModel):
    binna_rows: list[AshtakavargaRow] = Field(default_factory=list)
    samudaya: list[int] = Field(default_factory=list)
    trikona_rows: list[AshtakavargaRow] = Field(default_factory=list)
    ekadhipatya_rows: list[AshtakavargaRow] = Field(default_factory=list)
    pinda_rows: list[AshtakavargaPinda] = Field(default_factory=list)


class VimsopakaEntry(BaseModel):
    label: str
    score: float
    percent: float
    qualifying_count: int
    qualifying_vargas: list[str] = Field(default_factory=list)


class PlanetVargaQualityProfile(BaseModel):
    planet: str
    vimsopaka: list[VimsopakaEntry] = Field(default_factory=list)
    vaiseshikamsa: list[str] = Field(default_factory=list)


class CharaKarakaAssignment(BaseModel):
    role: str
    planet: str
    meaning: str
    rank_value: float


class PlanetStateProfile(BaseModel):
    planet: str
    age_state: str
    alertness_state: str
    mood_states: list[str] = Field(default_factory=list)
    activity_state: str


class DetectedYoga(BaseModel):
    key: str
    name: str
    category: str
    description: str


class DetectedDosha(BaseModel):
    key: str
    name: str
    severity: str
    description: str


class PlanetRelationshipProfile(BaseModel):
    planet: str
    natural: dict[str, str] = Field(default_factory=dict)
    temporary: dict[str, str] = Field(default_factory=dict)
    compound: dict[str, str] = Field(default_factory=dict)


class AspectEntry(BaseModel):
    source: str
    target: str
    system: str
    aspect_name: str
    source_sign: str
    target_sign: str
    house_distance: int
    orb_degrees: float = 0.0
    strength: float
    classification: str


class ArgalaEntry(BaseModel):
    reference: str
    argala_type: str
    house_from_reference: int
    obstructing_house: int
    supporters: list[str] = Field(default_factory=list)
    obstructors: list[str] = Field(default_factory=list)
    status: str
    net_strength: int = 0


class TransitEntry(BaseModel):
    planet: str
    natal_sign: str
    transit_sign: str
    transit_degree: float
    house_from_lagna: int
    house_from_moon: int
    natal_house: int | None = None
    sign_shift: int = 0
    relation_to_natal: str = "-"
    orb_degrees: float | None = None
    retrograde: bool = False
    dignity: str = "Neutral"


class TransitSnapshot(BaseModel):
    as_of_utc: datetime
    as_of_local: datetime
    timezone: str
    transit_lagna_longitude: float
    entries: list[TransitEntry] = Field(default_factory=list)


class TransitAshtakavargaEntry(BaseModel):
    planet: str
    transit_sign: str
    house_from_lagna: int
    sav_value: int
    sav_band: str
    planet_bav_value: int | None = None
    overlay_score: int
    overlay_note: str = ""


class TransitAshtakavargaOverlay(BaseModel):
    as_of_utc: datetime
    sav_average: float
    sav_peak_sign: str
    sav_peak_value: int
    entries: list[TransitAshtakavargaEntry] = Field(default_factory=list)


class ChartResult(BaseModel):
    schema_version: int = PERSISTED_SCHEMA_VERSION
    chart_id: str
    birth_data: BirthData
    profile: CalculationProfile
    jd_ut: float
    ayanamsha_value: float
    lagna_longitude: float
    planets: list[PlanetPosition]
    houses: list[float]
    vargas: dict[str, VargaChart]
    moon_chart: VargaChart | None = None
    bhava_chart: VargaChart | None = None
    vimshottari_dasha: list[DashaPeriod]
    vimshottari_antardasha: dict[str, list[DashaPeriod]]
    panchanga: PanchangaDetails | None = None
    solar_context: SolarContext | None = None
    auxiliary_points: list[PlanetPosition] = Field(default_factory=list)
    planet_strengths: list[PlanetStrengthProfile] = Field(default_factory=list)
    ashtakavarga: AshtakavargaDetails | None = None
    varga_quality_profiles: list[PlanetVargaQualityProfile] = Field(default_factory=list)
    chara_karakas: list[CharaKarakaAssignment] = Field(default_factory=list)
    planetary_states: list[PlanetStateProfile] = Field(default_factory=list)
    yogas: list[DetectedYoga] = Field(default_factory=list)
    doshas: list[DetectedDosha] = Field(default_factory=list)
    planet_relationships: list[PlanetRelationshipProfile] = Field(default_factory=list)
    aspects: list[AspectEntry] = Field(default_factory=list)
    argala_entries: list[ArgalaEntry] = Field(default_factory=list)
    transit_snapshot: TransitSnapshot | None = None
    transit_ashtakavarga_overlay: TransitAshtakavargaOverlay | None = None
    tags: list[str] = Field(default_factory=list)
    computed_at: datetime

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in value:
            tag = raw.strip()
            if not tag:
                continue
            if len(tag) > 30:
                raise ValueError("tag must be at most 30 characters")
            normalized = tag.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(tag)
        return cleaned

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: int) -> int:
        if value < 1:
            raise ValueError("schema version must be at least 1")
        return value
