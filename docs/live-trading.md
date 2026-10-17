# Live trading (Phase 7.2): demo forward test

Decisions by the user, 2026-10-17 (ROADMAP 7.2). Builds on 7.1 (`live/`: connection, credentials in the
Windows Credential Manager, DEMO LOCK in every order function, `OrderLog`).

## What runs

- **Strategy:** the opening-range breakout candidate (`docs/strategy-opening-range.md`, ROADMAP 11.10):
  band 0.25 ATR, no target, `min_rel_volume` 1.5, on US30, US500, NAS100, US2000, exit 15:55 New York.
  The same strategy code as the backtest, fed only closed M1 candles from MT5 (no lookahead).
- **Mode: fully automatic demo orders** (user, 2026-10-17). A paper log of every signal with its simulated
  fill runs alongside, so live and backtest can be compared trade by trade.
- **DEMO LOCK stays:** every order function refuses unless the account is DEMO. No override.

## Risk (adjustable per strategy, user 2026-10-17)

- **Risk per trade 0.25 %** of the balance; lots from risk % and the SL distance (Phase 5 sizer),
  rounded down to the volume step; below the minimum lot -> no trade, logged.
- **Daily stop -2 %** (closed + open P/L since the FTMO day start, midnight Europe/Prague): close own
  positions, no new orders until the next day. FTMO's own limits (5 % daily, 10 % max) stay checked too.
- **Emergency stop:** close all own positions (by `MAGIC`) and stop the bot; from the Live page and Telegram.

## Where it runs

- The MT5 Python API needs a running terminal; the bot starts it itself (`initialize(path=...)`), so
  the user does not have to open MT5 by hand. Later on a Windows VPS near the broker for 24/5 (no code
  change). Alternative without a terminal: FTMO's cTrader accounts via the cTrader Open API (Linux
  possible); not planned now.
- The bot is its own process (not inside the browser); closing the page does not stop it.

## Monitoring

- **Live page (minimal first):** connection and account (balance, equity, today's P/L in R and %),
  open positions, today's signals and skips with reasons, the log, Start / Stop / Emergency stop.
- **Telegram:** a message for start / stop, every signal, fill, exit (R), skip reason, daily stop,
  errors and disconnects; commands /status and /stop. The bot token and chat id are entered in
  Settings ⚙ and stored only in the Windows Credential Manager, like the MT5 login.
- **Duration** of the forward test: the user decides (an FTMO trial challenge runs 14 days).
