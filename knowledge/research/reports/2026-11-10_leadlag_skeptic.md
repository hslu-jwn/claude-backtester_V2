# Skeptic Review: Multi-Symbol Lead-Lag Strategies (Strategies 14–18)

**Date:** 2026-11-10  
**Status:** Pre-implementation skeptic review (prior to multi-symbol Step 1a build)  
**Author:** Antigravity (Gemini 3.8 Flash, coordinator skeptic review)  
**Scope:** Evaluation of five pre-registered lead-lag strategy specs (`docs/strategy-us_close_de_open.md`, `docs/strategy-gold_silver_leadlag.md`, `docs/strategy-btc_eth_leadlag.md`, `docs/strategy-oil_cad_leadlag.md`, `docs/strategy-usd_breadth_usdcad.md`) and their grids in `research/grids/`. Grounded in `AGENTS.md`, `knowledge/topics/cost-wall.md`, `docs/design/multi-symbol.md` Section A, and `src/backtester/engine/costs.py`.

---

## 1. Executive Summary & Ranking

Five cross-market lead-lag strategies have been pre-registered following idea harvests. Before engineering the multi-symbol snapshot infrastructure (`docs/design/multi-symbol.md` Section A) and dispatching strategy builders, this review tests each specification against the hard empirical lessons of V1/V2 (`knowledge/topics/cost-wall.md` and `docs/research-log.md`).

### The Core Tension: Microstructure Speed vs. CFD Cost Wall
Cross-market lead-lag hypotheses suffer from an inherent economic paradox:
1. **At short horizons (M1 to H1):** Information diffuses between electronically linked markets in milliseconds to seconds (via HFT triangular arbitrage and index arbitrage). Any residual gross lead-lag predictability over 1–4 hours is fractional (typically 1–3 bp), but trading costs on retail CFDs are 1–25 bp, easily consuming the edge.
2. **At long horizons (D1 / 24 hours):** While a daily stop makes transaction costs small in R (~0.01–0.03 R), markets are informationally efficient over 24-hour cycles. A delayed reaction 24 hours after an oil shock or dollar move has zero empirical support in modern markets (the cited papers studied *contemporaneous* correlations, not lagged predictive trading rules), while overnight swap (-$8.44/lot on short USDCAD) creates steady bleeding.

### Prior Ranking Summary

| Rank | Strategy | Traded / Ref | Normal Cost (R) | Double Cost (R) | Swap Risk | Trade Count (Dev) | Prior Chance | Primary Failure Mode |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **1** | **Strategy 14: US Close → German Open** (`us_close_de_open`) | GER40 / US500 | ~0.025 R | ~0.051 R | None (0 swap) | ~700 (Safe) | **Moderate (~15–20%)** | Gross move priced into DAX open / futures gap; gross R < 0.05 R. |
| **2** | **Strategy 17: Oil Shock → CAD Next Day** (`oil_cad_leadlag`) | USDCAD / USOIL | ~0.008 R + swap | ~0.016 R + swap | High (-$8.44/lot short) | ~300 (Safe) | **Low (~5–8%)** | Contemporaneous BoC effect has no delayed edge; short swap eats gains. |
| **3** | **Strategy 18: Dollar Breadth → USDCAD** (`usd_breadth_usdcad`) | USDCAD / 6 USD | ~0.008 R + swap | ~0.016 R + swap | High (-$8.44/lot short) | ~350 (Safe) | **Low (~4–6%)** | Triangular FX arbitrage prices USD moves instantaneously; no 24h lag. |
| **4** | **Strategy 15: Gold → Silver Lead-Lag** (`gold_silver_leadlag`) | XAGUSD / XAUUSD | ~0.245 R | ~0.490 R | High in EDT (-$68.05/lot) | ~220 (Borderline) | **Very Low (<2%)** | Brutal XAGUSD cost wall (~0.25 R/tr); Granger causality was 1-min, not 2-hour. |
| **5** | **Strategy 16: BTC → ETH Lead-Lag** (`btc_eth_leadlag`) | ETHUSD / BTCUSD | ~0.015 R + swap | ~0.030 R + swap | Extreme (-30% to -60%/yr) | ~120 (Fails Gate 6) | **Near Zero (<1%)** | Literature refutes shock delay; lethal FTMO crypto swap/comm; trade count < 200. |

