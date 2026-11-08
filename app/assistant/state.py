"""The chat's records, events and size rules. No Streamlit, no network (RU-15). Contract: docs/architecture/j4_chat.md section 3."""
import math
from dataclasses import dataclass
from numbers import Real
from typing import Literal, Union

from app.engine import IncomeCut, Shock
from app.engine.shock import AFTER_ENDS, MAX_MONTHS

Kind = Literal["job", "bills", "repair"]                      # glossary "Kind"; mix is job + bills
Twist = Literal["job", "bills", "repair", "mix", "type"]     # the T2 buttons
Source = Literal["button", "typed", "parsed", "assumed"]
ASSUMED_MONTHS = 6                              # D2, ADR 0010: card 3 gives no length; assume card 1's 6 months
Phase = Literal["no_customer", "greeting", "ask_size", "confirm", "result", "plan", "pick_size", "sent"]
Status = Literal["ok", "partial", "out_of_range", "unsure"]
FollowUp = Literal["backup", "goal", "stack", "size", "new", "send"]
Field = Literal["keep_pct", "months", "after_ends", "bills_increase_pct", "other_spending_change",
                "one_off_spending_multiple", "one_off_dollars"]
DEFAULT_TARGET = 3.0     # make_plan's default target_months; the goal plan uses ctx.target_months (OI-5)


@dataclass(frozen=True)
class SizeRule:
    field: Field
    kind: Kind
    unit: str               # "%", "months", "$ a month", "months of spending", "$", ""
    low: float | None
    high: float | None      # None: no upper limit
    whole: bool


RULES: dict[str, SizeRule] = {r.field: r for r in (
    SizeRule("keep_pct", "job", "%", 0, 100, False),
    SizeRule("months", "job", "months", 1, MAX_MONTHS, True),          # None = until it runs out
    SizeRule("after_ends", "job", "", None, None, False),               # one of AFTER_ENDS
    SizeRule("bills_increase_pct", "bills", "%", 0, None, False),
    SizeRule("other_spending_change", "bills", "$ a month", 0, None, False),
    SizeRule("one_off_spending_multiple", "repair", "months of spending", 0, None, False),
    SizeRule("one_off_dollars", "repair", "$", 0, None, False),
)}
KIND_FIELDS: dict[str, tuple[Field, ...]] = {
    "job": ("keep_pct", "months"),
    "bills": ("bills_increase_pct",),
    "repair": ("one_off_spending_multiple",),
    "mix": ("keep_pct", "months", "bills_increase_pct"),
}
FIELD_KIND: dict[str, Kind] = {f: r.kind for f, r in RULES.items()}

# The {size} and {range} words of T.out_of_range (NEW-COPY-4, drafted). Plain strings here so state stays free of the copy module.
SIZE_WORDS = {"keep_pct": "income kept", "months": "the length", "after_ends": "what happens after", "bills_increase_pct": "the bills rise",
              "other_spending_change": "the rent rise", "one_off_spending_multiple": "the repair", "one_off_dollars": "the repair"}
RANGE_WORDS = {"keep_pct": "0 to 100%", "months": f"a whole number of months from 1 to {MAX_MONTHS}", "after_ends": " or ".join(AFTER_ENDS)}
ZERO_OR_MORE = "0 or more"


@dataclass(frozen=True)
class CardAnswer:
    """One choice (RU-18). value is in the presenter's unit: keep is a percent (55, not 0.55)."""
    turn: int                                  # the turn it was stored on; parse() returns -1, flow stamps it
    kind: Kind
    field: Field
    value: float | int | str | None            # months None = until it runs out; after_ends a word
    unit: str
    source: Source
    shown: str                                 # as shown: "55%", "Until it runs out", "laid off, EI 55% ..."


@dataclass(frozen=True)
class RangeProblem:
    field: Field
    value: str          # as typed, for T.out_of_range {value}
    size: str           # T.out_of_range {size}
    range: str          # T.out_of_range {range}


@dataclass(frozen=True)
class ParseResult:
    status: Status
    answers: tuple[CardAnswer, ...] = ()       # source "parsed", turn -1, asking order
    missing: tuple[Field, ...] = ()            # partial: fields still to ask, in asking order
    unsure: str | None = None                  # "U1" .. "U6"
    month_named: bool = False                  # U6 because of a calendar month: T.unsure_month
    problem: RangeProblem | None = None        # out_of_range

    @property
    def shock(self) -> Shock | None:           # shock_from(answers) when status == "ok", else None
        return shock_from(self.answers) if self.status == "ok" else None


@dataclass(frozen=True)
class EngineOutput:
    """One engine run (RU-18, glossary "Engine output"). Copied from the result when it ran; never recomputed."""
    turn: int
    account_id: int
    function: Literal["apply_shock", "make_plan"]
    call: str                                  # the {call} of T.engine_call, exactly as shown
    shock: Shock
    through_months: int | None
    target_months: float | None                # make_plan only
    verdict_case: str | None                   # apply_shock only
    runway_before: str | None                  # Runway.label
    runway_after: str | None
    gap_before: float | None
    gap_after: float | None
    fact_codes: tuple[str, ...]
    goal_state: str | None                     # make_plan only
    backup_state: str | None


# Events: one per click or typed line. turn is the state's turn when the widget was drawn (RU-19).
@dataclass(frozen=True)
class CustomerSeen:
    account_id: int | None
    turn: int = -1                             # never stale: the page sends it whenever ss.shown_id differs


