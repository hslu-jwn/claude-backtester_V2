"""`FakeMt5` extended for the bot tests: full deals (entry, reason, profit), settable account
numbers, a terminal that shows a fill late (as FTMO does), and stop-outs by hand."""

from __future__ import annotations

from collections import namedtuple

from fake_mt5 import FakeMt5

Deal2 = namedtuple(
    "Deal2",
    "ticket order position_id symbol type volume price entry reason profit commission swap fee "
    "time",
)


class FakeBotMt5(FakeMt5):
    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1
    DEAL_REASON_SL = 4
    DEAL_REASON_TP = 5
    DEAL_REASON_EXPERT = 3
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1

    def __init__(self, trade_mode=0, delay_polls=0, balance=100_000.0, equity=None, **kw):
        super().__init__(trade_mode=trade_mode, **kw)
        self.delay_polls = delay_polls  # polls after an order_send that still see the old state
        self.balance = balance
        self.equity = balance if equity is None else equity
        self.commission_per_lot = 0.0
        self._stale = None
        self.init_calls = 0
        self.fail_init = 0  # the next N initialize() calls fail

    def initialize(self, path=None, **kwargs):
        self.init_calls += 1
        if self.fail_init > 0:
            self.fail_init -= 1
            self.error = (-10005, "IPC timeout")
            return False
        return super().initialize(path, **kwargs)

    def account_info(self):
        info = super().account_info()
        return None if info is None else info._replace(balance=self.balance, equity=self.equity)

    def _value(self, symbol: str) -> float:
        info = self.symbols[symbol]
        return info.trade_tick_value / info.trade_tick_size

    # --- orders: late visibility, full deals --------------------------------------------
    def order_send(self, request):
        before = (dict(self.positions), dict(self.deals))
        known = set(self.deals)
        pos = self.positions.get(request.get("position"))
        result = super().order_send(request)
        for ticket in set(self.deals) - known:
            old = self.deals[ticket]
            profit = 0.0
            if pos is not None:
                sign = 1 if pos.type == self.POSITION_TYPE_BUY else -1
                profit = sign * (old.price - pos.price_open) * old.volume * self._value(old.symbol)
            commission = -self.commission_per_lot * old.volume
            self.deals[ticket] = Deal2(
                old.ticket, old.order, old.position_id, old.symbol, old.type, old.volume,
                old.price, self.DEAL_ENTRY_OUT if pos is not None else self.DEAL_ENTRY_IN,
                self.DEAL_REASON_EXPERT, profit, commission, 0.0, 0.0, 0,
            )  # fmt: skip
            if pos is not None:
                self.balance += profit + commission
        if self.delay_polls and result.retcode == self.TRADE_RETCODE_DONE:
            self._stale = [before, self.delay_polls]
            result = result._replace(deal=0, price=0.0)
        return result

    def _view(self):
        if self._stale and self._stale[1] > 0:
            return self._stale[0]
        return self.positions, self.deals

    def positions_get(self, symbol=None, ticket=None):
        positions, _ = self._view()
        return tuple(
            p
            for p in positions.values()
            if (symbol is None or p.symbol == symbol) and (ticket is None or p.ticket == ticket)
        )

    def history_deals_get(self, *args, ticket=None, position=None, **kwargs):
        _, deals = self._view()
        if self._stale and self._stale[1] > 0:
            self._stale[1] -= 1
        if ticket is not None:
            return tuple(d for d in deals.values() if d.ticket == ticket)
        if position is not None:
            return tuple(d for d in deals.values() if d.position_id == position)
        return tuple(deals.values())

    # --- stop-outs ----------------------------------------------------------------------
    def stop_out(self, ticket: int, price: float, reason: int) -> None:
        """The server closes the position at `price` (SL or TP hit)."""
        pos = self.positions.pop(ticket)
        sign = 1 if pos.type == self.POSITION_TYPE_BUY else -1
        profit = sign * (price - pos.price_open) * pos.volume * self._value(pos.symbol)
        self.next_ticket += 1
        self.deals[self.next_ticket] = Deal2(
            self.next_ticket, self.next_ticket, ticket, pos.symbol, 1 - pos.type, pos.volume,
            price, self.DEAL_ENTRY_OUT, reason, profit, 0.0, 0.0, 0.0, 0,
        )  # fmt: skip
        self.balance += profit