---

## 2. Deep Dive: Strategy 14 — US Close → German Open (`us_close_de_open`)

### A. Lookahead & Timing Risks
- **Mechanism:** US500 M1 return from 15:30 to 16:00 America/New_York on day $D_s$ conditions GER40 entry at 09:00 Europe/Berlin on day $D_t$.
- **Structural Gap:** 16:00 NY is 21:00 or 22:00 UTC on $D_s$; 09:00 Berlin is 07:00 or 08:00 UTC on $D_t$. An ~11-hour overnight buffer exists. Lookahead risk from price data availability is nil: the snapshot at 09:00 Berlin strictly contains yesterday's closed US session.
- **DST Mismatch Weeks:** US and Europe shift clocks on different dates (approx. 2–3 weeks in March and 1 week in October/November). The spec correctly mandates local clock evaluation (`America/New_York` and `Europe/Berlin`). The time delta between US close and German open shifts between 10, 11, and 12 hours, but local session definitions remain valid.
- **Critical Ambiguity — The 09:00 Candle:** In the backtester's timestamping conventions, does "the candle closing at 09:00 Berlin" mean the M1 candle with open timestamp `08:59:00` (which closes at `09:00:00`), or the candle with timestamp `09:00:00` (which closes at `09:01:00`)? 
  - If `08:59:00–09:00:00` is used, entry is placed at the opening auction bell of Xetra before regular cash trading begins (often wide CFD pre-market spread).
  - If `09:00:00–09:01:00` is used, entry executes at `09:01:00`, capturing the first cash minute.

### B. Cost Realism vs. Plausible Gross Move
- **Costs (`costs.py`):** GER40 spread = 2.30 points, slippage = 0.765 points per fill, commission = $0.0. Round-turn transaction cost = $2.30 + 2 \times 0.765 = 3.83$ points. Reference price = 25,563.64 (~1.5 bp).
- **In R:** At a 0.5 daily ATR stop (~150 points in 2015–2020), cost per trade is $3.83 / 150 \approx 0.0255\text{ R}$. Under Gate 1 (costs doubled), cost is $\approx 0.051\text{ R}$.
- **Plausible Gross Move:** In F2 (last 30 minutes momentum), GER40 gross edge was $+0.012\text{ R}$; UK100 was $+0.017\text{ R}$. Both were net negative. Here, the US news has had 11 hours to be digested by FDAX futures (trading from 01:15 or 08:00 CET) and Asian bourses. The overnight cash gap is excluded by rule. To clear normal costs ($0.025\text{ R}$) and doubled costs ($0.051\text{ R}$), the post-open 30-minute cash drift must exceed $+0.055\text{ R}$ gross. This is demanding, but within the realm of possibility for cash-open rebalancing.
- **Swap:** Exits at 09:30 or 10:00 Berlin, well before 17:00 NY rollover. Zero swap risk.

### C. Expected Trade Count vs. Min-Trades Gate
- GER40 development period: 2015-01-02 to 2020-06-14 (~5.45 years, ~1,380 trading days).
- A 30-minute US500 move of $\ge 0.10\%$ occurs on approximately 50–60% of all sessions.
- Expected trades at primary cell (0.10% threshold): $\approx 700–800$ trades. Easily clears the 200 min-trades gate.
- At 0.20% threshold: expected trades $\approx 350–450$, still safely $\ge 200$.

