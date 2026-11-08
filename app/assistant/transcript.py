"""The transcript as Markdown, from stored records only (ADR 0005, design section 4.5)."""
from app.ui import text

from .state import ChatState

NONE_YET = "None yet."


def _cell(value) -> str:
    return "" if value is None else str(value).replace("|", "\\|").replace("\n", " ")


def _table(header, rows):
    if not rows:
        return [NONE_YET, ""]
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(":--" for _ in header) + " |"]
    out += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return out + [""]


def _money(value):
    return "" if value is None else text.money(value)


def _section(account_id, messages, answers, outputs):
    lines = [f"## Customer {account_id}", "", "### Conversation", ""]
    if not messages:
        lines += [NONE_YET, ""]
    for m in messages:
        lines += [f"**{'Assistant' if m.role == 'assistant' else 'You'}:**", ""]
        for line in m.lines:
            lines += [line, ""]
    lines += ["### Card answers", ""]
    lines += _table(("Turn", "Kind", "Field", "Value", "Unit", "Source", "Shown"),
                    [(a.turn, a.kind, a.field, a.value, a.unit, a.source, a.shown) for a in answers])
    lines += ["### Engine outputs", ""]
    lines += _table(("Turn", "Call", "Verdict case", "Runway before -> after", "Gap before -> after", "Fact codes", "Plan states"),
                    [(o.turn, o.call, o.verdict_case, f"{o.runway_before or ''} -> {o.runway_after or ''}",
                      f"{_money(o.gap_before)} -> {_money(o.gap_after)}", ", ".join(o.fact_codes),
                      ", ".join(f"{k}: {v}" for k, v in (("goal", o.goal_state), ("backup", o.backup_state)) if v))
                     for o in outputs])
    return lines


def to_markdown(state: ChatState) -> str:
    lines = ["# Chat transcript", ""]
    for s in state.archive:
        lines += _section(s.account_id, s.messages, s.answers, s.outputs)
    if state.account_id is not None:
        lines += _section(state.account_id, state.messages, state.answers, state.outputs)
    if len(lines) == 2:
        lines += ["No customer yet.", ""]
    return "\n".join(lines)


def file_name(state: ChatState) -> str:
    return f"chat_transcript_{state.account_id}.md"
