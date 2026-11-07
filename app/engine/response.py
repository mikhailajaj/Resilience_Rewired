"""How spending responded to real income drops, recomputed from the data as discovery.ipynb does."""
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .data import get_dataset

DROP_THRESHOLD = 0.55
MIN_MONTHS = 3
BASELINE_MONTHS = 12


@dataclass(frozen=True)
class ResponseTier:
    name: str
    low: float            # buffer in months of usual spending, inclusive
    high: float           # exclusive
    events: int
    raw_pass_through: float      # median spending cut per $1 of lost income
    response_per_dollar: float   # the same, clipped to 0..1


@dataclass(frozen=True)
class SpendingResponse:
    tiers: tuple
    total_events: int
    evidence: str

    def tier_for(self, buffer_months):
        for tier in self.tiers:
            if tier.low <= buffer_months < tier.high:
                return tier
        return self.tiers[-1]


def _trailing_median(values):
    """Median of the previous 12 values. NaN where there are fewer than 12."""
    out = np.full(len(values), np.nan)
    if len(values) > BASELINE_MONTHS:
        windows = np.lib.stride_tricks.sliding_window_view(values[:-1], BASELINE_MONTHS)
        out[BASELINE_MONTHS:] = np.median(windows, axis=1)
    return out


def find_events(rows_by_account):
    """(start buffer in months of usual spending, pass-through) for every qualifying income drop."""
    found = []
    for x in rows_by_account.values():
        money_in, money_out = x.money_in.to_numpy(), x.money_out.to_numpy()
        ends = x.month_end_balance.to_numpy()
        base_in, base_out = _trailing_median(money_in), _trailing_median(money_out)
        with np.errstate(invalid="ignore"):
            low = (money_in < DROP_THRESHOLD * base_in) & (base_in > 0)
        i, n = 0, len(x)
        while i <= n - MIN_MONTHS:
            if low[i:i + MIN_MONTHS].all():
                j = i + MIN_MONTHS
                while j < n and low[j]:
                    j += 1
                if base_out[i] > 0:
                    in_mean = money_in[i:i + MIN_MONTHS].mean()
                    out_mean = money_out[i:i + MIN_MONTHS].mean()
                    found.append((ends[i - 1] / base_out[i], (base_out[i] - out_mean) / (base_in[i] - in_mean)))
                i = j
            else:
                i += 1
    return found


@lru_cache(maxsize=1)
def spending_response():
    events = find_events(get_dataset().rows_by_account)
    tiers = []
    for name, low, high in (("Under 2 months", -np.inf, 2.0), ("2 to 6 months", 2.0, 6.0), ("6 or more months", 6.0, np.inf)):
        in_tier = [p for b, p in events if low <= b < high]
        raw = float(np.median(in_tier)) if in_tier else 0.0
        tiers.append(ResponseTier(name, float(low) if low != -np.inf else -1e308, float(high) if high != np.inf else 1e308,
                                  len(in_tier), raw, min(max(raw, 0.0), 1.0)))
    evidence = (f"{len(events)} falls in deposits below 55% of normal for at least 3 months, nearly all on cash-only accounts. "
                "These aren't confirmed job losses.")
    return SpendingResponse(tuple(tiers), len(events), evidence)