### D. Overlap with Already Falsified Families
- F2 and F2-EU (same-index last 30 minutes) were falsified after costs (`research-log.md`).
- Calendar and index clock screens (660 and 792 cells) yielded 0 survivors on 2008–2014.
- However, cross-market overnight conditioning (US close to European open) is a fundamentally different economic mechanism with published peer-reviewed backing (Xu et al.).

### E. Missing / Ambiguous Rules Requiring Decisions
1. **Decision needed:** Clarify the exact 09:00 Berlin entry candle: is entry at the close of `08:59` (i.e. `09:00:00`) or close of `09:00` (i.e. `09:01:00`)?
2. **Decision needed:** Confirm handling of UK100 breadth override in `research/grids/us_close_de_open.toml`: UK100 cash open is 08:00 London. Does runner support per-symbol entry/exit time overrides in a single grid, or does UK100 require a distinct grid file?

### F. Control / Gate 3 Soundness
- Gate 3 tests signal net R against an all-days baseline (long and short) matched to the signal's direction mix on non-signal days.
- Sound: correctly eliminates unconditional European morning cash-open drift.

---

## 3. Deep Dive: Strategy 15 — Gold Impulse → Silver Delayed Continuation (`gold_silver_leadlag`)

### A. Lookahead & Timing Risks
- **Mechanism:** XAUUSD H1 log return evaluated at H1 closes during 12:00–19:00 UTC; enters XAGUSD at the same H1 mark for a 120- or 180-minute hold.
- **Timing & Lookahead:** Evaluated at completed H1 closes; bounded snapshot ensures no lookahead.
- **Economic Latency Reality:** Gold and silver trade simultaneously on CME Globex 23 hours a day. The contemporaneous correlation between gold and silver over an H1 bar is 0.85–0.92. When gold moves $\ge 0.50\%$ in an hour, silver has already moved simultaneously during that exact same hour. The spec assumes silver has an *additional delayed continuation* over the *subsequent 2–3 hours*. The cited World Gold Council study documented Granger causality at the **1-minute** interval, not a 2-hour delayed reaction. Expecting an hourly delayed reaction in an electronically liquid commodity is microstructurally unsound.

### B. Cost Realism vs. Plausible Gross Move
- **Costs (`costs.py`):** XAGUSD spread = 0.049, slippage = 0.0245, commission = 0.000007 per side ($0.0014\%$ round turn), contract size = 5,000, reference price = 64.58.
- **The XAGUSD Cost Trap (`cost-wall.md` line 89–90):** Silver prices in 2015–2020 averaged \$15–\$20/oz, while daily ATR was $\approx \$0.35–\$0.50$.
  - Round-trip transaction cost = $0.049 + 2 \times 0.0245 = 0.098$ price units.
  - At a 1.0 daily ATR stop ($\approx \$0.40$), the transaction cost alone is $0.098 / 0.40 \approx \mathbf{0.245\text{ R}}$ per trade!
  - Under Gate 1 (doubled costs), cost is $\mathbf{0.490\text{ R}}$ per trade!
  - A strategy paying 0.25 R to 0.49 R per trade requires a massive gross edge of $+0.30\text{ R}$ to $+0.55\text{ R}$, which does not exist in any liquid CFD in this repository.
- **Rollover Swap Violation in EDT:** Spec Assumption 6 claims: "completely avoiding the daily maintenance break and avoiding overnight rollover swap at 17:00 New York." **This is false during US Daylight Saving Time (EDT).** In summer, 17:00 NY is 21:00 UTC. An entry at 19:00 UTC with a 180-minute hold exits at 22:00 UTC, which crosses 21:00 UTC and incurs overnight swap! Long swap on XAGUSD is $-\$68.05$ per lot per night!

### C. Expected Trade Count vs. Min-Trades Gate
- Active window: 12:00–19:00 UTC (8 possible evaluation hours).
- Concurrency rule: `max_open_positions = 1`. A 120-minute hold blocks signals for the next 2 hours.
- A $\ge 0.50\%$ H1 gold move occurs on ~5–8% of liquid hours. Across ~1,700 development days, accounting for 2-hour blocking, expected trades are $\approx 200–260$.
- High risk of falling below the 200 min-trades gate, particularly for 180-minute holds or if missing data bars are skipped.

