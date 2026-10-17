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

## App layout and Live page (rules set by the user, 2026-10-17; ROADMAP 7.3)

Style inspiration: `docs/ui-mockups/live-page.png` and `chart-page.png` (dark cards, monospace numbers).
**Inspiration only, not to be copied literally** (user, 2026-10-17); the mockup shows strategy 2, the bot
runs strategy 6.

- **No separate start page.** One top bar on every page: Chart · Backtest · Risk · Live. The app opens on
  `/live` when the bot is running (fresh heartbeat), otherwise on the chart.
- **Live button red** while the bot is running (live trading active), neutral otherwise; it updates on
  every page.
- **Gear ⚙ = backtest and chart settings only.** Chart settings are one collapsible block. The temporary
  Sweep menu moves out of the top bar into the chart settings (the sweep options themselves stay, off by
  default).
- **Account connection moves to `/live`:** a "Connection" section (MT5 login / server / terminal path,
  test connection, demo test orders, server clock, Telegram), collapsed once connected. Telegram is always
  on when a token is saved (no on/off switch).
- **`/live` shows:** status (running / paused / stopped), strategy and symbols; buttons Start, **Pause**
  (no new entries; open trades keep being managed; press again to resume), Stop, Close all & stop (confirm
  dialog); balance and equity in USD; today's P/L against the daily stop; distance to the FTMO 5 % daily and
  10 % max loss limits; session window with a countdown to the next one; bot heartbeat ("checked 4 s ago",
  red when stale); the setup in progress per symbol (strategy 6: range forming, range set, waiting for
  breakout, volume filter passed, entered); open positions; recent trades as a bar strip in % with the
  balance line in USD (Day / Week / All); today's signals and skips; the event log.
- **Settings on `/live`** (risk % per trade, daily stop %, symbols) can be changed **only while the bot is
  stopped**; Start passes them to the bot.
- **Pause** (rule set by the user, 2026-10-17): a breakout that comes while paused is skipped for that
  day (logged "paused"); resuming never enters it late, only later signals.
- **Times on the Live page in Swiss time** (Europe/Zurich, labelled "CH"; user, 2026-10-17); status.json
  and the logs stay in UTC.
- **Top bar links** (user, 2026-10-17): Backtest opens the newest run's results (no run list yet); Risk
  stays greyed out until the Risk page exists.
