"""Shared market classes. Spec: research-runner.md > Additional diagnostics."""

INDEX_CLASSES = {
    **dict.fromkeys(("NAS100", "US500", "US30", "US2000"), "US indices"),
    **dict.fromkeys(("GER40", "EU50", "UK100", "JP225"), "EU/UK/JP indices"),
}
MARKET_CLASSES = {
    **INDEX_CLASSES,
    **dict.fromkeys(("XAUUSD", "XAGUSD"), "Metals"),
    **dict.fromkeys(
        (
            "GBPUSD",
            "GBPJPY",
            "EURUSD",
            "USDJPY",
            "AUDUSD",
            "USDCAD",
            "USDCHF",
            "NZDUSD",
            "EURJPY",
            "EURGBP",
        ),
        "FX",
    ),
    **dict.fromkeys(("USOIL", "UKOIL", "NATGAS"), "Energy"),
    **dict.fromkeys(("BTCUSD", "ETHUSD", "BTCUSDT", "ETHUSDT"), "Crypto"),
    "DXY": "Dollar index",
}


def market_class(trade):
    """ORB's session classes when available; otherwise classify by symbol."""
    group = MARKET_CLASSES.get(trade.symbol, "Other")
    reason = getattr(trade, "reason", "") or ""
    session = reason.rsplit(" ", 1)[-1] if reason.startswith("opening range") else None
    if group in ("Metals", "FX") and session in ("london", "new_york"):
        label = "London" if session == "london" else "NY" if group == "Metals" else "New York"
        return f"{group} {label}"
    return group
