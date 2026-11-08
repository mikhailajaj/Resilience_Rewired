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


@dataclass(frozen=True)
class IncomeDropEvent:
    account_id: int
    start_month: str
    start_buffer_months: float    # month-end balance before the drop / trailing median spending
    base_in: float                # trailing 12-month medians, excluding the month itself
    base_out: float
    in_mean: float                # first MIN_MONTHS months
    out_mean: float
    start_balance: float          # month-end balance before the drop
    end_balance: float            # month-end balance after MIN_MONTHS months
    income_kept: float            # in_mean / base_in
    spending_kept: float          # out_mean / base_out
    predicted_end: float          # start_balance - MIN_MONTHS * (base_out - in_mean): spending held flat
    pass_through: float           # (base_out - out_mean) / (base_in - in_mean)


def _trailing_median(values):
    """Median of the previous 12 values. NaN where there are fewer than 12."""
    out = np.full(len(values), np.nan)
    if len(values) > BASELINE_MONTHS:
        windows = np.lib.stride_tricks.sliding_window_view(values[:-1], BASELINE_MONTHS)
        out[BASELINE_MONTHS:] = np.median(windows, axis=1)
    return out


def _events(rows_by_account):
    found = []
    for account, x in rows_by_account.items():
        money_in, money_out = x.money_in.to_numpy(), x.money_out.to_numpy()
        ends, months = x.month_end_balance.to_numpy(), x.month.to_numpy()
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
                    in_mean = float(money_in[i:i + MIN_MONTHS].mean())
                    out_mean = float(money_out[i:i + MIN_MONTHS].mean())
                    start, b_in, b_out = float(ends[i - 1]), float(base_in[i]), float(base_out[i])
                    found.append(IncomeDropEvent(
                        account_id=int(account), start_month=str(months[i]), start_buffer_months=start / b_out, base_in=b_in, base_out=b_out,
                        in_mean=in_mean, out_mean=out_mean, start_balance=start, end_balance=float(ends[i + MIN_MONTHS - 1]),
                        income_kept=in_mean / b_in, spending_kept=out_mean / b_out, predicted_end=start - MIN_MONTHS * (b_out - in_mean),
                        pass_through=(b_out - out_mean) / (b_in - in_mean)))
                i = j
            else:
                i += 1
    return tuple(found)


@lru_cache(maxsize=1)
def income_drop_events() -> tuple[IncomeDropEvent, ...]:
    """Cached. The one pass over the data; find_events and spending_response read it and return exactly what they did."""
    return _events(get_dataset().rows_by_account)


def find_events(rows_by_account):
    """(start buffer in months of usual spending, pass-through) for every qualifying income drop."""
    return [(e.start_buffer_months, e.pass_through) for e in _events(rows_by_account)]


@lru_cache(maxsize=1)
def spending_response():
    events = [(e.start_buffer_months, e.pass_through) for e in income_drop_events()]
    tiers = []
    for name, low, high in (("Under 2 months", -np.inf, 2.0), ("2 to 6 months", 2.0, 6.0), ("6 or more months", 6.0, np.inf)):
        in_tier = [p for b, p in events if low <= b < high]
        raw = float(np.median(in_tier)) if in_tier else 0.0
        tiers.append(ResponseTier(name, float(low) if low != -np.inf else -1e308, float(high) if high != np.inf else 1e308,
                                  len(in_tier), raw, min(max(raw, 0.0), 1.0)))
    evidence = (f"{len(events)} falls in deposits below 55% of normal for at least 3 months, nearly all on cash-only accounts. "
                "These aren't confirmed job losses.")
    return SpendingResponse(tuple(tiers), len(events), evidence)
