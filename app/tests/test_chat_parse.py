"""The guided chat's free-text parser (J4.2): PT-01..PT-25, the cheatsheet examples, read_number, the size rules, and a fuzz run (RU-15, RU-17, RU-22)."""
import time

import pytest

from app.assistant.parse import parse, read_number
from app.assistant.state import check_size, shock_from, CardAnswer
from app.engine import IncomeCut, Shock
from app.ui import cheatsheet

IC = IncomeCut

# (id, text, status, shock if ok, missing if partial, unsure code, month_named, problem field)
PT = [
    ("PT-01", "laid off, EI 55% for 6 months", "ok", Shock(income_cut=IC(0.55, 6)), (), None, False, None),
    ("PT-02", "laid off, EI 55% for 6 months and bills up 15%", "ok", Shock(income_cut=IC(0.55, 6), bills_increase_pct=15), (), None, False, None),
    ("PT-03", "The furnace dies, and the repair costs a full month of their typical spending.", "ok", Shock(one_off_spending_multiple=1), (), None, False, None),
    ("PT-04", "They lose their job (EI at 55%) and their household bills go up 15% in the same month.", "ok", Shock(income_cut=IC(0.55, 6), bills_increase_pct=15), (), None, False, None),
    ("PT-05", "Rent or household bills go up 15%.", "ok", Shock(bills_increase_pct=15), (), None, False, None),
    ("PT-06", "rent up $300 a month", "ok", Shock(other_spending_change=300), (), None, False, None),
    ("PT-07", "car repair $2,500", "ok", Shock(one_off_dollars=2500), (), None, False, None),
    ("PT-08", "roof repair $1.5k", "ok", Shock(one_off_dollars=1500), (), None, False, None),
    ("PT-09", "EI 57% for 12 months", "ok", Shock(income_cut=IC(0.57, 12)), (), None, False, None),
    ("PT-10", "laid off for a year, EI 55%", "ok", Shock(income_cut=IC(0.55, 12)), (), None, False, None),
    ("PT-11", "laid off, EI 55% until it runs out", "ok", Shock(income_cut=IC(0.55, None)), (), None, False, None),
    ("PT-12", "laid off", "partial", None, ("keep_pct", "months"), None, False, None),
    ("PT-13", "income drops to 70% for three months", "ok", Shock(income_cut=IC(0.7, 3)), (), None, False, None),
    ("PT-14", "income cut by 30% for 3 months", "ok", Shock(income_cut=IC(0.7, 3)), (), None, False, None),
    ("PT-15", "income drops 30%", "unsure", None, (), "U4", False, None),
    ("PT-16", "EI 150% for 6 months", "out_of_range", None, (), None, False, "keep_pct"),
    ("PT-17", "laid off, EI 55% for 200 months", "out_of_range", None, (), None, False, "months"),
    ("PT-18", "laid off, EI 55% for 2.5 months", "out_of_range", None, (), None, False, "months"),
    ("PT-19", "laid off, no EI, for 3 months", "ok", Shock(income_cut=IC(0, 3)), (), None, False, None),
    ("PT-20", "laid off, EI 55% for 6 months, then back to work", "ok", Shock(income_cut=IC(0.55, 6, after_ends="income_returns")), (), None, False, None),
    ("PT-21", "bills down 10%", "unsure", None, (), "U4", False, None),
    ("PT-22", "the furnace dies in January", "unsure", None, (), "U6", True, None),
    ("PT-23", "bills up 15% and rent up 10%", "unsure", None, (), "U3", False, None),
    ("PT-24", "EI 0.55 for 6 months", "unsure", None, (), "U5", False, None),
    ("PT-25", "what if they win the lottery", "unsure", None, (), "U1", False, None),
]


@pytest.mark.parametrize("pid,text,status,shock,missing,unsure,month_named,problem_field", PT, ids=[r[0] for r in PT])
def test_pt_rows(pid, text, status, shock, missing, unsure, month_named, problem_field):
    r = parse(text)
    assert r.status == status
    assert r.unsure == unsure
    assert r.month_named == month_named
    if status == "ok":
        assert r.shock == shock
        assert r.missing == ()
    else:
        assert r.shock is None
    if status == "partial":
        assert r.missing == missing
    if status == "out_of_range":
        assert r.problem.field == problem_field
    else:
        assert r.problem is None


def test_pt04_assumes_six_months_and_says_so_in_the_answer():
    r = parse(PT[3][1])
    assert [(a.field, a.value, a.source) for a in r.answers] == [("keep_pct", 55, "parsed"), ("months", 6, "assumed"), ("bills_increase_pct", 15, "parsed")]
    assert r.answers[1].shown == "6 months (assumed)" and r.answers[1].kind == "job"