### D. Overlap with Already Falsified Families
- Gold session rules were marked "Dead" in `research-log.md` line 123.
- `cost-wall.md` explicitly warns: "Stop proposing: ... gold session rules".
- Gold trend following (Strategy 4) was killed by swap (`cost-wall.md` line 16).

### E. Missing / Ambiguous Rules Requiring Decisions
1. **Decision needed:** Fix the EDT rollover swap leak: either restrict `active_to` to 18:00 UTC (so 180m holds exit by 21:00 UTC), or explicitly allow and model swap.
2. **Decision needed:** Clarify ATR daily boundary: does XAGUSD daily ATR use UTC 00:00–24:00 or NY 17:00–17:00?
3. **Decision needed:** Gate 4 (Breadth) specifies symmetric lead-lag (silver $\to$ gold), but `research/grids/gold_silver_leadlag.toml` lists only `symbols = ["XAGUSD"]`. How is the breadth run configured?

### F. Control / Gate 3 Soundness
- Uses disjoint baseline across 12:00–19:00 UTC. Conceptually sound for controlling intraday precious metals drift, but unable to rescue a 0.25 R cost deficit.

---

## 4. Deep Dive: Strategy 16 — BTC Impulse → ETH Delayed Continuation (`btc_eth_leadlag`)

### A. Lookahead & Timing Risks
- **Mechanism:** BTCUSD H1 percentage return evaluated 24/7 across all UTC hours; enters ETHUSD for 180 or 240 minutes.
- **Timing & Lookahead:** Evaluated at completed UTC H1 closes. Snapshot bounded by `now`. Low lookahead risk.
- **Data Gap Asymmetry:** Early MT5 data (2018–2020) had Saturday feed pauses on FTMO, whereas Binance traded 24/7. Spec skips missing bars correctly.

### B. Cost Realism vs. Plausible Gross Move
- **The Crypto Cost Reality (`costs.py`):**
  - FTMO crypto commission: `FTMO_CRYPTO_COMMISSION_PCT_SIDE = 0.000325` (3.25 bp per side = 6.5 bp round-turn).
  - Gate 1 doubled commission: **13.0 bp** round turn!
  - ETHUSD spread = 0.66, slippage = 0.30 per fill. At reference price 2,498, spread + slippage adds another 5.0 bp (10.0 bp doubled).
  - Total transaction friction: **11.5 bp normal, 23.0 bp doubled.**
  - **Lethal Swap:** `swap_long_pct_year = -0.30`, `swap_short_pct_year = -0.30` (-30% per year on both sides!).
  - Under Gate 1, swap is **-60% per year**. Crossing 17:00 NY rollover incurs an immediate penalty of $\approx 8.2\text{ bp}$ (or $24.6\text{ bp}$ on Friday triple swap).
- **Literature Refutation:** The spec's own cited literature (Chernoff, MDPI 2024) specifically found **no delayed cross-asset adjustment after extreme shocks**. In C3 (`research-log.md` line 23), crypto intraday momentum was screened out because published gross edge was 2.8 bp vs. FTMO cost of 6.5 bp.
- Here, an intraday holding window of 3–4 hours faces a 11.5–23 bp fee hurdle plus 30–60% annual financing against an academic consensus of zero delayed drift.

### C. Expected Trade Count vs. Min-Trades Gate
- Development window: 2018-01-10 to 2021-09-13 (~3.67 years, ~1,340 days).
- Primary cell: BTCUSD H1 move $\ge 2.0\%$, hold = 240 minutes (4 hours).
- With `max_open_positions = 1`, each trade locks out all subsequent signals for 4 hours.
- A $2.0\%$ H1 move on BTC is an extreme event (occurs ~100–150 times per year across 24 hours). With 4-hour blocking and 2018 weekend gaps, expected trade count is **100–150 trades**.
- **Fails Gate 6:** The spec itself concedes (lines 104–106) that the primary cell will likely generate fewer than 200 trades and report "not enough evidence".

