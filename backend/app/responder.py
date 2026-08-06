"""Construit une réponse structurée (texte + spécification de graphique) à partir
d'une Intent déjà résolue par nlu.py, en s'appuyant uniquement sur les données
réelles chargées depuis regions.json. Aucune valeur n'est jamais inventée :
si une information manque, la réponse le dit explicitement.
"""

from __future__ import annotations

from .nlu import (
    INDICATOR_ARTICLES,
    INDICATOR_LABELS,
    INDICATOR_RANKING_PHRASES,
    INDICATOR_UNITS,
    Intent,
)
from .schemas import AskResponse, ChartSeries, ChartSpec, SourceInfo

SUGGESTED_QUESTIONS = [
    "Quel est le taux de pauvreté à Kaolack comparé à Dakar ?",
    "Quelle est la région la plus pauvre du Sénégal ?",
    "Quelle est la population de Thiès ?",
    "Quelles sont les régions les plus peuplées ?",
    "Quel est le taux de pauvreté au Sénégal ?",
    "Compare Ziguinchor et Kolda sur la pauvreté",
]

CLARIFICATION_ANSWER = (
    "Je peux répondre sur deux indicateurs pour l'instant : la population "
    "(RGPH-5, 2023) et le taux de pauvreté (EHCVM 2021/2022), par région "
    "du Sénégal. Essayez par exemple : « Quel est le taux de pauvreté à "
    "Kaolack ? » ou « Quelle est la population de Thiès ? »"
)


def _fmt(value: float, indicator: str) -> str:
    if indicator == "population":
        return f"{int(value):,}".replace(",", " ")
    return f"{value:.1f}".replace(".", ",")


def _region_by_name(regions_data: dict, name: str) -> dict:
    return next(r for r in regions_data["regions"] if r["name"] == name)


def _source_for(regions_data: dict, indicator: str) -> SourceInfo:
    meta = regions_data["meta"][indicator]
    return SourceInfo(report=meta["source"], table=meta["table"], url=meta["url"])


def _all_sorted(regions_data: dict, indicator: str, descending: bool) -> list[dict]:
    return sorted(regions_data["regions"], key=lambda r: r[indicator], reverse=descending)


def build_response(intent: Intent, regions_data: dict) -> AskResponse:
    if intent.indicator is None:
        return AskResponse(
            answer=CLARIFICATION_ANSWER,
            chart=ChartSpec(type="none"),
            source=None,
            suggestions=SUGGESTED_QUESTIONS,
        )

    indicator = intent.indicator
    label = INDICATOR_LABELS[indicator]
    unit = INDICATOR_UNITS[indicator]
    article = INDICATOR_ARTICLES[indicator]
    source = _source_for(regions_data, indicator)

    # 1) Classement (ex. "la région la plus pauvre", "le top 3 des régions les plus peuplées")
    if intent.ranking is not None:
        direction, n = intent.ranking
        ranked = _all_sorted(regions_data, indicator, descending=(direction == "high"))
        top = ranked[:n]
        series = [ChartSeries(label=r["name"], value=r[indicator]) for r in top]
        if n == 1:
            r = top[0]
            phrase = INDICATOR_RANKING_PHRASES[indicator][direction]
            answer = (
                f"D'après {source.report}, {r['name']} présente {article} {label} "
                f"{phrase} du pays : {_fmt(r[indicator], indicator)} {unit}."
            )
        else:
            items = ", ".join(f"{r['name']} ({_fmt(r[indicator], indicator)} {unit})" for r in top)
            answer = f"D'après {source.report}, le classement est : {items}."
        return AskResponse(
            answer=answer,
            chart=ChartSpec(type="bar", unit=unit, series=series, indicator=indicator),
            source=source,
            suggestions=SUGGESTED_QUESTIONS,
        )

    # 2) Comparaison entre régions citées (ou une région citée comparée au national)
    if intent.regions and intent.wants_comparison:
        cited = [_region_by_name(regions_data, name) for name in intent.regions]
        if len(cited) == 1:
            r = cited[0]
            national = regions_data["national"][indicator]
            series = [
                ChartSeries(label=r["name"], value=r[indicator]),
                ChartSeries(label="Sénégal (moyenne nationale)", value=national),
            ]
            answer = (
                f"Selon {source.report}, {article} {label} est de {_fmt(r[indicator], indicator)} {unit} "
                f"à {r['name']}, contre {_fmt(national, indicator)} {unit} au niveau national."
            )
        else:
            series = [ChartSeries(label=r["name"], value=r[indicator]) for r in cited]
            parts = ", ".join(f"{_fmt(r[indicator], indicator)} {unit} à {r['name']}" for r in cited)
            answer = f"Selon {source.report}, {article} {label} est de {parts}."
        return AskResponse(
            answer=answer,
            chart=ChartSpec(type="bar", unit=unit, series=series, indicator=indicator),
            source=source,
            suggestions=SUGGESTED_QUESTIONS,
        )

    # 3) Une seule région citée, sans comparaison explicite
    if len(intent.regions) == 1:
        r = _region_by_name(regions_data, intent.regions[0])
        ranked = _all_sorted(regions_data, indicator, descending=True)
        rank = next(i for i, x in enumerate(ranked, start=1) if x["name"] == r["name"])
        qualifier = "la plus touchée par la pauvreté" if indicator == "poverty_rate" else "la plus peuplée"
        answer = (
            f"Selon {source.report}, {article} {label} à {r['name']} est de "
            f"{_fmt(r[indicator], indicator)} {unit} — c'est la {rank}ᵉ région {qualifier} "
            f"sur les 14 régions du Sénégal."
        )
        national = regions_data["national"][indicator]
        series = [
            ChartSeries(label=r["name"], value=r[indicator]),
            ChartSeries(label="Sénégal (moyenne nationale)", value=national),
        ]
        return AskResponse(
            answer=answer,
            chart=ChartSpec(type="bar", unit=unit, series=series, indicator=indicator),
            source=source,
            suggestions=SUGGESTED_QUESTIONS,
        )

    # 4) Aucune région citée : réponse nationale + carte de toutes les régions
    national = regions_data["national"][indicator]
    series = [ChartSeries(label=r["name"], value=r[indicator]) for r in regions_data["regions"]]
    answer = (
        f"Selon {source.report}, {article} {label} au Sénégal est de "
        f"{_fmt(national, indicator)} {unit}. Voici la répartition par région :"
    )
    return AskResponse(
        answer=answer,
        chart=ChartSpec(type="map", unit=unit, series=series, indicator=indicator),
        source=source,
        suggestions=SUGGESTED_QUESTIONS,
    )
