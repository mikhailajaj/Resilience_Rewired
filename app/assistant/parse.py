"""Free text to a parse result, by docs/design/ux/chat_parser.md. Deterministic, never raises (ADR 0004)."""
import re
from dataclasses import replace

from .state import ASSUMED_MONTHS, FIELD_KIND, RULES, CardAnswer, ParseResult, check_size

_UNITS = {w: i for i, w in enumerate("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split(), 1)}
_TENS = {w: 10 * i for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split(), 2)}
_WORDS = {**_UNITS, **_TENS, "hundred": 100}
_SMALL = "|".join(w for w in _UNITS if _UNITS[w] < 10)
_WORD_NUM = (r"(?:(?:one[\s-]+)?hundred|(?:" + "|".join(_TENS) + r")(?:[\s-]+(?:" + _SMALL + r"))?|" + "|".join(sorted(_UNITS, key=len, reverse=True)) + r")\b")
_NUM = r"(?:\d+(?:\.\d+)?|\.\d+|" + _WORD_NUM + r")"
_NUMB = r"(?<![\w.])" + _NUM
_PCT = _NUMB + r"\s*(?:%|percent\b|per\s*cent\b)"

_MULT = re.compile(r"(?<![\w.])(?:(?P<n>" + _NUM + r")|an?)\s+(?:full\s+)?months?\s+of\s+(?:(?:their|his|her)\s+)?(?:(?:typical|usual|normal|monthly)\s+)?spending\b")
_AFTER = re.compile(r"\bthen\s+(?:(?:they|he|she)\s+)?(?:(?:is|are|go|goes)\s+)?back\s+to\s+work\b|\bthen\s+(?:their\s+)?income\s+returns\b")
_KEEP_BY = re.compile(r"\b(?:income|pay|paycheque|paycheck|salary|earnings|ei)\s+(?:(?:was|is|gets)\s+)?(?:drops?|dropped|falls?|fell|cuts?|cut|reduced|down)\s*(?P<how>to|by)?\s*(?P<pct>" + _PCT + r")?")
_KEEP_EI = re.compile(r"\b(?:ei|pays?|keeps?|keeping)\b(?:\s+(?:at|of|is|about|around|only))*\s*(?P<pct>" + _PCT + r")")
_KEEP_OF = re.compile(r"(?P<pct>" + _PCT + r")\s+of\s+(?:(?:their|his|her)\s+)?(?:(?:usual|normal|regular|typical)\s+)?(?:income|pay)\b")
_NO_INCOME = re.compile(r"\b(?:no|without)\s+(?:ei|income|pay|paycheque|paycheck)\b")
_MONTHS = re.compile(r"(?<![\w.])(?P<n>" + _NUM + r")[\s-]*months?\b")
_HALF_YEAR = re.compile(r"\bhalf[\s-]+(?:a[\s-]+)?year\b")
_YEARS = re.compile(r"(?<![\w.])(?:(?P<n>" + _NUM + r")|an?)[\s-]*years?\b")
_OPEN = re.compile(r"\buntil\s+it\s+runs\s+out\b|\bruns\s+out\b|\bno\s+end\b|\bopen[\s-]ended\b")

_PCT_RX = re.compile(r"(?P<n>" + _NUMB + r")\s*(?:%|percent\b|per\s*cent\b)")
_DOLLAR = re.compile(r"\$\s*(?P<a>\d+(?:\.\d+)?)\s*(?P<k>k\b)?|(?<![\w.])(?P<b>\d+(?:\.\d+)?)\s*dollars?\b")
_SPLIT = re.compile(r"\.(?=\s|$)|[;,!?()\n]|\band\b|\bbut\b|\bthen\b|\balso\b|\bplus\b|\bwhile\b")

_JOB_KW = re.compile(r"\blaid[\s-]?off\b|\blay[\s-]?offs?\b|\b(?:lose|loses|lost|losing)\s+(?:(?:their|his|her|the|a|my|your)\s+)?job\b|\bjob\s+loss\b|\bunemployed\b|\bfired\b|\bei\b")
_BILLS_KW = re.compile(r"\b(?:bills?|rent|utilities|utility|hydro)\b")
_REPAIR_KW = re.compile(r"\b(?:repairs?|furnace|roof|car|surprise\s+costs?|one[\s-]off)\b")
_UP = re.compile(r"\b(?:up|rise[sn]?|rising|increase[sd]?|increasing|higher)\b|\+")
_DOWN = re.compile(r"\b(?:down|drops?|dropped|less|lower|decrease[sd]?|cheaper|cut|falls?)\b")
_MONTH_NAME = re.compile(r"\b(?:january|february|march|april|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec)\b"
                         r"|\b(?:in|on|by|from|since|during|next|last|this|every|until|before|after)\s+may\b|\bmay\s+\d")
_NEGATION = re.compile(r"\bnot\b|n['’]t\b")
_FRACTION = re.compile(r"(?<![\w.$])(?:0?\.\d+|1\.0+)(?![\w.])")
_DIGIT = re.compile(r"\d")
_COMMAS = re.compile(r"(?<=\d),(?=\d{3}\b)")
_LONE = re.compile(r"\$?\s*(?P<n>\d+(?:\.\d+)?|\.\d+|" + _WORD_NUM + r")(?:\s*(?P<k>k))?(?:\s*(?:%|percent|per\s*cent|dollars?))?")

_ORDER = tuple(RULES)


def _word_value(s):
    total = 0
    for tok in re.split(r"[\s-]+", s):
        total = (total or 1) * 100 if tok == "hundred" else total + _WORDS[tok]
    return total


def _num(s):
    v = float(s) if _DIGIT.search(s) else _word_value(s)
    return int(v) if isinstance(v, float) and v.is_integer() and abs(v) < 1e15 else v


def _whole(v):
    return int(v) if isinstance(v, float) and v.is_integer() and abs(v) < 1e15 else v


def _blank(s, spans):
    if not spans:
        return s
    out, last = [], 0
    for a, b in sorted(spans):
        out += [s[last:a], " " * (b - a)]
        last = b
    out.append(s[last:])
    return "".join(out)


def _take(rx, s):
    ms = list(rx.finditer(s))
    return ms, _blank(s, [m.span() for m in ms])


def _parse(text):
    shown = text.strip()
    t0 = _COMMAS.sub("", text.lower())
    found = {f: [] for f in _ORDER}              # field -> [(value, typed)]
    u4 = False
    t = t0

    ms, t = _take(_MULT, t)
    for m in ms:
        found["one_off_spending_multiple"].append((_num(m["n"]) if m["n"] else 1, m.group(0)))
    ms, t = _take(_AFTER, t)
    after = bool(ms)

    for rx in (_KEEP_BY, _KEEP_EI, _KEEP_OF):
        ms, t = _take(rx, t)
        for m in ms:
            if not m["pct"]:
                continue
            n = _num(_PCT_RX.search(m["pct"])["n"])
            if rx is _KEEP_BY and m["how"] is None:
                u4 = True
            elif rx is _KEEP_BY and m["how"] == "by":
                found["keep_pct"].append((_whole(round(100 - n, 9)), m["pct"].strip()))
            else:
                found["keep_pct"].append((n, m["pct"].strip()))
    ms, t = _take(_NO_INCOME, t)
    found["keep_pct"] += [(0, m.group(0)) for m in ms]
    keep_found = bool(found["keep_pct"]) or u4

    ms, t = _take(_HALF_YEAR, t)
    found["months"] += [(6, m.group(0)) for m in ms]
    ms, t = _take(_YEARS, t)
    found["months"] += [(_whole(_num(m["n"]) * 12) if m["n"] else 12, m.group(0)) for m in ms]
    ms, t = _take(_MONTHS, t)
    found["months"] += [(_num(m["n"]), m.group(0)) for m in ms]
    ms, t = _take(_OPEN, t)
    found["months"] += [(None, m.group(0)) for m in ms]

    job_kind = bool(_JOB_KW.search(t0)) or keep_found
    stray = False
    if not job_kind:
        stray = any(v is not None for v, _ in found["months"])
        found["months"] = []
        after = False
    if after:
        found["after_ends"].append(("income_returns", "then back to work"))

    bills_kind = repair_kind = bool(found["one_off_spending_multiple"])
    bills_kind = False
    rests = []
    for clause in _SPLIT.split(t):
        if _REPAIR_KW.search(clause):
            repair_kind = True
        bills_up = False
        if _BILLS_KW.search(clause):
            if _DOWN.search(clause):
                u4 = bills_kind = True
            elif _UP.search(clause):
                bills_up = bills_kind = True
        spans = []
        if bills_up:
            for m in _PCT_RX.finditer(clause):
                found["bills_increase_pct"].append((_num(m["n"]), m.group(0).strip()))
                spans.append(m.span())
        if bills_up or _REPAIR_KW.search(clause):
            for m in _DOLLAR.finditer(clause):
                v = float(m["a"] or m["b"]) * (1000 if m["k"] else 1)
                field = "one_off_dollars" if _REPAIR_KW.search(clause) else "other_spending_change"
                found[field].append((_whole(round(v, 6)), m.group(0).strip()))
                spans.append(m.span())
        rests.append(_blank(clause, spans))
    rest = " ".join(rests)

    kind = job_kind or bills_kind or repair_kind
    negated = kind and bool(_NEGATION.search(t0))
    month_named = kind and bool(_MONTH_NAME.search(t0))
    sized_twice = any(len(found[f]) > 1 for f in _ORDER) or (found["bills_increase_pct"] and found["other_spending_change"]) \
        or (found["one_off_spending_multiple"] and found["one_off_dollars"])

    if month_named or negated:
        return ParseResult("unsure", unsure="U6", month_named=month_named)
    if u4:
        return ParseResult("unsure", unsure="U4")
    if kind and _FRACTION.search(rest):
        return ParseResult("unsure", unsure="U5")
    if sized_twice:
        return ParseResult("unsure", unsure="U3")
    if not kind:
        return ParseResult("unsure", unsure="U1")
    if stray or _DIGIT.search(rest):
        return ParseResult("unsure", unsure="U2")

    for f in _ORDER:
        for v, typed in found[f][:1]:
            problem = check_size(f, v)
            if problem:
                return ParseResult("out_of_range", problem=replace(problem, value=typed))

    assumed = job_kind and (bills_kind or repair_kind) and not found["months"]
    if assumed:
        found["months"].append((ASSUMED_MONTHS, "assumed"))
    missing = []
    if job_kind:
        missing += [f for f in ("keep_pct", "months") if not found[f]]
    if bills_kind and not (found["bills_increase_pct"] or found["other_spending_change"]):
        missing.append("bills_increase_pct")
    if repair_kind and not (found["one_off_spending_multiple"] or found["one_off_dollars"]):
        missing.append("one_off_spending_multiple")
    missing.sort(key=_ORDER.index)
    answers = tuple(CardAnswer(-1, FIELD_KIND[f], f, found[f][0][0], RULES[f].unit, "parsed", shown) if not (assumed and f == "months")
                    else CardAnswer(-1, "job", f, ASSUMED_MONTHS, RULES[f].unit, "assumed", f"{ASSUMED_MONTHS} months (assumed)")
                    for f in _ORDER if found[f])
    return ParseResult("partial" if missing else "ok", answers=answers, missing=tuple(missing))


def parse(text: str) -> ParseResult:
    try:
        return _parse(text if isinstance(text, str) else "")
    except Exception:
        return ParseResult("unsure", unsure="U1")


def read_number(text: str) -> float | None:
    try:
        s = _COMMAS.sub("", text.strip().lower())
        m = _LONE.fullmatch(s)
        if not m:
            return None
        v = float(_num(m["n"])) * (1000 if m["k"] else 1)
        return v if v == v and abs(v) != float("inf") else None
    except Exception:
        return None
