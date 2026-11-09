from pathlib import Path
from types import SimpleNamespace

import pytest

from backtester.data.sources import DEFAULT_SOURCES
from backtester.tools import research


def test_parse_cache_dir():
    assert research.parse_args(['grid.toml']).cache_dir is None
    assert research.parse_args(['grid.toml', '--cache-dir', 'x']).cache_dir == Path('x')


def test_main_passes_custom_sources(tmp_path, monkeypatch):
    (tmp_path / 'EURUSD').mkdir()
    (tmp_path / 'GBPUSD').mkdir()
    monkeypatch.setattr(research, 'load_grid', lambda path: SimpleNamespace(symbols=['EURUSD', 'GBPUSD']))
    captured = {}

    def run(grid, **kwargs):
        captured.update(kwargs)
        return {'message': 'done', 'folder': tmp_path, 'status': 'done'}

    monkeypatch.setattr(research, 'run_research', run)
    assert research.main(['grid.toml', '--cache-dir', str(tmp_path), '--dev-only']) == 0
    sources = captured['sources']
    assert dict(sources.cache_dirs) == {'EURUSD': tmp_path, 'GBPUSD': tmp_path}
    assert not sources.preferred_dirs
    assert captured['dev_only'] is True


@pytest.mark.parametrize('missing_symbol', [False, True])
def test_main_rejects_missing_cache_directory(tmp_path, monkeypatch, missing_symbol):
    cache = tmp_path / 'cache'
    if missing_symbol:
        cache.mkdir()
    monkeypatch.setattr(research, 'load_grid', lambda path: SimpleNamespace(symbols=['EURUSD']))
    expected = cache / 'EURUSD' if missing_symbol else cache
    with pytest.raises(SystemExit, match='EURUSD' if missing_symbol else 'cache') as exc:
        research.main(['grid.toml', '--cache-dir', str(cache)])
    assert str(expected) in str(exc.value)


def test_main_without_cache_dir_uses_default_sources(monkeypatch, tmp_path):
    captured = {}

    def run(grid, **kwargs):
        captured.update(kwargs)
        return {'message': 'done', 'folder': tmp_path, 'status': 'done'}

    monkeypatch.setattr(research, 'run_research', run)
    assert research.main(['grid.toml']) == 0
    assert captured.get('sources', DEFAULT_SOURCES) is DEFAULT_SOURCES
