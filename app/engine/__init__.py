"""Resilience Rewired engine. No UI code. See docs/engine_contract.md."""
from dataclasses import asdict, is_dataclass

from .data import get_dataset
from .errors import EngineError, InvalidAccountIdError, InvalidPlanError, InvalidShockError
from .formulas import Runway, money
from .findings import AccountFindings, BiggestFinding, FindingTier, account_findings, biggest_finding
from .goals import (DeadlineAnswer, EmergencyCost, EmergencyResult, GoalResult, PlanDesign, PlanRequest, Reach, Rebuild, SavingsGoal, TimeOff,
                    TimeOffCheck, TimeOffResult, Timeline, TimelineEvent, TimelineLine, Wallet, design_plan, wallets_at)
from .plan import BackupPlan, BackupStep, GoalAtRate, GoalPlan, LoanEndCheck, LowBalanceGoal, PathPoint, Plan, make_plan
from .profile import (AccountFlows, AccountIdRange, AccountOverview, AccountWarning, CustomerProfile, CustomerRecord, DistrictDetail, NoteDefinition,
                      OrderDetail, PersonDetail, account_flows, account_id_range, account_overview, customer_record, flags, get_profile,
                      monthly_history, note_catalogue)
from .rates import LoanEnd, SavingRate, SavingRates, loan_end, saving_rates
from .response import IncomeDropEvent, ResponseTier, SpendingResponse, income_drop_events, spending_response
from .shock import (EI_WEEKLY_MAX_2026, EI_WEEKLY_MAX_2026_SOURCE, WEEKS_PER_MONTH, CappedFigure, DurationResult, ExtraFigure, Fact, Figures,
                    IncomeCut, Preset, Shock, ShockResult, apply_shock, get_preset, list_presets)


def warm_up():
    """Loads the data, the spending response and the biggest finding, so the first lookup is instant. Not account_findings (ADR 0009)."""
    get_dataset()
    spending_response()
    biggest_finding()


def to_dict(result):
    """A result as plain dicts and lists, ready for json.dumps."""
    return _plain(asdict(result)) if is_dataclass(result) else _plain(result)


def _plain(node):
    if isinstance(node, dict):
        return {k: _plain(v) for k, v in node.items()}
    if isinstance(node, (list, tuple)):
        return [_plain(v) for v in node]
    return node


__all__ = [
    "AccountFlows", "AccountIdRange", "AccountOverview", "CustomerRecord", "DistrictDetail", "OrderDetail", "PersonDetail", "account_flows", "customer_record", "AccountWarning", "BackupPlan", "BackupStep", "CappedFigure", "CustomerProfile", "DurationResult",
    "EI_WEEKLY_MAX_2026", "EI_WEEKLY_MAX_2026_SOURCE", "EngineError", "WEEKS_PER_MONTH",
    "ExtraFigure", "Fact", "Figures", "GoalPlan", "IncomeCut", "InvalidAccountIdError", "InvalidPlanError", "InvalidShockError",
    "LowBalanceGoal", "NoteDefinition", "PathPoint", "Plan", "Preset", "ResponseTier", "Runway", "Shock", "ShockResult", "SpendingResponse",
    "account_id_range", "account_overview", "apply_shock", "flags", "get_preset", "get_profile", "list_presets", "make_plan", "money",
    "monthly_history", "note_catalogue", "spending_response", "to_dict", "warm_up",
    "AccountFindings", "BiggestFinding", "DeadlineAnswer", "EmergencyCost", "EmergencyResult", "FindingTier", "GoalAtRate", "GoalResult",
    "IncomeDropEvent", "LoanEnd", "LoanEndCheck", "PlanDesign", "PlanRequest", "Reach", "Rebuild", "SavingRate", "SavingRates", "SavingsGoal",
    "TimeOff", "TimeOffCheck", "TimeOffResult", "Timeline", "TimelineEvent", "TimelineLine", "Wallet", "account_findings", "biggest_finding",
    "design_plan", "income_drop_events", "loan_end", "saving_rates", "wallets_at",
]