def test_pt12_partial_has_no_answers():
    assert parse("laid off").answers == ()


def test_keep_is_a_percent_not_a_fraction_and_cut_by_30_is_70():
    assert parse("EI 55% for 6 months").answers[0].value == 55
    cut = parse("income cut by 30% for 3 months")
    assert [(a.field, a.value) for a in cut.answers] == [("keep_pct", 70), ("months", 3)]


def test_answers_are_parsed_turn_minus_one_with_unit_and_typed_text():
    text = "  laid off, EI 55% for 6 months  "
    r = parse(text)
    assert [a.field for a in r.answers] == ["keep_pct", "months"]
    for a in r.answers:
        assert (a.turn, a.source, a.shown) == (-1, "parsed", text.strip())
    assert [a.unit for a in r.answers] == ["%", "months"]
    assert [a.kind for a in r.answers] == ["job", "job"]
    assert isinstance(r.answers[1].value, int)


def test_out_of_range_problem_shows_the_size_as_typed():
    assert parse("EI 150% for 6 months").problem.value == "150%"
    assert parse("laid off, EI 55% for 200 months").problem.value == "200 months"
    assert parse("laid off, EI 55% for 2.5 months").problem.value == "2.5 months"


def test_unsure_wins_over_out_of_range_and_partial():
    assert parse("EI 150% and bills down 10%").status == "unsure"
    assert parse("laid off in March, EI 150%").unsure == "U6"
    assert parse("laid off, EI 150%").status == "out_of_range"


def test_u6_negation_and_no_ei_is_not_a_negation():
    r = parse("they did not lose their job, EI 55% for 6 months")
    assert (r.status, r.unsure, r.month_named) == ("unsure", "U6", False)
    assert parse("they didn't lose their job").unsure == "U6"
    assert parse("laid off, no EI, for 3 months").status == "ok"


def test_u2_a_number_no_rule_used():
    assert parse("laid off, EI 55% for 6 months in 2024").unsure == "U2"
    assert parse("bills up 15% for 6 months").unsure == "U2"


def test_u3_one_kind_sized_twice():
    assert parse("laid off, EI 55% and EI 40% for 6 months").unsure == "U3"
    assert parse("furnace repair $500 and car repair $900").unsure == "U3"


def test_pt04_month_without_number_is_not_a_length_and_not_u6():
    r = parse("laid off, EI 55%, bills up 15% in the same month")
    assert (r.status, r.missing, r.unsure) == ("ok", (), None)
    assert [a.source for a in r.answers if a.field == "months"] == ["assumed"]


def test_word_numbers_and_percent_words():
    assert parse("laid off, EI 55 percent for twelve months").shock == Shock(income_cut=IC(0.55, 12))
    assert parse("laid off, EI 55% for one month").shock == Shock(income_cut=IC(0.55, 1))
    assert parse("furnace repair costs two months of spending").shock == Shock(one_off_spending_multiple=2)


@pytest.mark.parametrize("example,expected", [(ex, sh) for _, _, ex, sh in cheatsheet.TEMPLATES])
def test_every_cheatsheet_example_parses_to_its_shock(example, expected):
    r = parse(example)
    assert r.status == "ok", r
    assert r.shock == expected


@pytest.mark.parametrize("text,value", [
    ("55", 55), ("55%", 55), ("$2,500", 2500), ("1.5k", 1500), ("$1.5k", 1500), ("six", 6),
    ("  12 ", 12), ("55 percent", 55), ("2.5", 2.5),
])
def test_read_number_reads_a_lone_size(text, value):
    assert read_number(text) == value


@pytest.mark.parametrize("text", ["abc", "", "   ", "55 and 6", "55 6", "%", "$", "six months and seven", "1e5x"])
def test_read_number_refuses_anything_else(text):
    assert read_number(text) is None


@pytest.mark.parametrize("field,value,ok", [
    ("keep_pct", 0, True), ("keep_pct", 100, True), ("keep_pct", 100.01, False), ("keep_pct", -1, False),
    ("months", 1, True), ("months", 120, True), ("months", 121, False), ("months", 0, False), ("months", 2.5, False), ("months", None, True),
])
def test_check_size_edges(field, value, ok):
    assert (check_size(field, value) is None) is ok


def test_shock_from_keep_55_is_a_fraction():
    a = CardAnswer(-1, "job", "keep_pct", 55, "%", "parsed", "55%")
    assert shock_from((a,)).income_cut.keep_fraction == 55 / 100


