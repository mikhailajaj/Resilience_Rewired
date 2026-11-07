"""The README runway rule, on plain numbers."""
import pytest

from app.engine.formulas import runway_from


@pytest.mark.parametrize("buffer_left,gap,state,months,label", [
    (0, 100, "no_buffer", 0.0, "0 months"),
    (-5, -100, "no_buffer", 0.0, "0 months"),          # buffer is tested before the gap
    (100, 0, "no_shortfall", None, "No shortfall (120+)"),
    (100, -1, "no_shortfall", None, "No shortfall (120+)"),
    (100, 30, "months", 3.3, "3.3 months"),
    (1_000_000, 1, "months", 120.0, "120.0 months"),   # the cap
    (0.01, 1000, "months", 0.0, "0.0 months"),         # rounds down, still not the no-buffer case
])
def test_runway_rule(buffer_left, gap, state, months, label):
    r = runway_from(buffer_left, gap)
    assert (r.state, r.months, r.label) == (state, months, label)
