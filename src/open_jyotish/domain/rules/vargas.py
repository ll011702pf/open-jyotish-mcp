from __future__ import annotations


STANDARD_VARGAS = (
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "D8",
    "D9",
    "D10",
    "D11",
    "D12",
    "D16",
    "D20",
    "D24",
    "D27",
    "D30",
    "D40",
    "D45",
    "D60",
)

COMMON_VARGAS = (
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "D8",
    "D9",
    "D10",
    "D11",
    "D12",
)

ADVANCED_VARGAS = (
    "D16",
    "D20",
    "D24",
    "D27",
    "D30",
    "D40",
    "D45",
    "D60",
)

VARGA_GROUPS = (
    ("常用分盘", COMMON_VARGAS),
    ("高阶分盘", ADVANCED_VARGAS),
)

DEFAULT_ENABLED_VARGAS = ["D1", "D9", "D10"]

VARGA_FACTORS = {
    "D1": 1,
    "D2": 2,
    "D3": 3,
    "D4": 4,
    "D5": 5,
    "D6": 6,
    "D7": 7,
    "D8": 8,
    "D9": 9,
    "D10": 10,
    "D11": 11,
    "D12": 12,
    "D16": 16,
    "D20": 20,
    "D24": 24,
    "D27": 27,
    "D30": 30,
    "D40": 40,
    "D45": 45,
    "D60": 60,
}

VARGA_LABELS = {
    "D1": "D1",
    "D2": "D2",
    "D3": "D3",
    "D4": "D4",
    "D5": "D5",
    "D6": "D6",
    "D7": "D7",
    "D8": "D8",
    "D9": "D9",
    "D10": "D10",
    "D11": "D11",
    "D12": "D12",
    "D16": "D16",
    "D20": "D20",
    "D24": "D24",
    "D27": "D27",
    "D30": "D30",
    "D40": "D40",
    "D45": "D45",
    "D60": "D60",
}


def normalize_enabled_vargas(value: list[str]) -> list[str]:
    if not value:
        raise ValueError("at least one varga must be enabled")

    normalized: list[str] = []
    seen: set[str] = set()
    for varga in value:
        name = varga.strip().upper()
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        normalized.append(name)

    if "D1" not in normalized:
        raise ValueError("D1 must always be enabled")

    unsupported = sorted(set(normalized) - set(STANDARD_VARGAS))
    if unsupported:
        raise ValueError(f"unsupported vargas: {', '.join(unsupported)}")
    return normalized


def grouped_available_vargas(available_vargas: list[str]) -> list[tuple[str, tuple[str, ...]]]:
    normalized_available = [varga for varga in STANDARD_VARGAS if varga in set(available_vargas)]
    groups: list[tuple[str, tuple[str, ...]]] = []
    for group_label, group_vargas in VARGA_GROUPS:
        members = tuple(varga for varga in group_vargas if varga in normalized_available)
        if members:
            groups.append((group_label, members))
    return groups
