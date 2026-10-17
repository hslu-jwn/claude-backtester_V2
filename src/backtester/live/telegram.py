"""Telegram messages and commands for the live bot. Spec: docs/live-trading.md › Monitoring.

Bot token and chat id live only in the Windows Credential Manager (service
`backtester.trading`, entry "Telegram"), like the MT5 login. They are never written to the repo,
`results/`, logs, error texts or test output: `TelegramConfig` prints as "<hidden>" and every
error text is scrubbed of the token.

`Notifier` never blocks or crashes the trading loop: `notify` only puts the text into a bounded
queue; a background thread sends it (short timeouts) and polls `getUpdates` for commands from the
saved chat id (all other chats are ignored): /status, /stop (STOP file), /emergency (asks for
"/emergency confirm" within 60 s, then writes the EMERGENCY file). Commands sent before the bot
started are dropped by the first poll.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from backtester.live.credentials import SERVICE, CredentialStoreError, keyring_backend

log = logging.getLogger(__name__)

ENTRY = "Telegram"
API = "https://api.telegram.org"
SEND_TIMEOUT_S = 8.0
EMERGENCY_CONFIRM_S = 60.0
HIDDEN = "<hidden>"
Http = Callable[[str, dict, float], dict]  # (url, json payload, timeout) -> parsed json reply


class TelegramError(RuntimeError):
    pass


@dataclass(frozen=True)
class TelegramConfig:
    token: str = field(repr=False)
    chat_id: str = field(repr=False)

    def __repr__(self) -> str:
        return "TelegramConfig(<hidden>)"

    __str__ = __repr__


def load_telegram(backend=None) -> TelegramConfig | None:
    backend = backend or keyring_backend()
    try:
        text = backend.get_password(SERVICE, ENTRY)
    except Exception as e:  # noqa: BLE001 - every keyring backend has its own errors
        raise CredentialStoreError(
            f"the credential store can't be read ({type(e).__name__})"
        ) from None
    if not text:
        return None
    try:
        data = json.loads(text)
        return TelegramConfig(str(data["token"]), str(data["chat_id"]))
    except (ValueError, KeyError, TypeError):
        return None


def save_telegram(config: TelegramConfig, backend=None) -> None:
    if not config.token or not config.chat_id:
        raise CredentialStoreError("the bot token and the chat id are both needed")
    if not config.chat_id.lstrip("-").isdigit():
        raise CredentialStoreError("the chat id is a number (it may start with -)")
    backend = backend or keyring_backend()
    text = json.dumps({"token": config.token, "chat_id": config.chat_id})
    try:
        backend.set_password(SERVICE, ENTRY, text)
    except Exception as e:  # noqa: BLE001
        raise CredentialStoreError(
            f"the credential store can't be written ({type(e).__name__})"
        ) from None


def _urllib_post(url: str, payload: dict, timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


class TelegramClient:
    def __init__(self, config: TelegramConfig, http: Http | None = None):
        self._config = config
        self._http = http or _urllib_post

    @property
    def chat_id(self) -> str:
        return self._config.chat_id

    def scrub(self, text: str) -> str:
        return text.replace(self._config.token, HIDDEN)

    def _call(self, method: str, payload: dict, timeout: float = SEND_TIMEOUT_S) -> dict:
        url = f"{API}/bot{self._config.token}/{method}"
        try:
            reply = self._http(url, payload, timeout)
        except Exception as e:  # noqa: BLE001 - urllib's errors can contain the URL
            raise TelegramError(f"{type(e).__name__}: {self.scrub(str(e))}") from None
        if not isinstance(reply, dict) or not reply.get("ok"):
            raise TelegramError(f"{method}: Telegram did not accept the request")
        return reply

    def send(self, text: str) -> None:
        self._call("sendMessage", {"chat_id": self._config.chat_id, "text": text})

    def get_updates(self, offset: int | None) -> list[dict]:
        payload: dict = {"timeout": 0, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset
        return list(self._call("getUpdates", payload).get("result") or [])


# --- message texts ---------------------------------------------------------------------------


def _num(value) -> str:
    return f"{value:g}" if isinstance(value, int | float) else str(value)


def format_event(kind: str, f: dict) -> str | None:
    """The Telegram text of a bot event, or None when the event is not announced."""
    sym = f.get("symbol", "")
    if kind == "connected":
        return "Bot started: connected to the DEMO account."
    if kind == "stopped":
        return "Bot stopped."
    if kind == "stop_file":
        return "STOP file found: bot stopping (positions stay open with their SL)."
    if kind == "emergency_file":
        return "EMERGENCY file found: closing all bot positions, then stopping."
    if kind == "paused":
        return "Paused: no new entries; open trades keep being managed."
    if kind == "unpaused":
        return "Resumed: new entries allowed again."
    if kind == "signal":
        return (
            f"Signal {sym} {f.get('side', '')} entry {_num(f.get('entry'))} SL {_num(f.get('sl'))}"
        )
    if kind == "order":
        return (
            f"Fill {sym} {f.get('side', '')} {_num(f.get('lots'))} lots at "
            f"{_num(f.get('fill'))}, SL {_num(f.get('sl'))} (ticket {f.get('ticket', '')})"
        )
    if kind == "trade_closed":
        r = float(f.get("r_net", 0.0))
        return f"Exit {sym}: {r:+.1f} R ({f.get('reason', '')})"
    if kind == "skip":
        return f"Skip {sym}: {f.get('reason', '')}"
    if kind == "guard_stop":
        return (
            f"Daily stop: {f.get('reason', '')} (day P/L {_num(f.get('day_pl'))}); no new orders."
        )
    if kind == "guard_breach":
        return f"FTMO limit: {f.get('reason', '')} (day P/L {_num(f.get('day_pl'))}); all closed."
    if kind == "refused":
        return f"Bot refused to run: {f.get('error', '')}"
    if kind in ("error", "close_failed", "connect_failed"):
        detail = f.get("what") or f.get("error") or f.get("retcode") or ""
        return f"Error ({kind}): {detail}"
    if kind == "disconnected":
        return f"Connection lost: {f.get('error', '')}; reconnecting."
    return None


# --- the background notifier -----------------------------------------------------------------


class Notifier:
    QUEUE_MAX = 100

    def __init__(
        self,
        client: TelegramClient,
        stop_file: Path | None,
        emergency_file: Path | None,
        status_text: Callable[[], str] = lambda: "no status yet",
        now: Callable[[], float] = time.monotonic,
        poll_every_s: float = 3.0,
        threaded: bool = True,
    ):
        self.client = client
        self.stop_file, self.emergency_file = stop_file, emergency_file
        self.status_text, self.now, self.poll_every_s = status_text, now, poll_every_s
        self.threaded = threaded
        self.errors: list[str] = []
        self.dropped = 0
        self._queue: queue.Queue[str] = queue.Queue(self.QUEUE_MAX)
        self._offset: int | None = None
        self._primed = False
        self._next_poll = 0.0
        self._confirm_until = 0.0
        self._halt = threading.Event()
        self._thread: threading.Thread | None = None

    # --- called from the trading loop: never blocks, never raises -----------------------------

    def notify(self, text: str) -> None:
        try:
            self._queue.put_nowait(text)
        except queue.Full:
            self.dropped += 1

    def event(self, kind: str, fields: dict) -> None:
        try:
            text = format_event(kind, fields)
        except Exception as e:  # noqa: BLE001 - a formatting bug must not stop trading
            self._error(f"format {kind}: {type(e).__name__}")
            return
        if text:
            self.notify(text)

    # --- worker --------------------------------------------------------------------------------

    def start(self) -> None:
        if self.threaded and self._thread is None:
            self._thread = threading.Thread(target=self._run, name="telegram", daemon=True)
            self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Send what is queued, then end the thread (waits at most `timeout`)."""
        self._halt.set()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None

    def _run(self) -> None:
        while not self._halt.wait(0.2):
            self.pump()
        self._send_queued()

    def pump(self, force_poll: bool = False) -> None:
        """One round: send the queued texts, poll for commands when due."""
        self._send_queued()
        if force_poll or self.now() >= self._next_poll:
            self._next_poll = self.now() + self.poll_every_s
            self._poll()
            self._send_queued()  # replies to commands

    def _send_queued(self) -> None:
        while True:
            try:
                text = self._queue.get_nowait()
            except queue.Empty:
                return
            try:
                self.client.send(text)
            except TelegramError as e:
                self._error(str(e))

    def _error(self, text: str) -> None:
        text = self.client.scrub(text)
        self.errors = [*self.errors[-19:], text]
        log.warning("telegram: %s", text)

    # --- commands --------------------------------------------------------------------------------

    def _poll(self) -> None:
        try:
            updates = self.client.get_updates(self._offset)
        except TelegramError as e:
            self._error(str(e))
            return
        for u in updates:
            self._offset = max(self._offset or 0, int(u.get("update_id", 0)) + 1)
        if not self._primed:  # commands sent before the bot started are not obeyed
            self._primed = True
            return
        for u in updates:
            message = u.get("message") or {}
            if str((message.get("chat") or {}).get("id")) != self.client.chat_id:
                continue
            self._command(str(message.get("text") or "").strip().lower())

    def _command(self, text: str) -> None:
        if text.startswith("/status"):
            try:
                self.notify(self.status_text())
            except Exception as e:  # noqa: BLE001
                self._error(f"status: {type(e).__name__}")
        elif text.startswith("/stop"):
            self._touch(self.stop_file)
            self.notify("STOP requested: the bot stops at its next cycle (nothing is closed).")
        elif text == "/emergency":
            self._confirm_until = self.now() + EMERGENCY_CONFIRM_S
            self.notify(
                f"EMERGENCY closes all bot positions and stops. Send /emergency confirm "
                f"within {EMERGENCY_CONFIRM_S:.0f} s."
            )
        elif text == "/emergency confirm":
            if self.now() <= self._confirm_until:
                self._confirm_until = 0.0
                self._touch(self.emergency_file)
                self.notify("EMERGENCY requested: closing all bot positions.")
            else:
                self.notify("Nothing to confirm: send /emergency first.")

    def _touch(self, path: Path | None) -> None:
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        except OSError as e:
            self._error(f"stop file: {type(e).__name__}")
