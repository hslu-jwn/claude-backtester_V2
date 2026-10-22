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
- **Warm-up history check (2026-10-17):** the terminal downloads history asynchronously, so the first
  request at start can end early. After fetching a symbol's history the bot compares the last candle's
  close with the terminal's last quote time (`symbol_info.time`); if the history ends more than 5 minutes
  before it (`BotConfig.history_tolerance_s`), it waits 3 s (`history_wait_s`) and fetches again, up to 10
  attempts (`history_attempts`). Still short: a `stale_history` warning in the log and the bot goes on; the
  next cycle fetches from the last candle and fills the gap. A weekend or closed market is fine (the quote
  time is the last quote, so it ends where the history does).

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

## Robustness rules (ROADMAP 13.1-13.5, built 2026-10-20)

- **Nothing ends the loop silently.** An unexpected error in a cycle step, a symbol's bars, an entry or an exit is
  logged (`error`) and sent to Telegram, and the bot goes on. An identical error is repeated only every 5 minutes
  (`error_repeat_s`, with the number held back). After 5 cycles with errors in a row (`error_persist_cycles`) an
  `error_persistent` message follows. A session exit that fails is retried every cycle. The demo lock and a lost
  connection keep their own handling (stop / reconnect); a `LookaheadError` (a bug) is never caught and ends the
  run. A bar that fails is reported and the rest of its batch is still fed; a failing log write never stops
  reporting or trading.
- **Emergency beats Stop:** if both files exist in the same minute, the bot closes everything (the STOP file is
  consumed too).
- **Close until flat:** emergency, FTMO breach and daily stop close every own position; up to 3 tries per cycle
  (waits 1 s, 2 s, ...), then again every cycle until none is left (`close_all_incomplete` to Telegram). After an
  emergency or FTMO breach the bot does not exit and opens nothing while an own position is open.
- **One bot only:** `results/live/bot.lock` holds the PID of the running bot (a dead PID is a stale lock). The bot
  exits with code 3 when another one holds it; the Start button refuses while it is held.
- **The bot outlives the app:** it is started by a short-lived launcher with `CREATE_BREAKAWAY_FROM_JOB` (no live
  parent, not in the app's job object), so restarting the Dash app does not stop it.
- **Lost order answer:** after an order without a clear answer the bot looks for a position with its MAGIC and the
  signal's comment; a found position is managed like any other (session exit). Unclear and nothing found: looked
  up again for 3 cycles, then skipped. An order the server accepted (DONE) is never skipped: looked up every cycle
  (comment, ticket, opening deal) until found.

## Review fixes (docs/review/live.md, 2026-10-22; safest option where the spec was silent)

- A bar counts as closed only when the terminal's last quote (`symbol_info.time`, server clock) is at or after its
  close, so a PC clock running ahead never admits a forming bar; no quote time known: the PC clock alone.
- Lots from the executable price (ask for a buy, bid for a sell) to the SL; R stays measured over the signal's
  entry-SL distance. SL / TP are rounded to the tick size; a stop on the wrong side of the price or inside the
  symbol's stops level is a skip, never sent. A partial fill is tracked with the filled lots.
- Session exit by the clock: a trade still open `exit_fallback_s` (60 s) after its session exit, because no exit
  bar came, is closed at the current quote.
- A failed MT5 query (None with an error) is never "nothing": no flat after a failed position query, an
  unconfirmed close is retried, a failed deal-history read blocks entries until the day-start balance is read.
- The daily stop is kept in `results/live/daily_stop.json` (account, FTMO day): a restart the same day stays
  blocked. PAUSE is read and an EMERGENCY file blocks entries before the start-up replay.
- A trade's money is the net of all its position's deals (entry and exit commission, fee, swap).
- The bot refuses to start with risk or daily stop outside the Live page's limits (> 0, <= 2 % / <= 5 %),
  non-finite values or a non-positive `--balance`.

## Bot data and chart (rules set by the user, 2026-10-21; ROADMAP 7.8)

- Every bot position, open or closed since the current bot start, can be opened on the chart (entry, SL, TP
  if any, exit; a rough drawing is enough).
- At start the bot brings its own symbols' MT5 cache up to yesterday from its warm-up history (no extra
  download) and launches the cache update of all other symbols in the background.
- While running it rewrites today's M1 bars of its symbols into `data/cache/live/` each minute; finished UTC
  days go into the MT5 cache. The chart reads `live/` only for days the MT5 / histdata caches lack.
- "Bot trades" chart overlay: trades since the current bot start (`status.json` `started_at`), on by default
  for the bot's symbols.
