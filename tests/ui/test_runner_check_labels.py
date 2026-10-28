"""Research runner warning labels are readable both inline and on hover."""

import pytest

from backtester.ui.research_model import flag_text, flag_tooltip


@pytest.mark.parametrize(
    "key,label",
    [
        ("too_many_parameters", "more than 4 swept settings"),
        ("entry_screen_failed", "entries not better than chance"),
        ("declining_returns", "returns falling over time"),
    ],
)
def test_runner_check_labels(key, label):
    assert label in flag_text([key])
    assert label in flag_tooltip([key])