### D. Overlap with Already Falsified Families
- C2 crypto momentum test failed on 2026-11-10 (`research-log.md` line 28): doubled costs including swap produced $-18.9\text{ R}$.
- C3 crypto intraday momentum was screened out on costs without a build.
- C1 trend following on crypto suffered severe swap drag (-30%/yr).

### E. Missing / Ambiguous Rules Requiring Decisions
1. **Decision needed:** Section `## Decisions by Opus` is completely blank (line 161).
2. **Decision needed:** Clarify Gate 6 failure handling: if the primary cell fails to reach 200 trades (highly probable at 2.0% threshold), does the family immediately count as falsified?
3. **Decision needed:** Define ATR calculation on 24/7 crypto: does Wilder ATR(14) use UTC midnight bars (00:00–24:00) including Saturday/Sunday stubs?

### F. Control / Gate 3 Soundness
- Disjoint control across 24/7 H1 closes properly handles secular crypto bull/bear drift, but cannot overcome negative gross expectancy and extreme fees.

---

## 5. Deep Dive: Strategy 17 — Oil Shock → CAD Next Day (`oil_cad_leadlag`)

### A. Lookahead & Timing Risks
- **Mechanism:** USOIL daily return evaluated at 21:00 UTC daily close; enters USDCAD at 21:00 UTC close for a 720- or 1440-minute hold.
- **The 21:00 UTC vs. 17:00 NY Clock Issue:**
  - 21:00 UTC is 17:00 America/New_York during US Summer Time (EDT), but **16:00 America/New_York** during US Winter Time (EST).
  - In summer (EDT), 21:00 UTC coincides exactly with the FX rollover and the CME energy maintenance halt.
  - In winter (EST), 21:00 UTC is 16:00 NY: USOIL is still actively trading for another hour (until 17:00 NY), and FX rollover occurs 60 minutes later.
  - A trade entered at 21:00 UTC in winter incurs overnight swap after holding for just 60 minutes!
  - If "daily bar" is defined at 21:00 UTC, the bar boundary shifts relative to physical market close between seasons.

### B. Cost Realism vs. Plausible Gross Move
- **Base Costs (`costs.py`):** USDCAD spread = 5.1e-5, commission = $5.00/lot round turn, slippage = 1.5e-5. Round-trip transaction cost is ~0.95 pip (~0.7 bp). At a 1.5 daily ATR stop (~120 pips), base cost in R is very low: $\approx \mathbf{0.008\text{ R}}$!
- **The Asymmetric Swap Trap:**
  - In `costs.py`: `swap_long_per_lot = +0.4792`, `swap_short_per_lot = -8.4426`.
  - When USOIL surges $\ge +2.0\%$, the economic signal is CAD appreciation $\to$ **SHORT USDCAD**.
  - Short USDCAD pays $-\$8.44$ per lot per night (and $-\$25.32$ on Wednesday rollover).
  - On a 1.5 ATR stop (~120 pips, risking ~$850/lot), one night of short swap is $\approx \mathbf{0.010\text{ R}}$, and Wednesday rollover is $\approx \mathbf{0.030\text{ R}}$.
  - Doubled swap under Gate 1 makes short swap $-\$16.88$/night ($\approx 0.020\text{ R}$ to $0.060\text{ R}$).
- **The Empirical Flaw (Contemporaneous vs. Lagged):**
  - The cited Bank of Canada (2016) paper studied *contemporaneous* daily co-movements.
  - In modern foreign exchange markets, oil price shocks are priced into USDCAD continuously throughout the trading day. There is zero published evidence that USDCAD drifts directionally over the *subsequent 24 hours* after an oil move has closed.
  - In `research-log.md` lines 76–79, USD pairs showed total daily drift of only 1.2–1.9 bp. Swap alone will extinguish any sub-2 bp edge.

