import csv
import json
from pathlib import Path

import pytest

from backtester.tools import harvest


def idea(**changes):
    result = {
        "name": "Month end", "claim": "The market rises", "source_url": "https://a.test/a",
        "source_type": "paper", "quote": "The month end rebalancing lifts the S&P market.",
        "language": "en", "mechanism": "index rebalancing", "rules": {
            "market": "S&P", "timeframe": "SWING", "entry": "buy at close",
            "exit": "sell next close", "stop": "one percent", "filters": "not stated"},
        "not_stated": [], "claimed_result": "5 percent", "required_data": ["price bars"],
        "we_have": "yes", "red_flags": ["none"],
    }
    result.update(changes)
    return result


PAGE = Path(__file__).parent / "harvest_fixtures" / "page.html"


def checked(item, page=None, allowed=True):
    return harvest.check_idea(item, "T0001", "model", lambda url: (
        200, PAGE.read_text() if page is None else page, allowed))


def test_source_checks():
    assert checked(idea())["status"] == "verified"
    assert checked(idea(quote="THE month end rebalancing lifts the S&P market."),
                   "<p>the MONTH end <b>rebalancing</b> lifts   the S&amp;P market.</p>")["status"] == "verified"
    assert checked(idea(quote="Completely unrelated paraphrase."))["reason"] == "unverified_source"
    assert checked(idea(), "sign in to continue")["reason"] == "unverified_source"
    assert checked(idea(), allowed=False)["reason"] == "unverified_source"
    assert checked(idea(quote="x" * 301))["reason"] == "schema"
    assert checked(idea(source_type="invalid"))["reason"] == "schema"
    bad = idea()
    bad["rules"]["entry"] = "use discretion"
    assert checked(bad)["reason"] == "untestable"


def test_robots_disallows_before_page_request(monkeypatch):
    calls = []
    class Response:
        status_code = 200
        text = "User-agent: *\nDisallow: /private"
    monkeypatch.setattr(harvest.requests, "get", lambda url, **kw: calls.append(url) or Response())
    monkeypatch.setattr(harvest.time, "sleep", lambda _: None)
    result = harvest.Fetcher()("https://example.test/private")
    assert not result[2]
    assert calls == ["https://example.test/robots.txt"]


def test_dedup_and_score(tmp_path):
    families = tmp_path / "families.csv"
    families.write_text("family,keywords,verdict,ledger_ids,note\n"
                        "turtle,Turtle Soup,falsified,,\nmonth,turn of month,open,,\n")
    ledger = tmp_path / "ledger.csv"
    ledger.write_text("id,source,notes\n")
    a = checked(idea(name="Turtle Soup"))
    b = checked(idea(name="turn of month"))
    c = checked(idea(name="another", source_url="https://b.test/a"))
    result = harvest.deduplicate([a, b, c], families, ledger)
    assert result[0]["reason"] == "known_family"
    assert result[1]["family"] == "month"
    assert result[2]["status"] == "merged"
    assert result[1]["seen_count"] == 2
    assert harvest.score_idea(result[1]) == 9
    weak = idea(mechanism="behaviour", source_type="forum", red_flags=["tiny_sample", "costs_ignored"])
    weak["rules"]["stop"] = "not stated"
    assert harvest.score_idea(weak) == 1


def test_plan_and_report(tmp_path, capsys):
    tasks = tmp_path / "tasks.csv"
    with pytest.raises(ValueError):
        harvest.plan(["BLOG.BAD.SWING.FLOW"], tasks)
    harvest.plan(["BLOG.IDX-US.SWING.FLOW"], tasks)
    with pytest.raises(ValueError):
        harvest.plan(["BLOG.IDX-US.SWING.FLOW"], tasks)
    ledger = tmp_path / "ledger.csv"
    ledger.write_text("id,stage,name,source,verdict,notes\nOLD,verified,old,,,\n")
    rows = [checked(idea())]
    harvest.report(rows, tasks, ledger, True)
    harvest.report(rows, tasks, ledger, True)
    with ledger.open(newline="") as f:
        assert len(list(csv.DictReader(f))) == 2
    assert "T0001" in capsys.readouterr().out


def test_jsonl_roundtrip(tmp_path):
    raw = tmp_path / "raw.jsonl"
    raw.write_text(json.dumps({"task_id": "T0001", "ideas": [idea()]}) + "\n")
    rows = harvest.check_file(raw, "model", lambda url: (200, PAGE.read_text(), True))
    assert rows[0]["status"] == "verified"


def test_fractional_win_rate_above_90_is_hindsight():
    assert checked(idea(claimed_result="win rate 90.5%"))["reason"] == "hindsight"


def test_fuzzy_quote_check_is_fast_on_a_long_page():
    import time as clock
    page = "<p>" + "filler words about markets " * 8000 + "the month end rebalancing lifts the s&p market</p>"
    start = clock.perf_counter()
    assert checked(idea(quote="The month-end rebalancing lifts the S&P market."), page)["status"] == "verified"
    assert checked(idea(quote="Completely unrelated paraphrase of nothing here."), page)["reason"] == "unverified_source"
    assert clock.perf_counter() - start < 5


def test_fetcher_follows_redirects(monkeypatch):
    seen = {}
    class Response:
        status_code = 200
        text = ""
    def get(url, **kw):
        seen[url] = kw.get("allow_redirects")
        return Response()
    monkeypatch.setattr(harvest.requests, "get", get)
    monkeypatch.setattr(harvest.time, "sleep", lambda _: None)
    harvest.Fetcher()("http://example.test/page")
    assert seen["http://example.test/page"] is True


def test_plan_uses_search_words_not_codes(tmp_path):
    tasks = tmp_path / "tasks.csv"
    harvest.plan(["AGG.IDX-US.SWING.FLOW"], tasks)
    queries = next(csv.DictReader(tasks.open(encoding="utf-8")))["queries"]
    assert "US stock index rebalancing flows" in queries and "IDX-US" not in queries
