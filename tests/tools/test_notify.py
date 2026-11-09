import io

from backtester.tools import notify


def test_hook_and_text_messages(monkeypatch):
    sent = []
    monkeypatch.setattr(notify, "telegram_sender", sent.append)
    monkeypatch.setattr("sys.stdin", io.StringIO('{"cwd": "X:\\\\a\\\\proj", "message": "Claude needs your permission"}'))
    notify.main(["--hook"])
    notify.main(["New", "strategy"])
    assert sent == ["Claude waiting (proj): Claude needs your permission", "New strategy"]


def test_failure_never_raises(monkeypatch):
    monkeypatch.setattr(notify, "telegram_sender", lambda t: 1 / 0)
    assert notify.main(["x"]) == 0