def _fuzz_strings():
    pt_texts = [r[1] for r in PT] + [ex for _, _, ex, _ in cheatsheet.TEMPLATES]
    out = ["", " ", "\n\t ", "😀", "😀 laid off 😀", "0", "9" * 500, "!?.,;:" * 40, "%$" * 200, "$" * 50, "%" * 50, "-" * 100,
           "1,2,3,4,5", "$1,5k", ".", "..5", "5.", "1e999", "nan", "inf", "\x00", "ＥＩ ５５％", "laid off, EI " + "9" * 400 + "%",
           "bills up " + "9" * 400 + "%", "furnace repair $" + "9" * 400 + "k", "laid off for " + "9" * 400 + " months"]
    for t in pt_texts:
        out += [t[::-1], t + " " + t, t.upper(), t + t, t.replace(" ", "")]
    # pad to 200+ with deterministic mixes
    pieces = [r[1] for r in PT] + ["%", "$", "k", "0.5", "and", "then", "months", "EI", "bills up", "not", "January", "  "]
    for i in range(120):
        out.append(" ".join(pieces[(i * 7 + j * 3) % len(pieces)] for j in range(1 + i % 6)))
    return out


FUZZ = _fuzz_strings()


def test_fuzz_has_at_least_200_strings():
    assert len(FUZZ) >= 200


@pytest.mark.parametrize("text", FUZZ)
def test_fuzz_never_raises_and_ok_answers_pass_check_size(text):
    r = parse(text)
    assert r.status in ("ok", "partial", "out_of_range", "unsure")
    if r.status == "ok":
        assert r.answers
        for a in r.answers:
            assert check_size(a.field, a.value) is None
        assert r.shock is not None
    if r.status == "unsure":
        assert r.unsure in ("U1", "U2", "U3", "U4", "U5", "U6")
    if r.status == "out_of_range":
        assert r.problem is not None
    read_number(text)


@pytest.mark.parametrize("big", [
    "a" * 10_000, "laid off, EI 55% for 6 months and bills up 15% " * 220, "1 " * 5_000, " " * 10_000, "1" + " " * 10_000 + "months",
    "-" * 10_000, "1-" * 5_000, "$" * 10_000, "%$" * 5_000, "9" * 10_000, "ei " * 3_000, "one " * 2_500, "😀" * 10_000, ".5" * 5_000,
])
def test_a_10kb_string_parses_in_under_50ms(big):
    start = time.perf_counter()
    parse(big)
    read_number(big)
    assert time.perf_counter() - start < 0.05


# --- J5.WP-C: number words, half a year, assumed length (R5, D2, ADR 0010) -------------------------------------------

@pytest.mark.parametrize("pid,text,shock", [
    ("NEW-PARSER-1", "laid off, EI 55% for half a year", Shock(income_cut=IC(0.55, 6))),
    ("NEW-PARSER-2", "EI pays 55% for half a year", Shock(income_cut=IC(0.55, 6))),
    ("NEW-PARSER-3", "bills up fifteen percent", Shock(bills_increase_pct=15)),
    ("NEW-PARSER-4", "laid off, EI fifty-five percent for twenty months", Shock(income_cut=IC(0.55, 20))),
    ("NEW-PARSER-5", "laid off, EI 55% for a year and bills up twenty percent", Shock(income_cut=IC(0.55, 12), bills_increase_pct=20)),
    ("R5-half-year", "laid off, EI 55% for a half-year", Shock(income_cut=IC(0.55, 6))),
    ("R5-compound", "laid off, EI fifty five percent for ninety months", Shock(income_cut=IC(0.55, 90))),
])
def test_new_parser_rows(pid, text, shock):
    r = parse(text)
    assert (r.status, r.shock) == ("ok", shock), pid


def test_new_parser_6_repair_stays_partial_and_the_length_stays_assumed():
    r = parse("laid off and the furnace dies, EI 55%")
    assert (r.status, r.missing) == ("partial", ("one_off_spending_multiple",))
    assert [(a.field, a.value, a.source) for a in r.answers] == [("keep_pct", 55, "parsed"), ("months", 6, "assumed")]


def test_d2_a_stated_length_is_never_assumed_and_a_bare_laid_off_still_asks():
    stated = parse("laid off, EI 55% for 3 months and bills up 15%")
    assert {a.source for a in stated.answers} == {"parsed"}
    r = parse("laid off")
    assert (r.status, r.missing, r.answers) == ("partial", ("keep_pct", "months"), ())
    assert parse("laid off, no EI, and bills up 10%").shock == Shock(income_cut=IC(0, 6), bills_increase_pct=10)


def test_r5_read_number_words():
    assert [read_number(w) for w in ("fifteen", "twenty", "fifty-five", "fifty five", "ninety", "hundred")] == [15, 20, 55, 55, 90, 100]
    assert read_number("thirteen") == 13 and read_number("one hundred") == 100


def test_r5_half_a_year_alone_is_not_a_length_without_a_job_kind():
    assert parse("half a year").status == "unsure"