@dataclass(frozen=True)
class TwistPicked:
    turn: int
    twist: Twist


@dataclass(frozen=True)
class FieldPicked:                             # "Dollars a month", "Dollar amount", or a PickSize button
    turn: int
    field: Field


@dataclass(frozen=True)
class ValuePicked:                             # a size button
    turn: int
    field: Field
    value: float | int | str | None
    label: str


@dataclass(frozen=True)
class ValueTyped:                              # the Other box
    turn: int
    field: Field
    text: str


@dataclass(frozen=True)
class TextSent:                                # st.chat_input
    turn: int
    text: str


@dataclass(frozen=True)
class ConfirmPicked:                           # T.b_run (True) or T.b_buttons (False)
    turn: int
    run: bool


@dataclass(frozen=True)
class FollowUpPicked:
    turn: int
    action: FollowUp


@dataclass(frozen=True)
class SendApplied:                             # the page wrote ss.inp; clears the outbox
    turn: int


Event = Union[CustomerSeen, TwistPicked, FieldPicked, ValuePicked, ValueTyped, TextSent, ConfirmPicked, FollowUpPicked, SendApplied]


@dataclass(frozen=True)
class Option:
    key: str            # stable slug, unique in its message: "job", "keep_55", "months_none", "backup", "run"
    label: str          # the T.* text on the button
    event: Event


@dataclass(frozen=True)
class OtherBox:
    field: Field
    placeholder: str    # "0 to 100", "1 to 120", "$ a month"
    button: str         # T.use


@dataclass(frozen=True)
class Message:
    turn: int
    role: Literal["assistant", "user"]
    lines: tuple[str, ...]                     # raw Markdown, "$" unescaped; the page escapes, the transcript doesn't
    options: tuple[Option, ...] = ()
    other: OtherBox | None = None


@dataclass(frozen=True)
class Section:
    """One earlier customer, kept for the transcript only (RU-20)."""
    account_id: int
    messages: tuple[Message, ...]
    answers: tuple[CardAnswer, ...]
    outputs: tuple[EngineOutput, ...]


@dataclass(frozen=True)
class Context:
    """What the page reads from outside the chat on each event."""
    target_months: float = DEFAULT_TARGET     # ss.inp["target"] if set, else 3 (J4.3 1a, OI-5)


@dataclass(frozen=True)
class ChatState:
    account_id: int | None = None
    phase: Phase = "no_customer"
    turn: int = 0                              # +1 on every accepted event; widget keys use it
    messages: tuple[Message, ...] = ()         # current customer only (RU-20)
    answers: tuple[CardAnswer, ...] = ()       # every card answer for this customer, in order (RU-18)
    outputs: tuple[EngineOutput, ...] = ()     # every engine run for this customer, in order (RU-18)
    current: tuple[CardAnswer, ...] = ()       # the shock now on screen, one answer per field
    draft: tuple[CardAnswer, ...] = ()         # the card being built
    asking: tuple[Field, ...] = ()             # fields still to ask; asking[0] is on screen
    pending: ParseResult | None = None         # an ok reading waiting for Run it (RU-17)
    stacking: bool = False                     # T.f_stack: the next card adds to current (RU-21)
    outbox: tuple[CardAnswer, ...] | None = None   # sizes for the page to write into ss.inp
    archive: tuple[Section, ...] = ()          # earlier customers


def _shown(field, value):
    unit = RULES[field].unit
    if isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value):
        n = f"{value:g}" if abs(value) < 1e15 else repr(value)
        return {"%": f"{n}%", "months": f"{n} months", "$ a month": f"${n} a month", "$": f"${n}", "months of spending": f"{n} months of spending"}.get(unit, n)
    return str(value)


def check_size(field: Field, value) -> RangeProblem | None:
    """None if the engine takes this size (RU-22). Months None (until it runs out) is allowed; bools, NaN and infinity never are."""
    rule = RULES[field]
    if field == "after_ends":
        ok = value in AFTER_ENDS
    elif field == "months" and value is None:
        ok = True
    elif isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        ok = False
    else:
        ok = (rule.low is None or value >= rule.low) and (rule.high is None or value <= rule.high) and (not rule.whole or float(value).is_integer())
    if ok:
        return None
    return RangeProblem(field, _shown(field, value), SIZE_WORDS[field], RANGE_WORDS.get(field, ZERO_OR_MORE))


def shock_from(answers: tuple[CardAnswer, ...]) -> Shock:
    """Last answer per field wins. keep_pct / 100 -> IncomeCut.keep_fraction, the same division the Shock and plan page does.
    Raises ValueError if months or after_ends are given without keep_pct."""
    last = {a.field: a.value for a in answers}
    cut = None
    if "keep_pct" in last:
        months = last.get("months")
        if isinstance(months, float) and months.is_integer():
            months = int(months)                 # 6.0 from a typed box; 2.5 stays and IncomeCut refuses it
        cut = IncomeCut(last["keep_pct"] / 100, months, last.get("after_ends", "no_income"))
    elif "months" in last or "after_ends" in last:
        raise ValueError("months and after_ends need keep_pct.")
    sizes = {f: last[f] for f in ("bills_increase_pct", "other_spending_change", "one_off_dollars", "one_off_spending_multiple") if f in last}
    return Shock(income_cut=cut, **sizes)