### C. Expected Trade Count vs. Min-Trades Gate
- Development period: 2015-01-02 to 2021-09-13 (~1,700 trading days).
- Daily USOIL $|r| \ge 2.0\%$ occurs on ~30–35% of days (~500–600 sessions).
- With 1440-minute hold blocking consecutive days, expected trades are $\approx 280–350$.
- Safely satisfies the 200 min-trades gate.

### D. Overlap with Already Falsified Families
- Strategy 12 `energy_report` (EIA inventory shocks on oil): tested 2026-11-10 (`research-log.md` lines 15–17); falsified on development (all 8 cells negative, $-7.5\text{ R}$).
- Commodity momentum and event drift across all tested setups have shown zero persistence beyond intraday price discovery.

### E. Missing / Ambiguous Rules Requiring Decisions
1. **Decision needed:** Clarify roll jump filtering: Spec Assumption 4 states "Any USOIL bar with price <= 0 or roll jump ... is skipped". How is a contract roll jump detected algorithmically? Must the builder use `ImportConfig.explained_jumps` dates, or apply an absolute return ceiling?
2. **Decision needed:** Standardize the evaluation clock: should the daily evaluation be fixed at 21:00 UTC, or at 17:00 America/New_York (session close)?
3. **Decision needed:** Resolve Gate 4 (Breadth): spec suggests "UKOIL ... or CADJPY as alternative cross". Which one is the binding gate?
4. **Decision needed:** Section `## Decisions by Opus` is completely blank (line 176).

### F. Control / Gate 3 Soundness
- Disjoint comparison against an all-days 21:00 UTC USDCAD hold isolates the oil-conditioned effect from multi-year CAD macro trends (e.g. the 2015 oil/CAD collapse). Clean methodology.

---

## 6. Deep Dive: Strategy 18 — Dollar Breadth → USDCAD (`usd_breadth_usdcad`)

### A. Lookahead & Timing Risks
- **Mechanism:** At 21:00 UTC, calculates daily log returns across 6 USD majors (EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCHF); if $\ge 4$ agree and mean return $\ge 0.20\%$, enters USDCAD for 720 or 1440 minutes.
- **Timing & Lookahead:** All 7 symbols are FX pairs with identical market clocks. Snapshot at 21:00 UTC contains completed daily bars for all symbols. Zero lookahead risk.
- **Same Clock Ambiguity:** 21:00 UTC is 17:00 NY in summer, but 16:00 NY in winter (1 hour prior to rollover).

### B. Cost Realism vs. Plausible Gross Move
- **Transaction Costs:** Identical to Strategy 17: base round-turn friction on USDCAD is $\approx \mathbf{0.008\text{ R}}$ at 1.5 daily ATR stop.
- **Swap Asymmetry:** Long USDCAD receives $+0.48$/lot; short USDCAD pays $-\$8.44$/lot ($-\$25.32$ on Wednesday). Short trades face a significant financing headwind.
- **The Severe Theoretical Barrier:**
  - Modern FX spot markets are the most liquid, electronically integrated markets in the world. Triangular arbitrage bots (e.g. EUR/USD $\times$ USD/CAD $\div$ EUR/CAD $= 1$) enforce instantaneous cross-currency pricing in microseconds.
  - The premise that broad USD re-pricing across EUR, GBP, JPY, AUD, NZD, and CHF will take **an additional 24 hours** to diffuse into USDCAD contradicts market microstructure realities.
  - The Bank of Canada paper documented that a multilateral USD index is contemporaneously correlated with CAD; it did *not* find a 24-hour delayed drift.
  - In `cost-wall.md` line 70–71, the mandate states: "Stop proposing: ... FX relative-strength / basket rules (highest turnover, 0.2 R per leg)". While this strategy trades only one leg, the underlying signal is an FX basket rule.

