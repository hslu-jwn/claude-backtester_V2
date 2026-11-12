"""Gates metadata has no effect on research identity or expansion."""

from backtester.tools.research_grid import expand, grid_id, load_grid


def test_gates_excluded_from_identity(tmp_path):
    path = tmp_path / "idea.toml"
    base = 'strategy = "opening_range"\nsymbols = ["US500"]\n'
    path.write_text(base)
    before = load_grid(path)
    original = grid_id(before, expand(before)[0])
    path.write_text(base + '\n[gates]\nunknown = { arbitrary = [1, 2] }\nmin_trades = "unchecked"\n')
    after = load_grid(path)
    assert grid_id(after, expand(after)[0]) == original
    assert expand(after) == expand(before)
