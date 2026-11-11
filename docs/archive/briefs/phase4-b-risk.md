# Brief B-risk: user decisions B1-B3 (V2.4; changes account results, not strategy trades)

Decisions are final (`docs/review/README.md` › B, rule set by the user 2026-10-22). Update the
spec (`docs/risk-management.md`, and `docs/live-trading.md` where the bot is affected) in the
same change, with "(rule set by the user, 2026-10-22)". Test first. Do NOT edit
`src/backtester/live/`; the bot uses `risk/prop_rules.py`, so B1 reaches it through that module
(list any live line that still needs a change in your report).

- **B1 FTMO daily loss (audit 13.11; review risk #2, ui #3, live #17):** the daily-loss limit
  is `daily_loss_percent` × **initial balance**, measured as day-start balance (FTMO midnight
  Europe/Prague) minus current equity. Fix `risk/prop_rules.py`, the Monte Carlo account replay
  (`risk/monte_carlo.py`), and the Live page display (`ui/live_model.py`: used % = day loss /
  (percent × initial balance)). Existing tests that encode the old base: change their expected
  values only where they encode exactly this rule, and list each one in the report.
- **B2 Monte Carlo pass rate (13.23; risk #4, #5):** a passing day is played to its end (a later
  loss that day can still breach); unfinished attempts are reported separately (count and
  share of all attempts), pass probability = passes / finished attempts plus the unfinished
  share shown next to it. Same for the adaptive path. UI card shows the unfinished share.
- **B3 adaptive risk (risk #1):** entry decisions use only what is known at entry: each open
  trade's initial risk money, never its later result.

Done = new tests green; full suite green (output to a file: this PC's terminal stalls unread
output); `ruff check .` clean. Report per decision: tests, files, changed expectations.