### C. Expected Trade Count vs. Min-Trades Gate
- Development period: 2015–2021 (~1,700 trading days).
- Condition: $\ge 4$ of 6 pairs agree, and mean basket return $|R_{USD}| \ge 0.20\%$.
- A $0.20\%$ daily move on a diversified USD basket is roughly 0.4–0.5 standard deviations. Occurs on ~35–45% of trading days.
- Expected trades with 24-hour lockout: $\approx 300–400$. Safely passes Gate 6.
- Risk: "Strict universe completeness" requires all 6 reference pairs to have valid bars. Histdata minor gaps could drop 5–10% of sessions.

### D. Overlap with Already Falsified Families
- FX relative strength / basket candidates were rejected in the M15 triage (`cost-wall.md` line 70).
- F1X (cross-currency European hours drift) showed that gross currency patterns exist (~0.015–0.025 R) but are completely absorbed by costs.
- Hourly profiles of 6 USD pairs (`research-log.md` line 76) confirmed USD drift is only 1.2–1.9 bp across an entire day.

### E. Missing / Ambiguous Rules Requiring Decisions
1. **Decision needed:** Clarify Gate 4 (Breadth): spec states "Leave-one-out breadth test ... or cross-pair breadth test (same USD breadth applied to AUDUSD or USDCHF)". Which test is binding?
2. **Decision needed:** Missing bar tolerance in the reference universe: if 1 of the 6 pairs is missing an M1 bar at 21:00 UTC due to broker reporting glitch, is the day aborted or can a 5-of-6 fallback operate?
3. **Decision needed:** Section `## Decisions by Opus` is completely blank.

### F. Control / Gate 3 Soundness
- Disjoint comparison against an all-days USDCAD 21:00 UTC baseline properly separates signal predictability from broader USD multi-year drift.

---

## 7. Comparative Assessment & Ranking

### Ranking Rationale

1. **Rank 1: Strategy 14 (`us_close_de_open`) — Prior ~15–20%**
   - **Why top:** It is the *only* strategy among the five grounded in a genuine structural market friction: European cash equities are physically closed when the US market closes. Information discovery from 15:30–16:00 NY cannot be transacted in cash equities until 09:00 Berlin the next morning. It has low cost in R (~0.025 R), zero swap, published academic backing (Xu et al.) claiming net profitability, and robust trade counts (~700). Its primary risk is that FDAX futures and Asian markets absorb the shock overnight before the 09:00 cash open.
2. **Rank 2: Strategy 17 (`oil_cad_leadlag`) — Prior ~5–8%**
   - **Why second:** Base transaction cost on USDCAD is small (~0.008 R), trade count is solid (~300), and oil has a genuine macroeconomic relationship with the Canadian economy. However, the cited BoC study is strictly contemporaneous, 24-hour delay is implausible in modern liquid macro markets, and short USDCAD swap (-$8.44/lot) creates a heavy drag.
3. **Rank 3: Strategy 18 (`usd_breadth_usdcad`) — Prior ~4–6%**
   - **Why third:** Similar cost and trade count characteristics to Strategy 17, but the economic rationale of a 24-hour lag across liquid G10 currency pairs is even weaker than commodity lead-lag. Microsecond triangular arbitrage eliminates cross-pair discrepancies instantly.
4. **Rank 4: Strategy 15 (`gold_silver_leadlag`) — Prior <2%**
   - **Why fourth:** Devastated by the XAGUSD cost wall. Round-trip transaction cost is ~0.245 R (normal) and ~0.490 R (doubled). In addition, gold and silver trade simultaneously on Globex; Granger causality at the 1-minute interval does not translate to an hourly delayed continuation. Long trades crossing 21:00 UTC in summer pay -$68.05/lot swap.
