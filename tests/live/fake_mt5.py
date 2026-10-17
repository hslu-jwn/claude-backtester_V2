"""A fake `MetaTrader5` module for the unit tests (the real one needs Windows + a terminal).

`FakeMt5` has the functions and constants the code uses, with the same return shapes:
named tuples for account / terminal / symbol info, a numpy structured array for rates,
`OrderSendResult`-like named tuples for `order_send`. Bars are given in **server time**
(seconds as MT5 returns them). Orders fill at once at the current tick (or are rejected
with a scripted retcode) and keep positions in memory, hedging style.

    fake = FakeMt5()
    fake.add_symbol("XAUUSD", digits=2, ...)
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
"""

from __future__ import annotations

from collections import namedtuple
from datetime import UTC, datetime

import numpy as np

AccountInfo = namedtuple(
    "AccountInfo",
    "login trade_mode leverage balance equity currency name server trade_allowed "
    "trade_expert margin_mode",
)
TerminalInfo = namedtuple("TerminalInfo", "connected trade_allowed maxbars build data_path path")
SymbolInfo = namedtuple(
    "SymbolInfo",
    "name visible digits point trade_contract_size trade_tick_size trade_tick_value "
    "volume_min volume_step volume_max trade_stops_level trade_freeze_level swap_long "
    "swap_short swap_mode trade_mode filling_mode trade_exemode currency_base "
    "currency_profit spread path description time",
    defaults=(0,),  # time: the last quote, server seconds (0 = unknown)
)
Tick = namedtuple("Tick", "time bid ask last volume time_msc")
Position = namedtuple("Position", "ticket symbol type volume price_open sl tp magic comment time")
Order = namedtuple("Order", "ticket symbol type volume_current magic")
Deal = namedtuple("Deal", "ticket order position_id symbol type volume price")
SendResult = namedtuple(
    "OrderSendResult",
    "retcode deal order volume price bid ask comment request_id retcode_external request",
)

RATE_DTYPE = np.dtype(
    [
        ("time", "<i8"),
        ("open", "<f8"),
        ("high", "<f8"),
        ("low", "<f8"),
        ("close", "<f8"),
        ("tick_volume", "<u8"),
        ("spread", "<i4"),
        ("real_volume", "<u8"),
    ]
)


