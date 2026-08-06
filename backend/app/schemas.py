from typing import Literal, Optional

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    context_indicator: Optional[Literal["poverty_rate", "population", "density"]] = None


class ChartSeries(BaseModel):
    label: str
    value: float


class ChartSpec(BaseModel):
    type: Literal["bar", "map", "none"]
    unit: str = ""
    series: list[ChartSeries] = []
    indicator: Optional[str] = None  # used by the map view to pick the right color scale


class SourceInfo(BaseModel):
    report: str
    table: str
    url: str


class AskResponse(BaseModel):
    answer: str
    chart: ChartSpec
    source: Optional[SourceInfo] = None
    suggestions: list[str] = []
    indicator: Optional[str] = None
