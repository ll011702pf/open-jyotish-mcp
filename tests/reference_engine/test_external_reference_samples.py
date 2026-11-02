from __future__ import annotations

import json
from pathlib import Path

import pytest

from open_jyotish.application.services.chart_calculation_service import ChartCalculationService
from open_jyotish.application.services.reference_comparison_service import ReferenceComparisonService
from open_jyotish.infrastructure.ephemeris.swiss_ephemeris_adapter import SwissEphemerisAdapter
from open_jyotish.infrastructure.timezone.timezone_service import TimezoneService


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture_paths() -> list[Path]:
    return sorted(FIXTURES_DIR.glob("*.json"))


@pytest.mark.parametrize("fixture_path", load_fixture_paths(), ids=lambda path: path.stem)
def test_external_reference_fixture(fixture_path: Path) -> None:
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    comparison_service = ReferenceComparisonService(
        chart_calculation_service=ChartCalculationService(
            timezone_service=TimezoneService(),
            ephemeris_adapter=SwissEphemerisAdapter(),
        )
    )
    comparison = comparison_service.compare_payload(payload)

    if comparison.skipped:
        pytest.skip(f"External reference fixture skipped: {comparison.skip_reason}")
    assert comparison.passed, "\n".join(comparison.findings)
