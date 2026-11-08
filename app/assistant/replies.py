"""Engine results to the exact lines the chat shows, through app/ui/text.py (RU-16). Design: docs/architecture/j4_chat.md section 4.3."""
from dataclasses import fields
from typing import Literal

import app.ui.text as text
from app.engine import CustomerProfile, IncomeCut, Plan, Shock, ShockResult

from .chat_text import T
from .state import CardAnswer, EngineOutput

GLYPH = {"ok": "✓ ", "bad": "✕ ", "neutral": ""}


def greeting(p: CustomerProfile) -> tuple[str, ...]:
    return (T.greet.format(id=p.account_id), text.summary_line(p),
            T.range.format(first_month=p.first_month, last_month=p.last_month, n_months=p.n_months),
            *("- " + note for note in text.notes(p)[:3]), T.pick)


def _num(value) -> str:
    return str(int(value)) if isinstance(value, float) and value.is_integer() else repr(value)


def _cut_text(cut: IncomeCut) -> str:
    parts = [_num(cut.keep_fraction), _num(cut.months)]
    if cut.after_ends != IncomeCut.__dataclass_fields__["after_ends"].default:
        parts.append(f'after_ends="{cut.after_ends}"')
    if cut.ei_weekly_max is not None:
        parts.append(f"ei_weekly_max={_num(cut.ei_weekly_max)}")
    return f"IncomeCut({', '.join(parts)})"


def _shock_text(shock: Shock) -> str:
    parts = []
    for f in fields(Shock):
        value = getattr(shock, f.name)
        if value == f.default:
            continue
        parts.append(f"{f.name}={_cut_text(value) if f.name == 'income_cut' else _num(value)}")
    return f"Shock({', '.join(parts)})"


def call_text(function: str, account_id: int, shock: Shock, *, through_months: int | None = None, target_months: float | None = None) -> str:
    args = [str(account_id), _shock_text(shock)]
    if target_months is not None:
        args.append(f"target_months={_num(target_months)}")
    if through_months is not None:
        args.append(f"through_months={_num(through_months)}")
    return f"{function}({', '.join(args)})"


def result_lines(r: ShockResult, p: CustomerProfile, *, assumed_months: bool = False) -> tuple[str, ...]:
    v = text.verdict(r)
    lines = [GLYPH[v.tone] + v.sentence]
    if v.second_line:
        lines.append(v.second_line)
    lines.append(T.change_line.format(R0=r.before.runway.label, R1=r.after.runway.label, g0=text.money(r.before.gap), g1=text.money(r.after.gap)))
    lines.append(text.after_line(r))
    oneoff = text.oneoff_line(r)
    if oneoff is not None:
        lines.append(oneoff)
    lines.extend(text.fact_lines(r, p))
    assumption = text.assumption_line(r)
    if assumption is not None:
        lines.append(assumption)
    if r.bills_on_standing_orders.applies:
        row = text.orders_row(r)
        lines.append(T.ours_line.format(label=row.label, value=row.value, counterpart=row.counterpart))
    if assumed_months:
        lines.append(text.ASSUMED_LENGTH)
    return tuple(lines)


def plan_lines(plan: Plan, which: Literal["backup", "goal"]) -> tuple[str, ...]:
    if which == "goal":
        return tuple(text.goal_lines(plan))
    return (*text.backup_lines(plan), *(f"{s.order}. {s.action}" for s in plan.backup.steps))


def plain(answers: tuple[CardAnswer, ...]) -> str:
    """The shock in words, for T.confirm, T.partial and T.stack_replace. Last answer per field; fixed order."""
    last = {a.field: a.value for a in answers}
    assumed = {a.field for a in answers if a.source == "assumed"}
    parts = []
    job = []
    if "keep_pct" in last:
        job.append(T.plain_keep.format(n=text.number(last["keep_pct"])))
    if "months" in last:
        n = last["months"]
        job.append(T.plain_open if n is None else T.plain_month_one if n == 1 else T.plain_months_assumed.format(n=text.number(n)) if "months" in assumed else T.plain_months.format(n=text.number(n)))
    joined = " ".join(job)
    if "after_ends" in last:
        joined += T.plain_returns if last["after_ends"] == "income_returns" else T.plain_no_income
    if joined:
        parts.append(joined)
    if "bills_increase_pct" in last:
        parts.append(T.plain_bills.format(n=text.number(last["bills_increase_pct"])))
    if "other_spending_change" in last:
        parts.append(T.plain_rent.format(d=text.money(last["other_spending_change"])))
    if "one_off_spending_multiple" in last:
        n = last["one_off_spending_multiple"]
        parts.append(T.plain_repair_month_one if n == 1 else T.plain_repair_months.format(n=text.number(n)))
    if "one_off_dollars" in last:
        parts.append(T.plain_repair_dollars.format(d=text.money(last["one_off_dollars"])))
    return T.plain_join.join(parts)


def _through(shock: Shock) -> int | None:
    return shock.income_cut.months if shock.income_cut else None


def record(turn: int, call: str, *, r: ShockResult | None = None, plan: Plan | None = None, target_months: float | None = None) -> EngineOutput:
    if r is not None:
        return EngineOutput(turn, r.account_id, "apply_shock", call, r.shock, _through(r.shock), None, r.verdict_case,
                            r.before.runway.label, r.after.runway.label, r.before.gap, r.after.gap,
                            tuple(f.code for f in r.facts), None, None)
    if plan is not None:
        return EngineOutput(turn, plan.account_id, "make_plan", call, plan.backup.shock, plan.backup.through_months, target_months, None,
                            None, None, None, None, tuple(f.code for f in plan.facts), plan.goal.state, plan.backup.state)
    raise ValueError("record needs a result or a plan.")
