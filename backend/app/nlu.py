"""Moteur d'extraction d'intention et d'entités pour XamStat.

Approche par dictionnaires + correspondance approximative (aucune dépendance
à un service externe). Conçu pour être remplacé plus tard par un pipeline
RAG/LLM sans changer le contrat de `interpret()` : une question en entrée,
une `Intent` structurée en sortie.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

INDICATOR_KEYWORDS: dict[str, list[str]] = {
    "poverty_rate": [
        "taux de pauvrete",
        "pauvrete",
        "pauvres",
        "pauvre",
        "seuil de pauvrete",
        # wolof
        "miskinaay",
        "miskin",
    ],
    "population": [
        "population",
        "habitants",
        "habitant",
        "nombre de personnes",
        "combien de personnes",
        "peuplement",
        "peuplee",
        "peuple",
        # wolof
        "askan",
        "way dekk",
        "waa dekk",
        "nit ni",
        "naata nit",
    ],
    "density": [
        "densite de population",
        "densite",
        "dense",
        "habitants au km",
        "habitants par km",
        "peuplement au km",
    ],
}

INDICATOR_LABELS = {
    "poverty_rate": "taux de pauvreté",
    "population": "population",
    "density": "densité de population",
}

INDICATOR_ARTICLES = {
    "poverty_rate": "le",
    "population": "la",
    "density": "la",
}

INDICATOR_RANKING_PHRASES = {
    "poverty_rate": {"high": "le plus élevé", "low": "le plus bas"},
    "population": {"high": "la plus élevée", "low": "la plus basse"},
    "density": {"high": "la plus élevée", "low": "la plus basse"},
}

INDICATOR_UNITS = {
    "poverty_rate": "%",
    "population": "habitants",
    "density": "hab/km²",
}

RANKING_HIGH = [
    "la plus pauvre",
    "les plus pauvres",
    "le taux le plus eleve",
    "la plus touchee",
    "les plus touchees",
    "la plus peuplee",
    "les plus peuplees",
    "le plus de monde",
    "plus grande population",
    "la plus dense",
    "les plus denses",
    # wolof
    "gen a miskin",
]
RANKING_LOW = [
    "la moins pauvre",
    "les moins pauvres",
    "le taux le plus bas",
    "la moins touchee",
    "les moins touchees",
    "la moins peuplee",
    "les moins peuplees",
    "moins peuplee",
    "la moins dense",
    "les moins denses",
]

COMPARISON_MARKERS = ["compar", "par rapport", " vs ", " versus ", " contre ", " et "]

MULTI_MARKERS = ["classement", "quelles sont les regions", "top ", "toutes les regions"]


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize(text: str) -> str:
    text = strip_accents(text.lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Intent:
    raw_question: str
    indicator: str | None
    regions: list[str] = field(default_factory=list)
    ranking: tuple[str, int] | None = None  # ("high" | "low", n)
    wants_comparison: bool = False
    used_context: bool = False


class RegionCatalog:
    """Résout un nom de région (avec alias et tolérance aux fautes de frappe) à partir de regions.json."""

    def __init__(self, regions_data: dict):
        self._alias_to_name: dict[str, str] = {}
        self.names: list[str] = []
        for region in regions_data["regions"]:
            name = region["name"]
            self.names.append(name)
            aliases = set(region.get("aliases", [])) | {name}
            for alias in aliases:
                self._alias_to_name[normalize(alias)] = name

    def resolve_all(self, norm_text: str) -> list[str]:
        found: list[str] = []

        # 1) correspondance exacte de sous-chaîne (gère les alias multi-mots, ex. "saint louis")
        for alias, name in sorted(self._alias_to_name.items(), key=lambda kv: -len(kv[0])):
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, norm_text) and name not in found:
                found.append(name)

        if found:
            return found

        # 2) repli : correspondance approximative sur des groupes de 1 ou 2 mots
        # (tolère les fautes de frappe, y compris sur les alias à deux mots comme "saint louis")
        tokens = norm_text.split()
        candidates = list(tokens)
        candidates += [" ".join(tokens[i : i + 2]) for i in range(len(tokens) - 1)]
        aliases = list(self._alias_to_name.keys())
        for candidate in candidates:
            if len(candidate) < 4:
                continue
            match = difflib.get_close_matches(candidate, aliases, n=1, cutoff=0.8)
            if match:
                name = self._alias_to_name[match[0]]
                if name not in found:
                    found.append(name)
        return found


def _extract_indicator(norm_text: str) -> str | None:
    best_key, best_len = None, 0
    for key, keywords in INDICATOR_KEYWORDS.items():
        for kw in keywords:
            if kw in norm_text and len(kw) > best_len:
                best_key, best_len = key, len(kw)
    return best_key


def _extract_ranking(norm_text: str) -> tuple[str, int] | None:
    n = 3 if any(m in norm_text for m in MULTI_MARKERS) else 1
    for phrase in RANKING_HIGH:
        if phrase in norm_text:
            return ("high", n)
    for phrase in RANKING_LOW:
        if phrase in norm_text:
            return ("low", n)
    return None


def interpret(question: str, catalog: RegionCatalog, context_indicator: str | None = None) -> Intent:
    norm_text = normalize(question)
    indicator = _extract_indicator(norm_text)
    regions = catalog.resolve_all(norm_text)
    ranking = _extract_ranking(norm_text)
    wants_comparison = bool(ranking) or len(regions) >= 2 or any(m in norm_text for m in COMPARISON_MARKERS)

    # Question de suivi ("Et à Kolda ?") : pas d'indicateur cité mais une région, un
    # classement ou une comparaison le sont — on reprend l'indicateur de l'échange précédent.
    used_context = False
    if indicator is None and context_indicator and (regions or ranking):
        indicator = context_indicator
        used_context = True

    return Intent(
        raw_question=question,
        indicator=indicator,
        regions=regions,
        ranking=ranking,
        wants_comparison=wants_comparison,
        used_context=used_context,
    )