class FakeMt5:
    # account trade modes
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_CONTEST = 1
    ACCOUNT_TRADE_MODE_REAL = 2
    ACCOUNT_MARGIN_MODE_RETAIL_NETTING = 0
    ACCOUNT_MARGIN_MODE_EXCHANGE = 1
    ACCOUNT_MARGIN_MODE_RETAIL_HEDGING = 2
    # timeframes (the real values)
    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H4 = 16388
    TIMEFRAME_D1 = 16408
    # trading
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    ORDER_TIME_GTC = 0
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_INVALID_STOPS = 10016
    TRADE_RETCODE_MARKET_CLOSED = 10018
    TRADE_RETCODE_INVALID_FILL = 10030
    SYMBOL_TRADE_MODE_DISABLED = 0
    SYMBOL_TRADE_MODE_LONGONLY = 1
    SYMBOL_TRADE_MODE_SHORTONLY = 2
    SYMBOL_TRADE_MODE_CLOSEONLY = 3
    SYMBOL_TRADE_MODE_FULL = 4
    SYMBOL_TRADE_EXECUTION_MARKET = 2

    def __init__(self, trade_mode: int = 0, login_ok: bool = True):
        self.trade_mode = trade_mode
        self.login_ok = login_ok
        self.initialized = False
        self.init_kwargs: dict = {}
        self.error = (1, "Success")
        self.symbols: dict[str, SymbolInfo] = {}
        self.ticks: dict[str, Tick] = {}
        self.rates: dict[tuple[str, int], np.ndarray] = {}
        self.positions: dict[int, Position] = {}
        self.deals: dict[int, Deal] = {}
        self.requests: list[dict] = []
        self.reject: dict[tuple[int, int | None], int] = {}  # (action, filling) -> retcode
        self.allowed_fillings = {self.ORDER_FILLING_FOK, self.ORDER_FILLING_IOC}
        self.algo_allowed = True
        self.next_ticket = 1000

    # --- connection --------------------------------------------------------------------
    def initialize(self, path=None, **kwargs):
        self.init_kwargs = {"path": path, **kwargs}
        if not self.login_ok:
            self.error = (-6, "Terminal: Authorization failed")
            return False
        self.initialized = True
        self.error = (1, "Success")
        return True

    def shutdown(self):
        self.initialized = False
        return True

    def last_error(self):
        return self.error

    def account_info(self):
        if not self.initialized:
            return None
        return AccountInfo(
            login=12345678,
            trade_mode=self.trade_mode,
            leverage=100,
            balance=100_000.0,
            equity=100_012.5,
            currency="USD",
            name="Test Trader",
            server="Broker-Demo",
            trade_allowed=True,
            trade_expert=True,
            margin_mode=self.ACCOUNT_MARGIN_MODE_RETAIL_HEDGING,
        )

    def terminal_info(self):
        if not self.initialized:
            return None
        return TerminalInfo(True, self.algo_allowed, 100_000, 5000, "C:/data", "C:/terminal")

    # --- symbols and data ----------------------------------------------------------------
    def add_symbol(self, name: str, **specs) -> None:
        defaults = dict(  # noqa: C408 - reads like the named tuple
            name=name,
            visible=True,
            digits=2,
            point=0.01,
            trade_contract_size=100.0,
            trade_tick_size=0.01,
            trade_tick_value=1.0,
            volume_min=0.01,
            volume_step=0.01,
            volume_max=100.0,
            trade_stops_level=0,
            trade_freeze_level=0,
            swap_long=-10.0,
            swap_short=5.0,
            swap_mode=1,
            trade_mode=self.SYMBOL_TRADE_MODE_FULL,
            filling_mode=3,
            trade_exemode=self.SYMBOL_TRADE_EXECUTION_MARKET,
            currency_base="XAU",
            currency_profit="USD",
            spread=20,
            path=f"Fake\\{name}",
            description=name,
        )
        defaults.update(specs)
        self.symbols[name] = SymbolInfo(**defaults)

    def set_tick(self, name: str, bid: float, ask: float, server_time: int) -> None:
        self.ticks[name] = Tick(server_time, bid, ask, 0.0, 0, server_time * 1000)

    def set_rates(self, name: str, timeframe: int, rows: list[tuple]) -> None:
        """rows: (server seconds, open, high, low, close[, spread points])."""
        out = np.zeros(len(rows), dtype=RATE_DTYPE)
        for i, row in enumerate(rows):
            t, o, h, lo, c, *rest = row
            out[i] = (t, o, h, lo, c, 10, rest[0] if rest else 0, 0)
        self.rates[(name, timeframe)] = out

    def symbols_get(self, group=None):
        return tuple(self.symbols.values())

    def symbol_info(self, name):
        return self.symbols.get(name)

    def symbol_select(self, name, enable=True):
        return name in self.symbols

    def symbol_info_tick(self, name):
        return self.ticks.get(name)

    def copy_rates_range(self, name, timeframe, date_from, date_to):
        rates = self.rates.get((name, timeframe))
        if rates is None:
            self.error = (-1, "Terminal: Call failed")
            return None
        lo, hi = _seconds(date_from), _seconds(date_to)
        return rates[(rates["time"] >= lo) & (rates["time"] <= hi)]

    def copy_rates_from_pos(self, name, timeframe, start_pos, count):
        rates = self.rates.get((name, timeframe))
        if rates is None:
            return None
        end = len(rates) - start_pos
        return rates[max(0, end - count) : end]

    # --- trading -------------------------------------------------------------------------
    def order_send(self, request):
        self.requests.append(dict(request))
        action, filling = request["action"], request.get("type_filling")
        for key in ((action, filling), (action, None)):
            if key in self.reject:
                return self._result(self.reject[key], request)
        if action == self.TRADE_ACTION_DEAL and filling not in self.allowed_fillings:
            return self._result(self.TRADE_RETCODE_INVALID_FILL, request)
        if action == self.TRADE_ACTION_SLTP:
            pos = self.positions[request["position"]]
            tick = self.ticks[pos.symbol]
            sl = request.get("sl", 0.0)
            # a buy's SL must be below the bid, a sell's above the ask
            if sl and (
                (pos.type == self.POSITION_TYPE_BUY and sl >= tick.bid)
                or (pos.type == self.POSITION_TYPE_SELL and sl <= tick.ask)
            ):
                return self._result(self.TRADE_RETCODE_INVALID_STOPS, request)
            self.positions[pos.ticket] = pos._replace(sl=sl, tp=request.get("tp", pos.tp))
            return self._result(self.TRADE_RETCODE_DONE, request)
        tick = self.ticks[request["symbol"]]
        buy = request["type"] == self.ORDER_TYPE_BUY
        price = tick.ask if buy else tick.bid
        self.next_ticket += 1
        ticket = self.next_ticket
        if request.get("position"):
            pos = self.positions[request["position"]]
            left = round(pos.volume - request["volume"], 8)
            if left <= 0:
                del self.positions[pos.ticket]
            else:
                self.positions[pos.ticket] = pos._replace(volume=left)
            position_id = pos.ticket
        else:
            position_id = ticket
            self.positions[ticket] = Position(
                ticket,
                request["symbol"],
                self.POSITION_TYPE_BUY if buy else self.POSITION_TYPE_SELL,
                request["volume"],
                price,
                request.get("sl", 0.0),
                request.get("tp", 0.0),
                request.get("magic", 0),
                request.get("comment", ""),
                tick.time,
            )
        self.deals[ticket] = Deal(
            ticket,
            ticket,
            position_id,
            request["symbol"],
            request["type"],
            request["volume"],
            price,
        )
        return self._result(
            self.TRADE_RETCODE_DONE,
            request,
            deal=ticket,
            order=ticket,
            price=price,
            volume=request["volume"],
        )

    def _result(self, retcode, request, deal=0, order=0, price=0.0, volume=0.0):
        tick = self.ticks.get(request.get("symbol", ""))
        return SendResult(
            retcode,
            deal,
            order,
            volume,
            price,
            tick.bid if tick else 0.0,
            tick.ask if tick else 0.0,
            "done" if retcode == self.TRADE_RETCODE_DONE else "rejected",
            1,
            0,
            dict(request),
        )

    def positions_get(self, symbol=None, ticket=None):
        out = [
            p
            for p in self.positions.values()
            if (symbol is None or p.symbol == symbol) and (ticket is None or p.ticket == ticket)
        ]
        return tuple(out)

    def orders_get(self, symbol=None, ticket=None):
        return ()

    def history_deals_get(self, *args, ticket=None, position=None, **kwargs):
        if ticket is not None:
            return tuple(d for d in self.deals.values() if d.ticket == ticket)
        if position is not None:
            return tuple(d for d in self.deals.values() if d.position_id == position)
        return tuple(self.deals.values())


def _seconds(value) -> int:
    if isinstance(value, datetime):
        value = value if value.tzinfo else value.replace(tzinfo=UTC)
        return int(value.timestamp())
    return int(value)
