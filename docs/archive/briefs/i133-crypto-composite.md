# Brief: I-133 crypto taker-flow + funding-carry composite screen

Model: Codex `gpt-6.1-terra` medium. Write task. Create ONE file:
`research/screens/2026-11-19_i133_crypto_composite_screen.py`. Touch nothing else. No commits, no servers, no
credentials. Do NOT run the `run` or `test` modes (Opus runs them after reading the code); you MAY run `--selfcheck`
and `power`.

## Rule (source of truth: `knowledge/ideas.md` › I-133, including assumptions A1-A4)

Reuse `research/screens/2026-11-14_i78_crypto_wide_factors_screen.py` (load it with importlib exactly as
`research/screens/2026-11-17_i100_wide_carry_screen.py` does; use `i78.load`, `i78.mondays`, `i78.week_rows`,
`i78.tstat`, `i78.END`). Development = 2020-01-01 .. 2023-12-31 (i78's END; no bar after it). Start Monday 2020-05-04
(as I-100).

Each Monday m:
1. `w = i78.week_rows(k, fund, m)` (Strategy 20's eligible names; columns sym, flow, ret, fund ...). Do NOT exclude
   the 37 seen names (unlike I-100: the full universe here).
2. Funding signal per name = funding settled in (m - 7 days, m] (exactly I-100's `sig`, in rate units); a name needs
   funding history with the first settlement <= m - 7 days (I-100's `ok`). Drop names without it or with NaN flow.
   Skip the week if fewer than 40 names remain (A3).
3. z_flow = (flow - mean) / sd over the week's names; z_carry = -(sig - mean) / sd (A2: long low funding);
   population or sample sd, either, but the same everywhere; a week with sd 0 in either is skipped.
   composite = (z_flow + z_carry) / 2 (A4).
4. Sort by (composite, sym) ascending (mergesort, as i78.spread); n = len // 5; long the top n, short the bottom n.
5. Week gross bp = mean(ret of longs) - mean(ret of shorts) - mean(fund of longs) + mean(fund of shorts)
   (`fund` in week_rows is the funding a LONG pays, in bp; check this sign against i100's `carry`: there gross =
   price + hi.fund.mean() - lo.fund.mean() with lo long, hi short). Net = gross - 20 bp.

## Modes

- `--selfcheck`: an assert-based check on a tiny hand-built week (5 names x 2 signals) that the composite, the legs
  and the funding sign come out as written by hand. Print "selfcheck OK".
- `power`: signal-free line: 200 draws, each week's names in random order, quintile spread of `ret` (price only);
  print the weekly sd mean, the number of weeks, se, and the net mean t 3.0 needs. No signal is read.
- `run` (development): print weeks, eligible names min / median / max; net mean, t (i78.tstat), win %, worst week;
  halves by week count (first / second half of the weeks) and each half / full-mean ratio (M7: both >= 0.25);
  doubled cost (net - 20); without the 2 best weeks; M6: the same net with every member `ret` capped at +-5,000 bp
  (keeps sign and >= half the mean?); verdict = PASSED only if all of: net > 0, t >= 3.0, both halves >= 0.25 of the
  mean, doubled > 0, without 2 best > 0, M6 holds; else KILLED with the list of failed gates.
  Reported (not gates): weekly correlation of the composite net with the flow-only quintile net (i78.spread on
  `flow`, long high) and with the carry-only net (quintile on z_carry, same universe); mean turnover per week of the
  composite vs flow-only (share of leg members that change from the previous week); placebo: z_carry permuted
  across names within each week (seed 3), its net mean and t; weeks where flow and carry legs disagree (share of
  composite long names in the carry short quintile).
  Shuffled-label control: 200 draws, composite replaced by a random permutation within each week (seeds 0..199),
  same gates; print the share of draws that PASS (must be <= 5 %).
- `test` (one-time test, 2024+): set `i78.END = pd.Timestamp("2026-10-31")` and load with
  `roots=(i78.ROOT, Path("data/cache/binance_wide_test"))` exactly as `i78.test` does (read it); only Mondays from
  2024-01-01 count. Gates: net > 0, t >= 1.8, doubled cost > 0. Verdict line must say
  "capped at UNPROVEN-POSITIVE (not blind)".

## Done =

The file exists, `--selfcheck` prints OK, `power` runs, `.venv/Scripts/ruff check <file>` is clean. No lookahead:
every signal uses only bars / settlements at or before Monday 00:00 (week_rows and the funding window already do).
Final answer: the power line output and anything in the rule you found unclear (do not guess; say it).
