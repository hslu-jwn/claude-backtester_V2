"""An in-memory stand-in for the `keyring` module (the tests never touch the real store)."""

from __future__ import annotations


class FakeKeyring:
    def __init__(self, fail: bool = False):
        self.store: dict[tuple[str, str], str] = {}
        self.fail = fail

    def get_password(self, service, username):
        if self.fail:
            raise RuntimeError("locked")
        return self.store.get((service, username))

    def set_password(self, service, username, password):
        if self.fail:
            raise RuntimeError("locked")
        self.store[(service, username)] = password

    def delete_password(self, service, username):
        del self.store[(service, username)]
