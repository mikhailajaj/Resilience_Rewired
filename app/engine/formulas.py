"""The README runway rule, on plain numbers."""
from dataclasses import dataclass

NO_SHORTFALL_LABEL = "No shortfall (120+)"
RUNWAY_CAP = 120


@dataclass(frozen=True)
class Runway:
    state: str  # no_buffer, no_shortfall or months
    months: float | None
    label: str


def runway_from(buffer_left, gap):
    buffer_left, gap = float(buffer_left), float(gap)
    if buffer_left <= 0:
        return Runway("no_buffer", 0.0, "0 months")
    if gap <= 0:
        return Runway("no_shortfall", None, NO_SHORTFALL_LABEL)
    months = round(min(buffer_left / gap, RUNWAY_CAP), 1)
    return Runway("months", months, f"{months:.1f} months")


def money(value):
    return f"-${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"
