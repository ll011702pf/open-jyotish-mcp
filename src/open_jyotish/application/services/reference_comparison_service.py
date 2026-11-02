from __future__ import annotations

from dataclasses import dataclass

from open_jyotish.application.services.chart_calculation_service import ChartCalculationService
from open_jyotish.domain.models.birth_data import BirthData
from open_jyotish.domain.models.calculation_profile import CalculationProfile


DEFAULT_TOLERANCES = {
    "ayanamsha_value": 0.0005,
    "lagna_longitude": 0.01,
    "degree_in_sign": 0.01,
    "varga_lagna_longitude": 0.02,
    "varga_moon_degree_in_sign": 0.02,
}


@dataclass(slots=True)
class ReferenceComparisonResult:
    sample_id: str
    source: str
    passed: bool
    skipped: bool
    skip_reason: str | None
    findings: list[str]


@dataclass(slots=True)
class ReferenceComparisonService:
    chart_calculation_service: ChartCalculationService

    def compare_payload(self, payload: dict) -> ReferenceComparisonResult:
        sample_id = payload.get("sample_id", "unknown")
        source = payload.get("source", "external")
        verification = payload.get("verification", {})
        if verification.get("mode") == "manual_template":
            return ReferenceComparisonResult(
                sample_id=sample_id,
                source=source,
                passed=False,
                skipped=True,
                skip_reason=verification.get("reason") or "fixture is marked for manual verification",
                findings=[],
            )
        expected = payload["expected"]
        if expected["ayanamsha_value"] is None or expected["lagna_longitude"] is None:
            return ReferenceComparisonResult(
                sample_id=sample_id,
                source=source,
                passed=False,
                skipped=True,
                skip_reason="top-level expected values are not filled",
                findings=[],
            )

        tolerances = DEFAULT_TOLERANCES.copy()
        tolerances.update(payload.get("tolerances", {}))
        result = self.chart_calculation_service.calculate_chart(
            BirthData.model_validate(payload["birth_data"]),
            CalculationProfile.model_validate(payload["profile"]),
        )

        findings: list[str] = []
        if result.profile.enabled_vargas != payload["profile"]["enabled_vargas"]:
            findings.append(
                f"enabled_vargas mismatch: actual={result.profile.enabled_vargas} expected={payload['profile']['enabled_vargas']}"
            )
        self._compare_float(
            findings=findings,
            label="ayanamsha_value",
            actual=result.ayanamsha_value,
            expected=expected["ayanamsha_value"],
            tolerance=tolerances["ayanamsha_value"],
        )
        self._compare_float(
            findings=findings,
            label="lagna_longitude",
            actual=result.lagna_longitude,
            expected=expected["lagna_longitude"],
            tolerance=tolerances["lagna_longitude"],
        )

        for planet_name, planet_expected in expected["planet_positions"].items():
            if planet_expected["sign"] is None:
                return ReferenceComparisonResult(
                    sample_id=sample_id,
                    source=source,
                    passed=False,
                    skipped=True,
                    skip_reason=f"planet expectations are not filled for {planet_name}",
                    findings=findings,
                )
            planet = next(item for item in result.planets if item.planet == planet_name)
            self._compare_text(findings, f"{planet_name}.sign", planet.sign, planet_expected["sign"])
            if planet_expected["degree_in_sign"] is not None:
                self._compare_float(
                    findings=findings,
                    label=f"{planet_name}.degree_in_sign",
                    actual=planet.degree_in_sign,
                    expected=planet_expected["degree_in_sign"],
                    tolerance=tolerances["degree_in_sign"],
                )
            if planet_expected["nakshatra"] is not None:
                self._compare_text(findings, f"{planet_name}.nakshatra", planet.nakshatra, planet_expected["nakshatra"])
            if planet_expected["pada"] is not None:
                self._compare_text(findings, f"{planet_name}.pada", str(planet.pada), str(planet_expected["pada"]))
            if planet_expected["house"] is not None:
                self._compare_text(findings, f"{planet_name}.house", str(planet.house), str(planet_expected["house"]))
            if planet_expected["dignity"] is not None:
                self._compare_text(findings, f"{planet_name}.dignity", planet.dignity, planet_expected["dignity"])

        for varga_name, varga_expected in expected["vargas"].items():
            if varga_expected["lagna_longitude"] is None:
                return ReferenceComparisonResult(
                    sample_id=sample_id,
                    source=source,
                    passed=False,
                    skipped=True,
                    skip_reason=f"varga expectations are not filled for {varga_name}",
                    findings=findings,
                )
            varga = result.vargas[varga_name]
            moon = next(item for item in varga.planets if item.planet == "Moon")
            self._compare_float(
                findings=findings,
                label=f"{varga_name}.lagna_longitude",
                actual=varga.lagna_longitude,
                expected=varga_expected["lagna_longitude"],
                tolerance=tolerances["varga_lagna_longitude"],
            )
            if varga_expected["moon_sign"] is not None:
                self._compare_text(findings, f"{varga_name}.moon_sign", moon.sign, varga_expected["moon_sign"])
            if varga_expected["moon_degree_in_sign"] is not None:
                self._compare_float(
                    findings=findings,
                    label=f"{varga_name}.moon_degree_in_sign",
                    actual=moon.degree_in_sign,
                    expected=varga_expected["moon_degree_in_sign"],
                    tolerance=tolerances["varga_moon_degree_in_sign"],
                )

        return ReferenceComparisonResult(
            sample_id=sample_id,
            source=source,
            passed=not findings,
            skipped=False,
            skip_reason=None,
            findings=findings,
        )

    def _compare_float(
        self,
        *,
        findings: list[str],
        label: str,
        actual: float,
        expected: float,
        tolerance: float,
    ) -> None:
        diff = abs(actual - expected)
        if diff > tolerance:
            findings.append(
                f"{label} mismatch: actual={actual:.6f} expected={expected:.6f} diff={diff:.6f} tol={tolerance:.6f}"
            )

    def _compare_text(self, findings: list[str], label: str, actual: str, expected: str) -> None:
        if actual != expected:
            findings.append(f"{label} mismatch: actual={actual} expected={expected}")
