import io

from backtester.tools import notify


def rig(monkeypatch, tmp_path):
    sent, waiters = [], []
    monkeypatch.setattr(notify, "telegram_sender", sent.append)
    monkeypatch.setattr(notify, "start_waiter", waiters.append)
    monkeypatch.setattr(notify, "PENDING", tmp_path / "p")
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO('{"cwd": "X:\\\\a\\\\proj", "message": "Claude needs your permission"}'),
    )
    return sent, waiters


def test_hook_sends_after_delay_when_user_stays_away(monkeypatch, tmp_path):
    sent, waiters = rig(monkeypatch, tmp_path)
    notify.main(["--hook"])
    assert sent == []
    notify.send_if_still_pending(waiters[0], delay_s=0)
    assert sent == ["Claude waiting (proj): Claude needs your permission"]


def test_activity_cancels_the_alert(monkeypatch, tmp_path):
    sent, waiters = rig(monkeypatch, tmp_path)
    notify.main(["--hook"])
    notify.main(["--clear"])
    notify.send_if_still_pending(waiters[0], delay_s=0)
    assert sent == []


def test_newer_alert_replaces_older_waiter(monkeypatch, tmp_path):
    sent, waiters = rig(monkeypatch, tmp_path)
    notify.main(["--hook"])
    monkeypatch.setattr("sys.stdin", io.StringIO('{"cwd": "X:\\\\b", "message": "m2"}'))
    notify.main(["--hook"])
    notify.send_if_still_pending(waiters[0], delay_s=0)
    assert sent == []
    notify.send_if_still_pending(waiters[1], delay_s=0)
    assert sent == ["Claude waiting (b): m2"]


def test_plain_text_and_failure(monkeypatch, tmp_path):
    sent, _ = rig(monkeypatch, tmp_path)
    notify.main(["New", "strategy"])
    assert sent == ["New strategy"]
    monkeypatch.setattr(notify, "telegram_sender", lambda t: 1 / 0)
    assert notify.main(["x"]) == 0
