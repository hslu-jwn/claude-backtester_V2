"""Trading login, kept only in the Windows Credential Manager. Spec: ROADMAP.md › 7.1.

Login, password and server are entered in the app (Settings ⚙ → Trading) and stored with
`keyring` (one entry per platform, service `backtester.trading`). They are never written to
the repo, `.env`, results/, logs, error messages or test output: `Credentials` prints as
"<hidden>", and `connection.scrub` removes the values from MT5's error texts.

`keyring` is part of the optional extra `[mt5]`; it is imported only when needed.
"""

from __future__ import annotations

import contextlib
import importlib
import json
from dataclasses import dataclass, field

SERVICE = "backtester.trading"


class CredentialStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class Credentials:
    login: str = field(repr=False)
    password: str = field(repr=False)
    server: str = field(repr=False)

    def __repr__(self) -> str:
        return "Credentials(<hidden>)"

    __str__ = __repr__

    def secrets(self) -> tuple[str, ...]:
        return tuple(v for v in (self.login, self.password, self.server) if v)


def keyring_backend():
    try:
        return importlib.import_module("keyring")
    except ImportError as e:
        raise CredentialStoreError('keyring is not installed: pip install -e ".[mt5]"') from e


def load_credentials(platform: str = "MT5", backend=None) -> Credentials | None:
    backend = backend or keyring_backend()
    try:
        text = backend.get_password(SERVICE, platform)
    except Exception as e:  # noqa: BLE001 - every keyring backend has its own errors
        raise CredentialStoreError(
            f"the credential store can't be read ({type(e).__name__})"
        ) from None
    if not text:
        return None
    try:
        data = json.loads(text)
        return Credentials(str(data["login"]), str(data["password"]), str(data["server"]))
    except (ValueError, KeyError, TypeError):
        return None


def save_credentials(credentials: Credentials, platform: str = "MT5", backend=None) -> None:
    if not (credentials.login and credentials.password and credentials.server):
        raise CredentialStoreError("login, password and server are all needed")
    backend = backend or keyring_backend()
    text = json.dumps(
        {
            "login": credentials.login,
            "password": credentials.password,
            "server": credentials.server,
        }
    )
    try:
        backend.set_password(SERVICE, platform, text)
    except Exception as e:  # noqa: BLE001 - as above
        raise CredentialStoreError(
            f"the credential store can't be written ({type(e).__name__})"
        ) from None


def delete_credentials(platform: str = "MT5", backend=None) -> None:
    backend = backend or keyring_backend()
    with contextlib.suppress(Exception):  # nothing saved
        backend.delete_password(SERVICE, platform)
