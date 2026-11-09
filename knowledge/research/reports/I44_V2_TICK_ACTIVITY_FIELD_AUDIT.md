# I-44 V2 tick-activity field audit

Date: 2026-11-03  
Outcome: **implementation carries MT5 update counts, but the current canonical candle field is not
measurement-ready; I-44 remains blocked**.

This is a read-only semantic trace through V2 code and documentation. No market values were read,
no strategy was run, and no V2 file was edited.

## End-to-end trace

1. `data/adapters/mt5_adapter.py` maps MetaTrader's `tick_volume` to a generic floating-point
   `volume` column. This is a count of broker-feed updates represented by the MT5 bar, not contracts,
   notional, or signed flow.
2. `data/mt5_download.py` writes that same count to both `bid_volume` and `ask_volume`. The two
   columns are duplicates; they do not represent bid-side versus ask-side activity.
3. Histdata imports store unknown volume as `NaN`, correctly distinguishing it from a measured
   zero at cache level.
4. `data/resample.py` aggregates `bid_volume` with pandas `sum`. An all-`NaN` group returns `0.0`
   under the current aggregation, so unknown histdata activity becomes zero in a resampled candle.
   A price-free local probe confirmed this behavior.
5. `Candle.volume` carries only the resulting number, without source, provider/server identity,
   aggregation rule, or an explicit availability flag. Preferred source selection can change by
   day between MT5 and histdata.
6. The opening-range filter compares the signal candle with the same local-session minute over
   previous sessions, which is directionally appropriate clock normalization. It fails closed in
   the common no-volume cases, but mixed `NaN`/zero/source semantics are not a validated research
   measurement contract.

## Consequences

- A generic value of zero is ambiguous between unknown histdata volume, a feed/filler condition,
  and a genuine zero update count.
- `ask_volume` must not be read as ask-side updates; it is a copy of the same bar count.
- Higher-timeframe sums are counts of recorded updates only if every constituent M1 value comes
  from one stable MT5 feed and missingness remains explicit.
- A preferred-source backtest can cross feed seams, so apparent activity breaks may be data-source
  changes rather than market regimes.
- The existing ORB A/B is an outcome of one implementation and does not validate tick activity as
  a portable proxy for executed volume or reopen the closed opening-range family.

## Minimum measurement declaration

Before a research-only I-44 data study, each usable observation must carry or inherit an immutable
declaration with:

- semantic name `broker_tick_activity` and raw field `MT5.tick_volume`;
- broker, server/feed, symbol alias, snapshot identity, and source interval;
- exact M1 aggregation and higher-timeframe sum rule;
- `AVAILABLE`, `UNKNOWN`, and observed-zero states that survive resampling distinctly;
- clock and session-calendar identity, including DST handling;
- same-clock historical coverage and a prohibition on mixed-source normalization windows;
- feed/platform breakpoints and yearly distribution diagnostics; and
- explicit statement that duplicated bid/ask cache fields are not directional volume.

For an all-unknown group, aggregation must remain unknown (for example `sum(min_count=1)` semantics),
not zero. A study interval must be MT5-only or otherwise prove a single comparable update-count
source throughout; price-only fallback is forbidden.

## Remaining evidence gate

Even after the field is repaired and declared, I-44 still needs the measurement study already
specified in `I44_TICK_VOLUME_RULES_DATA_CHECK.md`: per-symbol/session coverage, same-clock
normalization, yearly stability, structural-break checks, and—where an authoritative sample is
legally available—same-horizon comparison with executed volume. That study may establish a
feed-specific activity proxy only. It cannot establish true VWAP, order flow, absorption, trade
direction, or directional edge.

No I-44 strategy draft, A/B trial, queue payload, or capability claim is authorized.

## Research missingness reference

`fixtures/i44_tick_activity_missingness.json` and `tools/i44_reference.py` now freeze the expected
measurement behavior: all-known same-source counts sum; observed zero stays zero; any unknown
constituent keeps the aggregate unknown; mixed sources fail; and a same-clock ratio requires a
complete positive reference history. The fixture also binds every non-error case to its declared
synthetic source and carries the exact measurement, aggregation, same-clock normalization, clock,
calendar, and proxy-claim identities. Only explicit `null`/`None` is missing: non-finite or negative
known activity fails before aggregation or normalization, and aggregate, historical mean, and ratio
outputs must remain finite after arithmetic. The fixture must contain exactly one structurally
derived `KNOWN_SUM`, `KNOWN_ZERO`, `ALL_UNKNOWN`, `PARTIAL_UNKNOWN`, and `MIXED_SOURCE_ERROR` case;
missing, duplicate, extra, or relabeled coverage fails. Eight
focused tests pass. This is a semantic acceptance aid, not proof that the current V2 field or any
historical interval satisfies the gate.

## Research declaration fixture

`fixtures/broker_tick_activity_declaration.json` and
`tools/validate_tick_activity_declaration.py` now make the provenance gate executable. Six focused
tests require the exact `broker_tick_activity`/`MT5.tick_volume` semantics, immutable feed/snapshot
identity, complete interval and symbol coverage, unknown-versus-zero preservation, single-source
aggregation/normalization, clock/calendar identity, structural-break diagnostics, prohibited
executed-volume claims, and stable post-resolution identity. The synthetic fixture does not repair
V2's current field or authorize the measurement study or A/B.

The declaration validator now also requires `resolved_at >= generated_at`. That rejects reversed
metadata chronology; it does not independently prove that resolution occurred before activity
values were examined, so `resolved_before_activity_values: true` remains a separate required
assertion.

The consolidated runner in `tools/validate_research_controls.py` now compares the missingness
fixture's complete measurement block with the declaration fixture. Source, aggregation,
normalization, clock/calendar, raw-field, and proxy semantics must be equivalent at the parsed JSON
level; independent passes no longer permit an undeclared feed or normalization identity to drift
between the two controls. The previously FTMO-labelled example identifiers were replaced with the
declaration's synthetic feed identity, avoiding any claim about a real broker account. This
cross-control pass remains synthetic coherence only.

The activity declaration's ID/version/hash is now anchored in the consolidated manifest and
supplied to `tick_activity_gate_errors`; changing only the fixture tuple fails the common gate.
The all-zero synthetic digest is not a content hash claim and supplies no evidence about a real
broker feed.
