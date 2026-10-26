"""Chart review and trade inspection callbacks, callable without a server."""

from datetime import date, datetime, timedelta

from dash import Input, Output, State, ctx, no_update

from backtester.ui import review, settings_panel, trade_focus, trades_overlay


def review_orders(sources, symbol, first, last, settings):
    run = trades_overlay.registered_run(
        sources, symbol, date.fromisoformat(first), date.fromisoformat(last), settings
    )
    return [t for t in run.trades if first <= t.entry_time.date().isoformat() <= last]


def evaluate(sources, strategy, labels, orders, state):
    """Include previously labelled dates/symbols, so absent means removed by the rules."""
    all_orders = list(orders)
    extra = {}
    for row in labels:
        day = datetime.fromisoformat(row["entry_time"]).date().isoformat()
        if row["symbol"] != state["symbol"] or not state["first"] <= day <= state["last"]:
            extra.setdefault(row["symbol"], []).append(day)
    for symbol, days in extra.items():
        all_orders.extend(
            trade_focus.inspection_order(t)
            for t in review_orders(sources, symbol, min(days), max(days), state["settings"])
        )
    return review.agreement(labels, strategy, all_orders)


def transition(
    sources,
    action,
    state,
    symbol,
    first,
    last,
    settings,
    strategy,
    reason=None,
    own_tp=None,
    folder=review.LABEL_DIR,
):
    """Review transaction. Return only the selected entry's sanitized data to Dash."""
    if action == "leave" or not symbol:
        return None, None, "Review off", "", "", [], None, None
    if not first or not last or first > last:
        raise ValueError("Choose a valid review period")
    previous = state or {}
    if (
        action == "run"
        or not state
        or state.get("settings") != settings
        or state.get("symbol") != symbol
    ):
        state = {
            "symbol": symbol,
            "strategy": strategy,
            "first": first,
            "last": last,
            "settings": settings,
            "settings_hash": review.settings_hash(settings),
            "index": 0,
            "revealed": False,
        }
    else:
        state = dict(state)
    trades = review_orders(
        sources, state["symbol"], state["first"], state["last"], state["settings"]
    )
    orders = [trade_focus.inspection_order(t) for t in trades]
    labels = review.load_labels(strategy, folder)
    index = min(state.get("index", 0), max(0, len(orders) - 1))
    status = ""
    if action in {"take", "skip"} and orders:
        review.save_label(
            review.label(strategy, orders[index], state["settings_hash"], action, reason, own_tp),
            folder,
        )
        labels = review.load_labels(strategy, folder)
        status = "Label saved"
    labelled_keys = {review.key(r) for r in labels}
    labelled = {
        i for i, o in enumerate(orders) if review.key(dict(o, strategy=strategy)) in labelled_keys
    }
    index = review.navigate(index, action, len(orders), labelled)
    counts = evaluate(sources, strategy, labels, orders, state)
    snapshots = review.history(strategy, state["settings_hash"], counts, folder)
    if index is None:
        return (
            None,
            None,
            "No trades in this period",
            status,
            review.agreement_text(counts),
            snapshots,
            None,
            None,
        )
    changed = (
        previous.get("entry_time") != orders[index]["entry_time"]
        or action == "run"
        or previous.get("settings_hash") != state["settings_hash"]
    )
    state["revealed"] = action == "reveal" or (state.get("revealed", False) and not changed)
    state.update(
        index=index,
        entry_time=orders[index]["entry_time"],
        order=review.decision_order(orders[index], state["revealed"]),
    )
    state["order"]["_settings"] = state["settings"]
    outcome = f" · {trades[index].r_net:+.2f}R" if state["revealed"] else " · outcome hidden"
    current = f"Trade {index + 1}/{len(orders)} · {state['entry_time']} · {orders[index]['direction']}{outcome}"
    prior_label = next(
        (r for r in labels if review.key(r) == review.key(dict(orders[index], strategy=strategy))),
        {},
    )
    # Load a compact window around entry; the server ceiling still applies to its candles.
    day = datetime.fromisoformat(state["entry_time"]).date()
    dates = {
        "start": (day - timedelta(days=7)).isoformat(),
        "end": (day + timedelta(days=7)).isoformat(),
    }
    if state["revealed"] and orders[index].get("exit_time"):
        dates["end"] = max(
            dates["end"], datetime.fromisoformat(orders[index]["exit_time"]).date().isoformat()
        )
    return (
        state,
        dates,
        current,
        status,
        review.agreement_text(counts),
        snapshots,
        prior_label.get("reason"),
        prior_label.get("own_tp"),
    )


