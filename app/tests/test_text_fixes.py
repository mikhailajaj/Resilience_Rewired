"""Wording fixes R1, R4, R10, R11, R14, R19, R20, R21 and D4, D5, D6, D7, D12 on real accounts: whole sentences, no number computed here."""
import pandas as pd
import pytest

from app.engine import apply_shock, get_preset, get_profile, make_plan
from app.ui import text

IDS = sorted(pd.read_csv(__import__("pathlib").Path(__file__).resolve().parents[2] / "data" / "accounts.csv").account_id)


def run(account, preset="job_loss_ei", through=None, **overrides):
    shock = get_preset(preset, **overrides)
    through = through if through is not None else (shock.income_cut.months if shock.income_cut else None)
    return apply_shock(account, shock, through_months=through)


def test_r1_d1_a_shortfall_under_a_tenth_of_a_month_says_so():
    """R1/D1: 21271 on EI runs out in month 6, 0.0 months short."""
    assert text.verdict(run(21271)).sentence == "With income at 55% for 6 months, the money runs out in month 6, less than 0.1 months short."


def test_r1_no_account_says_about_0_months_short():
    for a in IDS:
        for keep in (0.55, 0.4, 0.9):
            sentence = text.verdict(run(a, keep_fraction=keep)).sentence
            assert "about 0 months short" not in sentence and "about 0.0 months short" not in sentence, (a, keep, sentence)


@pytest.mark.parametrize("pct", [15, 50, 100])
def test_r4_an_unchanged_runway_is_not_down_from_no_shortfall(pct):
    """R4: 20111 with bills up is unchanged at 7.8 months."""
    sentence = text.verdict(run(20111, "bills_up", bills_increase_pct=pct)).sentence
    assert sentence == "After this, the runway is unchanged at 7.8 months."
    assert "down from No shortfall" not in sentence


def test_r4_in_sentence_lowers_only_the_first_letter():
    assert text.in_sentence("No shortfall (120+)") == "no shortfall (120+)"


def test_r10_a_whole_month_is_singular_in_every_sentence_that_carries_one():
    """R10/NEW-COPY-9: length 1 and target 1."""
    assert text.months_word(1) == "1 month" and text.months_word(2) == "2 months" and text.months_word(1.5) == "1.5 months"
    r = run(20111, months=1)
    assert text.verdict(r).sentence.startswith("With income at 55% for 1 month, the money ")
    plan = make_plan(21101, get_preset("job_loss_ei", months=1), through_months=1, target_months=1.0)
    goal = text.goal_lines(plan)
    assert "To have 1 month of spending (**$19,611**) saved" in goal[1] and text.backup_lines(plan) == ["No cuts needed: the buffer lasts the full 1 month."]
    assert not any("1 months" in line for line in goal)


def test_r11_a_zero_runway_in_a_sentence_says_under_a_tenth():
    """R11: 49637 buffer $114 on $4,032 a month."""
    assert text.summary_line(get_profile(49637)) == (
        "Customer 49637 brings in about $154 a month and spends about $4,032. The buffer is $114, so it would last under 0.1 months.")


def test_r21_the_label_keeps_0_0_months_while_the_sentence_says_under():
    """R21: 32179 at EI 40%."""
    r = run(32179, keep_fraction=0.4)
    assert r.runway.label == "0.0 months"
    assert text.verdict(r).second_line == "The judges' runway is under 0.1 months."
    assert text.runway_words(r.runway) == "under 0.1 months"


def test_new_copy_14_and_15_when_money_in_and_out_are_both_zero():
    p = get_profile(31500)
    assert p.I == 0 and p.S == 0
    assert text.summary_line(p) == "Customer 31500 has almost no activity: typical money in and spending are both $0. The buffer is $7,509."
    assert text.verdict(run(31500)).sentence == "No money in or out in a typical month, so there is nothing for the buffer to cover."


def test_r14_new_copy_16_income_returns_assumption():
    r = run(20111, after_ends="income_returns", months=3, through=6)
    assert text.assumption_line(r) == "After month 3 we assume income returns to its typical level."
    r = run(20111, months=3, through=6)
    assert text.assumption_line(r) == "After month 3 we assume no income. A benefit ending doesn't mean a new job has started."


def test_r19_no_regular_income_is_not_described_as_slightly_more():
    """R19: 49900 has no money in."""
    line = text.summary_line(get_profile(49900))
    assert line == "Customer 49900 has no regular money in and spends about $63 a month. The buffer is $9,251, so it would last 120.0 months."
    assert "slightly more" not in line


def test_r20_a_one_off_equal_to_the_buffer_uses_up_the_whole_buffer():
    p = get_profile(20111)
    sentence = text.verdict(run(20111, "no_shock", one_off_dollars=p.B)).sentence
    assert sentence == "The one-off cost of $17,612 uses up the whole buffer of $17,612. Nothing is left to live on."


def test_d5_ac6_a_runway_at_the_cap_keeps_its_number():
    line = text.summary_line(get_profile(20134))
    assert line == "Customer 20134 spends slightly more than comes in. The buffer of $16,599 would last 120.0 months."
    assert "No shortfall" not in line and "120 months or more" not in line


def test_d4_r6_the_one_off_line_in_each_of_its_forms():
    assert text.oneoff_line(run(20111, "no_shock")) is None
    assert text.oneoff_line(run(20111, "no_shock", one_off_dollars=5000)) == "One-off cost: $5,000."
    assert text.oneoff_line(run(20111, "furnace_repair")) == "One-off cost: $8,600, 1 month of typical spending before the shock ($8,600 a month)."
    assert text.oneoff_line(run(20111, "no_shock", one_off_dollars=5000, one_off_spending_multiple=2)) == (
        "One-off cost: $22,199: $5,000 plus 2 months of typical spending before the shock ($8,600 a month).")


def test_d6_the_after_line_names_money_in_and_spending_after_the_shock():
    assert text.after_line(run(20111, "furnace_repair")) == "After the shock: money in $6,339 a month, spending $8,600 a month."


def test_d7_the_headline_goal_line_leads_then_the_judges_typical_month():
    lines = text.goal_lines(make_plan(20111, get_preset("no_shock")))
    assert lines[0] == ("Over the last 12 months the balance changed by -$748 a month (ours), so at that pace the fund isn't reached. "
                        "Saving starts with spending $748 a month less.")
    assert lines[1].startswith("On the judges' typical month (-$2,260 a month): ")


def test_backup_lines_loan_ending_inside_the_length_applies():
    """P.loan_backup: 20916 on EI, the loan ends in month 3 and the money still runs out in month 4."""
    plan = make_plan(20916, get_preset("job_loss_ei"), through_months=6)
    assert plan.backup.loan_end.reason == "applies"
    lines = text.backup_lines(plan)
    assert lines[-2:] == ["Counting the loan ending in month 3, the monthly gap falls by $3,545 from then (ours).", "They still run out in month 4 (ours)."]


def test_backup_lines_loan_not_in_typical_spending_new_copy_22():
    plan = make_plan(20208, get_preset("job_loss_ei"), through_months=6)
    assert plan.backup.loan_end.reason == "not_in_spending"
    assert text.backup_lines(plan)[-1] == (
        "The loan payment of $1,355 a month isn't in the judges' typical spending yet, because the loan started recently, "
        "so the judges' figure doesn't rise when it ends in month 24 (ours).")
