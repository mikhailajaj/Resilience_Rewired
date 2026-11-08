"""R13: what an account ID may look like when typed or pasted."""
import pytest

from app.engine import InvalidAccountIdError, account_flows, get_profile, loan_end, make_plan, monthly_history, saving_rates
from app.engine.profile import parse_account_id


@pytest.mark.parametrize("value", ["20,111", " 20111 ", "20111.0", 20111.0, "20111", 20111, "20111.00"])
def test_R13_accepted_forms(value):
    assert parse_account_id(value) == 20111


@pytest.mark.parametrize("value", ["20,11", "2,0111", "20111.5", "1e4", "-20111", "", True, False, "abc", "2 0111", "20,1111", None, "٢٠١١١", "20111.0.0"])
def test_R13_not_digits(value):
    with pytest.raises(InvalidAccountIdError) as e:
        parse_account_id(value)
    assert e.value.reason == "not_digits"


@pytest.mark.parametrize("value", ["99,999", "99999", 99999, "0", "99999.0", "9" * 40])
def test_R13_not_found(value):
    with pytest.raises(InvalidAccountIdError) as e:
        parse_account_id(value)
    assert e.value.reason == "not_found"


def test_R13_the_message_is_short_and_keeps_the_raw_value():
    with pytest.raises(InvalidAccountIdError) as e:
        parse_account_id("x" * 500)
    assert len(str(e.value)) < 200 and e.value.value == "x" * 500


@pytest.mark.parametrize("call", [get_profile, account_flows, loan_end, saving_rates, make_plan, monthly_history])
def test_R13_every_public_entry_parses_the_id(call):
    call("20,111")
    with pytest.raises(InvalidAccountIdError):
        call("20,11")
