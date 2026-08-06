"""Export simplifié au format SDMX-JSON (structure inspirée du standard
d'échange de données statistiques SDMX : dimensions, séries, observations).

Note : les codes région utilisés (REF_AREA) sont des identifiants internes
générés à partir du nom de la région, pas des codes ISO 3166-2 certifiés —
à harmoniser avec la nomenclature officielle de l'ANSD si ce format devait
être exposé publiquement.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .nlu import INDICATOR_LABELS, INDICATOR_UNITS, normalize


def region_code(name: str) -> str:
    compact = normalize(name).replace(" ", "").upper()
    return f"SN-{compact[:3]}"


def build_sdmx_message(indicator: str, regions_data: dict) -> dict:
    meta = regions_data["meta"][indicator]
    regions = regions_data["regions"]

    series = {}
    for i, r in enumerate(regions):
        series[f"{i}:0"] = {"attributes": [], "observations": {"0": [r[indicator]]}}

    return {
        "header": {
            "id": f"XAMSTAT-{indicator.upper()}",
            "prepared": datetime.now(timezone.utc).isoformat(),
            "sender": {"id": "ANSD", "name": "Agence Nationale de la Statistique et de la Démographie"},
            "source": meta["source"],
            "note": (
                "Format simplifié inspiré de SDMX-JSON, à des fins de démonstration. "
                "Les codes REF_AREA sont des identifiants internes, pas des codes ISO 3166-2 officiels."
            ),
        },
        "dataSets": [{"action": "Information", "series": series}],
        "structure": {
            "name": INDICATOR_LABELS[indicator],
            "dimensions": {
                "series": [
                    {
                        "id": "REF_AREA",
                        "name": "Région",
                        "values": [{"id": region_code(r["name"]), "name": r["name"]} for r in regions],
                    }
                ],
                "observation": [{"id": "TIME_PERIOD", "name": "Période", "values": [{"id": "2023", "name": "2023"}]}],
            },
            "attributes": {
                "dataSet": [],
                "series": [],
                "observation": [
                    {
                        "id": "UNIT_MEASURE",
                        "name": "Unité de mesure",
                        "values": [{"id": INDICATOR_UNITS[indicator]}],
                    }
                ],
            },
        },
    }
