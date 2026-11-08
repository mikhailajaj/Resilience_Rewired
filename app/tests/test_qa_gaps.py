"""QA gaps closed in the engine: R16 (capped income to the cent), R17 (through_months reaches apply_shock), R22 (money rounding)."""
import pytest

import app.engine.plan as plan_module
from app.engine.shock import duration_path, shock_gaps
from app.engine import IncomeCut, Shock, apply_shock, get_preset, get_profile, make_plan
from app.engine.formulas import money

CAP = Shock(IncomeCut(0.30, 6, ei_weekly_max=729))


def test_R16_20111_keeps_30_percent_to_the_cent():
    capped = apply_shock(20111, CAP).ei_capped
    assert capped.income_after == pytest.approx(1901.82, abs=0.005)
    assert capped.income_after == pytest.approx(0.30 * get_profile(20111).I, abs=1e-9)


def test_R16_flat_below_the_cap_the_capped_figure_equals_the_flat_one():
    for a in (20111, 20176, 32078):
        r = apply_shock(a, CAP)
        assert r.ei_capped.reason == "max_not_reached" and not r.ei_capped.max_applied
        assert r.ei_capped.income_after == r.income_after
        assert r.ei_capped.runway == r.runway


@pytest.mark.parametrize("account", [95548, 66505])
def test_R16_above_the_cap_the_capped_income_is_the_monthly_maximum_not_the_flat_share(account):
    r = apply_shock(account, CAP)
    c = r.ei_capped
    assert c.max_applied and c.reason == "max_applied"
    assert c.income_after == pytest.approx(729 * 52 / 12, abs=0.005) == pytest.approx(c.monthly_max)
    assert c.income_after < r.income_after
    assert c.income_after != pytest.approx(0.30 * get_profile(account).I)


def test_R16_the_capped_backup_is_built_from_the_capped_income():
    plan = make_plan(95548, CAP, through_months=6)
    c = apply_shock(95548, CAP, through_months=6).ei_capped
    assert plan.backup.income_basis == "flat" and plan.backup_capped.income_basis == "ei_weekly_max"
    assert plan.backup_capped.runway_before == c.runway
    assert plan.backup_capped.cut_to_close_gap == pytest.approx(max(c.gap, 0.0))
    assert plan.backup_capped.runway_before != plan.backup.runway_before
    assert make_plan(95548, get_preset("job_loss_ei"), through_months=6).backup_capped is None


@pytest.mark.parametrize("account", [95548, 66505])
def test_R16_the_capped_backup_cut_keeps_the_capped_balance_at_zero(account):
    shock = Shock(IncomeCut(0.30, 6, ei_weekly_max=300))
    r = apply_shock(account, shock, through_months=6)
    backup = make_plan(account, shock, through_months=6).backup_capped
    during, after, benefit = shock_gaps(get_profile(account), shock, r.spending_after, r.ei_capped.income_after)
    assert backup.cut_to_last is not None and backup.cut_to_last > 0
    path = duration_path(r.buffer_left, during - backup.cut_to_last, after - backup.cut_to_last, benefit, 6, "no_income")
    assert -1e-6 <= path.lowest_balance < 0.01


@pytest.fixture
def through_spy(monkeypatch):
    seen = []
    real = plan_module.apply_shock

    def spy(account_id, shock=None, *, through_months=None):
        seen.append(through_months)
        return real(account_id, shock, through_months=through_months)

    monkeypatch.setattr(plan_module, "apply_shock", spy)
    return seen


def test_R17_through_months_reaches_apply_shock_unchanged(through_spy):
    make_plan(20111, get_preset("job_loss_ei"), through_months=6)
    assert through_spy == [6]


def test_R17_none_stays_none(through_spy):
    make_plan(20111, get_preset("job_loss_ei"))
    assert through_spy == [None]


def test_R17_the_capped_pass_gets_the_same_value(through_spy):
    make_plan(95548, CAP, through_months=9)
    assert through_spy == [9, 9]


def test_R17_a_different_length_changes_the_months_asked():
    assert make_plan(20111, get_preset("job_loss_ei"), through_months=9).backup.through_months == 9
    assert make_plan(20111, get_preset("job_loss_ei")).backup.through_months == 6


@pytest.mark.parametrize("value,text", [(-0.3, "$0"), (-0.5, "$0"), (-0.49, "$0"), (-1, "-$1"), (-1.4, "-$1"), (1234.4, "$1,234"),
                                        (0, "$0"), (1234.5, "$1,234"), (-1234.6, "-$1,235")])
def test_R22_money_never_prints_minus_zero(value, text):
    assert money(value) == text
