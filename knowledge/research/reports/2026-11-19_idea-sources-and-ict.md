# Idea sources after the library, and ICT implementation status (2026-11-19)

Short report for the user (fusion run, Mode=auto). Facts from `research/ledger.csv`, `docs/confluences.md`,
`docs/HANDOFF.md`; no new data look.

## A. Where new strategy ideas can come from

What produced our only passes: Strategy 20 / I-83 (Binance taker flow: non-price, many names, cross-sectional) and
I-109 (Treasury month-end: a forced buyer on a known date). Books and web harvests mostly return published effects
that have decayed below our costs. Ranked by expected yield per Codex hour:

| Rank | Source | Why | Cost / blocker |
|---|---|---|---|
| **1 (pick)** | **Exchange / venue non-price data with a forced counterparty** (crypto first: Deribit options DVOL and expiry open interest, Binance / Bybit open interest and liquidations, cross-venue funding; CFTC COT; Treasury auction and index-extension calendars) | same kind of data as our two passes; free APIs; our Binance and FRED pipelines already exist | Codex terra for loaders; history depth varies (liquidations often only forward) |
| 2 | **Start forward collectors now** (Binance book depth and liquidation stream, FTMO spreads / positioning, IBKR fills once the account exists) | data no one has historically; zero multiplicity until read; the clock only starts when we start | a small always-on job on this PC (no server in dispatches) |
| 3 | **Fusions of our own components** (this run) | cheap, uses measured gross edges; honest only if pre-registered and counted | multiplicity; most components are near zero gross, so most fusions add noise |
| 4 | **Paid intraday futures data** (Databento / CME: ES, NQ, ZN, CL tick or 1-minute with real futures costs) | reopens goal 1 off the FTMO CFD wall (M11) and parked cards (I-125 intraday VX) | the user declined paid data on 2026-11-18 |
| 5 | **Forward-log findings** (Strategies 19 / 20, shelf, I-109 weekend month-ends) | clean out-of-sample evidence | slow: first rows 2026-12-03, power after ~52 weeks |
| 6 | **Regime splits of live streams** | tempting, but every split is a rescue-shaped look on a spent test period (M8); only as a pre-registered sizing rule | low power, high multiplicity |

## B. ICT concepts

### What I can implement alone from `docs/confluences.md` and the detectors

Already built and fully specified (detector + tests in `src/backtester/detectors/`): swings, BOS, trend (BOS-defined,
4H overall), strong-move filter, validation (tap / confirm / invalidate), **FVG**, **breaker block**, BPR, equilibrium,
overlapping-confluence ranking, toggles. A new ICT strategy can be assembled from these without new rules.

Partly specified: **liquidity sweep** (built behind off-by-default settings, spec says "being reworked"), **order
block** (two rule sets; the code runs the first one), **SMT** ("future"; a version was screened as I-88).
Not specified at all: **killzones** (no section in the spec; only strategy-specific session windows exist).

### Rules that are ambiguous and need you (quotes)

1. Sweep tolerance: "differences that are not significant are ignored (⚙️ setting; threshold unit and value to be
   agreed before implementing)". Unit (ATR share? points?) and value.
2. Sweep two-close rule: the text says "if two consecutive candles close beyond the level ... it was no sweep", but
   the code state says `two_closes_cancel` is "off by default until the user has settled them on the chart". Is the
   rule in force (on) or not?
3. Sweep close: "⚙️ Whether a close above the level still counts (default: yes)". Keep yes?
4. Order block: "⏸ Not in use ... the code still uses the first version (ROADMAP 2.6 ...)". Which version is the
   canonical OB for new strategies: v1 (leg into the latest swing at any BOS) or the 2026-10-06 sweep-based v2?
5. OB range: "wicks for now; sometimes only the bodies matter, possibly a setting later". Wicks or bodies?
6. Strong-move filter: "Order blocks no longer use it ... the code still has the OB switch (default on)". Off for OBs?
   And "n still to be swept".
7. Doji share: `doji_range_share` "default 0 = off ... until the user has looked at it on the chart". Turn on (0.10)
   for 4H and above?
8. SMT: "requires an overall market bias": which bias (4H trend? daily?), which symbol pairs, which swings compared
   (latest confirmed on each, within how many candles of each other)?
9. Killzones: which windows and in which city time (common ICT: Asia 20:00-00:00, London 02:00-05:00, NY AM
   07:00-10:00, NY PM 13:30-16:00 New York time), and what a killzone does (entry allowed only inside? the sweep must
   happen inside?).

### Where I need examples marked on the chart

- Sweeps: ~10 cases on NAS100 / XAUUSD 5m and 30m, marked "sweep" vs "not a sweep" (decides 1-3).
- Order blocks v2: ~5 cases with the zone drawn as you would trade it (decides 4-5).
- SMT: ~5 cases on NAS100 / US500 with the two swings you compare (decides 8).
- Doji share: 2-3 4H candles you consider dojis and 2-3 you do not (decides 7).
Killzones need only the times, no chart.

### What the data says so far (to set expectations)

Every ICT component we measured is at zero gross before costs: session-zone sweep S01 -0.047 R gross, NY index sweep
S02 +0.018 R (net -0.037), sweep study 2026-10-13 (~35,000 sweeps) drift 0.0 +- 0.02 ATR, FVG levels vs matched random
levels +0.2 bp (t 0.86, I-94), previous-day raid I-91 t -0.87, power of three I-92 t -1.59, SMT I-88 t -0.17. So no ICT
component qualifies as "measured gross edge" for the fusion run; settling the rules above would let us test your exact
version, not rescue the measured ones.
