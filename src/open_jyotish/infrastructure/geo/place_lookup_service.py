from __future__ import annotations

from dataclasses import dataclass
import gzip
import json
import re
import unicodedata
from functools import lru_cache
from importlib.resources import files


@dataclass(frozen=True, slots=True)
class PlaceRecord:
    city: str
    country: str
    timezone: str
    latitude: float
    longitude: float
    aliases: tuple[str, ...] = ()
    population: int = 0

    @property
    def label(self) -> str:
        return f"{self.city}, {self.country} | {self.timezone} | {self.latitude:.4f}, {self.longitude:.4f}"


PLACE_DATA: tuple[PlaceRecord, ...] = (
    PlaceRecord("Shanghai", "China", "Asia/Shanghai", 31.2304, 121.4737, ("sh", "shanghai")),
    PlaceRecord("Beijing", "China", "Asia/Shanghai", 39.9042, 116.4074, ("beijing", "peking")),
    PlaceRecord("Guangzhou", "China", "Asia/Shanghai", 23.1291, 113.2644, ("guangzhou", "canton")),
    PlaceRecord("Shenzhen", "China", "Asia/Shanghai", 22.5431, 114.0579, ("shenzhen",)),
    PlaceRecord("Hong Kong", "China", "Asia/Hong_Kong", 22.3193, 114.1694, ("hongkong", "hk")),
    PlaceRecord("Taipei", "Taiwan", "Asia/Taipei", 25.0330, 121.5654, ("taipei",)),
    PlaceRecord("Tokyo", "Japan", "Asia/Tokyo", 35.6762, 139.6503, ("tokyo",)),
    PlaceRecord("Seoul", "South Korea", "Asia/Seoul", 37.5665, 126.9780, ("seoul",)),
    PlaceRecord("Singapore", "Singapore", "Asia/Singapore", 1.3521, 103.8198, ("singapore",)),
    PlaceRecord("Bangkok", "Thailand", "Asia/Bangkok", 13.7563, 100.5018, ("bangkok",)),
    PlaceRecord("Delhi", "India", "Asia/Kolkata", 28.6139, 77.2090, ("delhi", "new delhi")),
    PlaceRecord("Mumbai", "India", "Asia/Kolkata", 19.0760, 72.8777, ("mumbai", "bombay")),
    PlaceRecord("Bengaluru", "India", "Asia/Kolkata", 12.9716, 77.5946, ("bengaluru", "bangalore")),
    PlaceRecord("London", "United Kingdom", "Europe/London", 51.5074, -0.1278, ("london",)),
    PlaceRecord("Paris", "France", "Europe/Paris", 48.8566, 2.3522, ("paris",)),
    PlaceRecord("Berlin", "Germany", "Europe/Berlin", 52.5200, 13.4050, ("berlin",)),
    PlaceRecord("Moscow", "Russia", "Europe/Moscow", 55.7558, 37.6173, ("moscow",)),
    PlaceRecord("Dubai", "United Arab Emirates", "Asia/Dubai", 25.2048, 55.2708, ("dubai",)),
    PlaceRecord("New York", "United States", "America/New_York", 40.7128, -74.0060, ("new york", "nyc")),
    PlaceRecord("Chicago", "United States", "America/Chicago", 41.8781, -87.6298, ("chicago",)),
    PlaceRecord("Los Angeles", "United States", "America/Los_Angeles", 34.0522, -118.2437, ("los angeles", "la")),
    PlaceRecord("San Francisco", "United States", "America/Los_Angeles", 37.7749, -122.4194, ("san francisco", "sf")),
    PlaceRecord("Toronto", "Canada", "America/Toronto", 43.6532, -79.3832, ("toronto",)),
    PlaceRecord("Sydney", "Australia", "Australia/Sydney", -33.8688, 151.2093, ("sydney",)),
    PlaceRecord("Melbourne", "Australia", "Australia/Melbourne", -37.8136, 144.9631, ("melbourne",)),
    PlaceRecord("Sao Paulo", "Brazil", "America/Sao_Paulo", -23.5558, -46.6396, ("sao paulo", "sao-paulo")),
)


class PlaceLookupService:
    def search_places(self, query: str, *, limit: int = 8) -> list[PlaceRecord]:
        records = load_place_records()
        normalized = normalize_query(query)
        if not normalized:
            return sorted(records, key=lambda record: (-record.population, record.city))[:limit]

        scored: list[tuple[int, PlaceRecord]] = []
        for record in records:
            haystacks = (
                normalize_query(record.city),
                normalize_query(record.country),
                normalize_query(record.timezone),
                *record.aliases,
            )
            score = score_match(normalized, haystacks)
            if score >= 0:
                scored.append((score, record))

        scored.sort(key=lambda item: (item[0], -item[1].population, item[1].city))
        return [record for _, record in scored[:limit]]


def score_match(query: str, haystacks: tuple[str, ...]) -> int:
    best_score = -1
    for haystack in haystacks:
        if haystack == query:
            return 0
        if haystack.startswith(query):
            best_score = min(best_score if best_score >= 0 else 1, 1)
        elif any(token.startswith(query) for token in haystack.split()):
            best_score = min(best_score if best_score >= 0 else 1, 1)
        elif query in haystack:
            best_score = min(best_score if best_score >= 0 else 2, 2)
    return best_score


def normalize_query(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    collapsed = re.sub(r"[^a-z0-9/_+-]+", " ", lowered)
    return re.sub(r"\s+", " ", collapsed).strip()


@lru_cache(maxsize=1)
def load_place_records() -> tuple[PlaceRecord, ...]:
    dataset_path = files("open_jyotish.infrastructure.geo").joinpath("data/world_cities.json.gz")
    if not dataset_path.is_file():
        return PLACE_DATA

    with gzip.open(dataset_path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    return tuple(
        PlaceRecord(
            city=item[0],
            country=item[1],
            timezone=item[2],
            latitude=float(item[3]),
            longitude=float(item[4]),
            population=int(item[5]),
            aliases=tuple(item[6]),
        )
        for item in payload
    )
