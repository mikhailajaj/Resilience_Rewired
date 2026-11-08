"""The Findings page's figures (D10, D13 and the notebook findings F1 to F6). Computed live from the engine and cached (ADR 0009)."""
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .data import get_dataset
from .plan import make_plan
from .profile import account_flows, get_profile
from .response import DROP_THRESHOLD, MIN_MONTHS, income_drop_events, spending_response
from .shock import get_preset


@dataclass(frozen=True)
class FindingTier:
    name: str                     # SpendingResponse tier names: "Under 2 months", "2 to 6 months", "6 or more months"
    events: int                   # 410, 219, 106
    spending_kept_median: float   # median spending_kept in the tier: 0.37, 0.71, 2.47 (discovery §5 tier table)
    pass_through: float           # ResponseTier.raw_pass_through: 0.70, 0.27, -1.21


@dataclass(frozen=True)
class BiggestFinding:
    events: int                   # 735
    accounts: int                 # 480
    income_kept_median: float     # 0.13
    spending_kept_median: float   # 0.50
    within_10pct_share: float     # 0.05: spending stayed within 10% of usual
    predicted_below_zero: int     # 493: predicted_end < 0
    actually_below_zero: int      # 31: end_balance < 0
    months: int                   # MIN_MONTHS (3)
    threshold: float              # DROP_THRESHOLD (0.55)
    spending_kept: tuple[float, ...]   # one per event, for the chart
    evidence: str                 # SpendingResponse.evidence (the limits line)
    tiers: tuple[FindingTier, FindingTier, FindingTier]   # by start_buffer_months, edges 2 and 6 (F2)


@dataclass(frozen=True)
class AccountFindings:
    accounts: int                 # 4,500
    ei6_runs_out: int             # 1,596: job_loss_ei preset, through_months=6, backup.makes_it_before is False
    rescued_by_cuts: int          # 1,526: of those, makes_it_after_steps and no ask_lender step (D13)
    rescued_with_lender: int      # 22: makes_it_after_steps only with an ask_lender step
    rescued_total: int            # 1,548
    surplus_accounts: int         # 3,309: I - S > 0
    surplus_not_in_balance: int   # 1,038: of those, account_flows.change_last_12 <= 0
    running_loans: int            # 448
    loans_missed_by_medians: int  # 197: loan_median == 0 (D12)
    missed_payment_median: float  # 2,545.40: median P on those
    pension_accounts: int         # 740: income_type == "Pension"


@lru_cache(maxsize=1)
def biggest_finding() -> BiggestFinding:
    """Cached; reads only income_drop_events() and spending_response()."""
    events = income_drop_events()
    response = spending_response()
    kept = np.array([e.spending_kept for e in events])
    tiers = []
    for tier in response.tiers:
        in_tier = [e.spending_kept for e in events if tier.low <= e.start_buffer_months < tier.high]
        tiers.append(FindingTier(tier.name, len(in_tier), float(np.median(in_tier)) if in_tier else 0.0, tier.raw_pass_through))
    return BiggestFinding(
        events=len(events), accounts=len({e.account_id for e in events}),
        income_kept_median=float(np.median([e.income_kept for e in events])), spending_kept_median=float(np.median(kept)),
        within_10pct_share=float(((kept >= 0.9) & (kept <= 1.1)).mean()),
        predicted_below_zero=sum(e.predicted_end < 0 for e in events), actually_below_zero=sum(e.end_balance < 0 for e in events),
        months=MIN_MONTHS, threshold=DROP_THRESHOLD, spending_kept=tuple(float(v) for v in kept), evidence=response.evidence, tiers=tuple(tiers))


@lru_cache(maxsize=1)
def account_findings() -> AccountFindings:
    """Cached at first use; NOT called by warm_up(). One pass over every account: profile, flows and the EI plan over 6 months."""
    shock = get_preset("job_loss_ei")
    accounts = sorted(get_dataset().rows_by_account)
    runs_out = by_cuts = with_lender = surplus = not_in_balance = loans = missed = pension = 0
    missed_payments = []
    for account in accounts:
        p = get_profile(account)
        if p.income_type == "Pension":
            pension += 1
        if p.running_loan and p.P > 0:
            loans += 1
            if p.loan_median == 0:
                missed += 1
                missed_payments.append(p.P)
        if p.I - p.S > 0:
            surplus += 1
            if account_flows(account).change_last_12 <= 0:
                not_in_balance += 1
        backup = make_plan(account, shock, through_months=6).backup
        if backup.makes_it_before is False:
            runs_out += 1
            if backup.makes_it_after_steps:
                if any(step.code == "ask_lender" for step in backup.steps):
                    with_lender += 1
                else:
                    by_cuts += 1
    return AccountFindings(len(accounts), runs_out, by_cuts, with_lender, by_cuts + with_lender, surplus, not_in_balance, loans, missed,
                           float(np.median(missed_payments)) if missed_payments else 0.0, pension)
