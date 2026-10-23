"""B8: post-gap events cannot cross inclusive deadlines (strategy-ny-indices.md › Rules)."""

import pytest
from test_setup_steps import (
    BASE,
    FVG_A,
    LONG,
    M5,
    bos,
    drive,
    harness,
    minute,
    zone,
)

from backtester.strategy.ny_index_sweep.setup import Step


@pytest.mark.parametrize("arrival,accepted", [(50, True), (55, True), (60, False)])
def test_setup_bos_deadline_inclusive_even_after_gap(arrival, accepted):
    events = {minute(arrival): [bos(LONG, 100.3, arrival // 5 - 1, minute(arrival))]}
    m1, frames, setup = harness(setup_events=events)
    # No update at the deadline unless that is the event's arrival.
    drive(m1, frames, setup, until=minute(49))
    drive(m1, frames, setup, after=minute(arrival - 1), until=minute(arrival))
    assert (setup.step is Step.BOS) is accepted
    if not accepted:
        assert setup.step is Step.DONE and setup.bos is None
        assert setup.ended == "no setup-TF BoS in time"


@pytest.mark.parametrize("arrival,accepted", [(129, True), (130, True), (132, False)])
def test_tap_deadline_inclusive_even_after_gap(arrival, accepted):
    overrides = {0: BASE[0], arrival - 1: (99.5, 99.6, 99.1, 99.5)}
    m1, frames, setup = harness(overrides, entry_events={})
    drive(m1, frames, setup, until=minute(128))
    assert setup.step is Step.BOS
    drive(m1, frames, setup, after=minute(arrival - 1), until=minute(arrival))
    assert (setup.step is Step.TAPPED) is accepted
    if accepted:
        assert setup.z3 == FVG_A and setup.tap_at == minute(arrival)
    else:
        assert setup.step is Step.DONE and setup.tap_at is None
        assert setup.ended == "3rd confluence not tapped in time"


def test_deeper_wick_after_gap_starts_new_sweep_deadline():
    overrides = {**BASE, 59: (99.0, 99.1, 97.5, 99.0)}
    events = {minute(60): [bos(LONG, 100.3, 11, minute(60))]}
    fresh = zone(M5, 99.2, 98.8, 11, 11, minute(60), minute(55))
    m1, frames, setup = harness(overrides, setup_events=events, zones=(fresh,))
    drive(m1, frames, setup, until=minute(49))
    drive(m1, frames, setup, after=minute(59), until=minute(60))
    assert setup.extreme_ts == minute(59) and setup.step is Step.BOS


def test_reentry_tap_uses_original_bos_deadline_after_gap():
    m1, frames, setup = harness({0: BASE[0], 131: (99.5, 99.6, 99.1, 99.5)}, entry_events={})
    drive(m1, frames, setup, until=minute(5))
    # A prior trade lost its Z3; returning to BOS must not reset the tap clock.
    setup.step = Step.IN_TRADE
    setup.trade_closed(minute(120))
    assert setup.step is Step.BOS
    drive(m1, frames, setup, after=minute(131), until=minute(132))
    assert setup.step is Step.DONE and setup.ended == "3rd confluence not tapped in time"