5. **Rank 5: Strategy 16 (`btc_eth_leadlag`) — Prior <1%**
   - **Why fifth:** Direct academic contradiction (Chernoff specifically refuted delayed adjustment after shocks), massive transaction costs (11.5 bp normal, 23 bp doubled), punishing swap (-30% to -60%/year), and high probability of failing Gate 6 (<200 trades). It is structurally non-viable under FTMO parameters.

---

## 8. Concrete Decisions Needed by Opus Before Build

Before the multi-symbol Step 1a build and strategy implementation proceed, Opus should resolve the following explicit ambiguities:

### Global / Architectural (Step 1a)
1. **Decision needed [Global-1]: Standard Daily Bar Alignment for FX & Commodities.**  
   Strategies 17 and 18 specify daily evaluation at `21:00 UTC`, which is 17:00 NY in summer (EDT) but 16:00 NY in winter (EST). Should daily bars for FX and energy be evaluated strictly at `17:00 America/New_York` (the true session close / rollover time) rather than fixed `21:00 UTC`?
2. **Decision needed [Global-2]: Next-Open Execution Semantics.**  
   Existing single-symbol strategies execute on the candle close. Lead-lag specs refer to "close of candle, fills at close / open of next candle per engine rules". Confirm whether new strategies use standard M1 close fills or if the proposed "first-M1-open-after-signal" execution mode (`docs/design/multi-symbol.md` Section A) must be built first.

### Strategy-Specific
3. **Decision needed [Strategy 14]: 09:00 Berlin Entry Bar Definition.**  
   Does "candle closing at 09:00 Berlin" mean the M1 candle with open timestamp `08:59` (closing at `09:00:00`), or `09:00` (closing at `09:01:00`)? Recommended: `09:00` (closing at `09:01:00`) to ensure cash market liquidity.
4. **Decision needed [Strategy 14]: UK100 Breadth Execution in Runner.**  
   Confirm whether UK100 breadth (requiring London 08:00 entry and 08:30 exit) should be run via a secondary grid file (`research/grids/us_close_de_open_uk100.toml`) or via multi-symbol runner overrides.
5. **Decision needed [Strategy 15]: XAGUSD EDT Rollover Swap Leak.**  
   During EDT, a 19:00 UTC entry with a 180-minute hold exits at 22:00 UTC, crossing the 21:00 UTC (17:00 NY) rollover and incurring -$68.05/lot swap. Should `active_to` be restricted to 18:00 UTC so all trades exit before rollover?
6. **Decision needed [Strategy 15]: XAGUSD Gate 4 Breadth Implementation.**  
   Confirm how symmetric lead-lag (XAG $\to$ XAU) is executed, given that `research/grids/gold_silver_leadlag.toml` currently defines only XAGUSD as the traded symbol.
7. **Decision needed [Strategy 16]: Blank Decisions Section & Gate 6 Policy.**  
   Record formal decisions in `docs/strategy-btc_eth_leadlag.md`. If the primary cell generates fewer than 200 trades (estimated 100–150), does the candidate fail automatically on Gate 6 without a re-sweep?
8. **Decision needed [Strategy 17]: Algorithmic Definition of USOIL Roll Jumps.**  
   Define the exact algorithmic filter for USOIL contract roll jumps in `oil_cad_leadlag`: should the builder reference `ImportConfig.explained_jumps` explicitly, or filter by a daily return threshold (e.g. $|r| > 15\%$)?
9. **Decision needed [Strategy 17 & 18]: Breadth Gate Selection.**  
   For Strategy 17, is UKOIL or CADJPY the binding Gate 4 test? For Strategy 18, is leave-one-out or cross-pair (AUDUSD/USDCHF) the binding Gate 4 test? Choose exactly one per spec.
10. **Decision needed [Strategy 18]: Reference Universe Missing Bar Tolerance.**  
    If 1 of the 6 reference pairs has an isolated missing M1 candle at the 21:00 mark, does the strategy abort the trade, or is a 5-of-6 vote permitted? Recommended: strict abort to preserve invariant integrity.