def register_callbacks(app, sources, config, results_dir):
    from backtester.ui.pages import chart

    @app.callback(
        Output("review-period", "start_date"),
        Output("review-period", "end_date"),
        Input("chart-symbol", "value"),
    )
    def period(symbol):
        days = [d for d in sources.cached_days(symbol) if d < date(2021, 9, 14)] if symbol else []
        return (min(days).isoformat(), max(days).isoformat()) if days else (None, "2021-09-13")

    actions = ["run", "leave", "previous", "next", "unlabelled", "reveal", "take", "skip"]

    @app.callback(
        Output("chart-review", "data"),
        Output("chart-dates", "data", allow_duplicate=True),
        Output("review-current", "children"),
        Output("review-status", "children"),
        Output("review-agreement", "children"),
        Output("review-history", "children"),
        Output("review-reason", "value"),
        Output("review-tp", "value"),
        *[Input(f"review-{a}", "n_clicks") for a in actions],
        Input("settings-current", "data"),
        Input("chart-symbol", "value"),
        State("chart-review", "data"),
        State("review-period", "start_date"),
        State("review-period", "end_date"),
        State("review-reason", "value"),
        State("review-tp", "value"),
        prevent_initial_call=True,
    )
    def control(*args):
        store, symbol, state, first, last, reason, tp = args[-7:]
        action = str(ctx.triggered_id).removeprefix("review-")
        if action not in actions:
            if not state:
                return (no_update,) * 8
            if action == "chart-symbol":
                action = "leave"
        try:
            result = transition(
                sources,
                action,
                state,
                symbol,
                first,
                last,
                settings_panel.store_json(store),
                settings_panel.store_strategy(store),
                reason,
                tp,
                results_dir / "review",
            )
        except (ValueError, KeyError, OSError) as error:
            return (
                no_update,
                no_update,
                no_update,
                str(error),
                no_update,
                no_update,
                no_update,
                no_update,
            )
        new_state, dates, current, status, agreement, rows, reason, tp = result
        if dates:
            dates = {"start": dates["start"], "end": dates["end"]}
        return (
            new_state,
            dates or no_update,
            current,
            status,
            agreement,
            review.history_table(rows),
            reason,
            tp,
        )

    @app.callback(
        Output("chart-order", "data", allow_duplicate=True),
        Output("inspection-reason", "children"),
        Output("inspection-panel", "style"),
        Input("chart-inspect", "data"),
        State("chart-review", "data"),
        prevent_initial_call=True,
    )
    def inspect(clicked, review_state):
        if review_state:
            return no_update, "", {"display": "none"}
        order = (clicked or {}).get("order")
        return order, (order or {}).get("reason", ""), {} if order else {"display": "none"}

    @app.callback(
        Output("chart-replay", "data", allow_duplicate=True),
        Output("chart-replay-mode", "data", allow_duplicate=True),
        Output("chart-replay-controls", "style", allow_duplicate=True),
        Input("inspection-replay", "n_clicks"),
        State("inspection-lead", "value"),
        State("chart-order", "data"),
        State("chart-symbol", "value"),
        State("chart-timeframe", "value"),
        State("chart-dates", "data"),
        State("chart-review", "data"),
        prevent_initial_call=True,
    )
    def replay_trade(click, lead, order, symbol, timeframe, dates, review_state):
        if not click or not order or review_state:
            return (no_update,) * 3
        first, last = chart.dates_of(dates)
        replay, _ = chart.load_replay(sources, symbol, timeframe, first, last, config)
        if replay is None:
            return (no_update,) * 3
        index = replay.cursor_at(datetime.fromisoformat(order["entry_time"]))
        if index is None:
            return (no_update,) * 3
        at = review.utc(
            replay.close_time(max(0, index - max(0, int(lead if lead is not None else 50))))
        )
        state = {"on": True, "picking": False, "playing": False, "start": at, "now": at}
        return state, {"on": True, "picking": False}, {}
