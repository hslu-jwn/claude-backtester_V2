# FX_LONDON_FIX_REV v1.0.0 development-result review

Reviewed: 2026-10-29  
Canonical result: `Shared_Interface/feedback/results/FX_LONDON_FIX_REV__v1.0.0__DEVELOPMENT__1.json`  
Experiment: `FX_LONDON_FIX_REV__v1.0.0__DEVELOPMENT__1`  
Submission SHA-256: `8ec6b914e7669cc28b3eeb1008271dae8df264453934d6ce5c099b3d70ae6263`

## Decision

**Reject the strategy family as specified in v1.0.0 on development data. Do not run the final
holdout. Do not select or redesign a rule from these results.**

This is a retained negative result, not an implementation failure. The canonical envelope is
`COMPLETED`, identifies V2 commit `39813517edcf1fe985528a96d46685b9083b9c66`, uses only the fixed
development period 2015-01-02 through 2021-09-13, declares holdout disclosure `NONE`, and carries
the exact SHA-256 of the immutable claimed submission.

## Frozen primary interpretation

The pre-result checklist froze `stop_atr_multiplier=4.0, holding_minutes=360` as the sole primary
cell. The submitted specification provides no mechanical selector among the nine grid cells.
Therefore the envelope's selected `v0007` (`5.0`, `180`) is exploratory and cannot replace the
primary cell.

The envelope establishes that **zero of all nine grid cells has positive net R**. Because the
frozen primary is one of those nine cells, its primary net-profit gate necessarily fails. That
single failure is sufficient for rejection under the preregistered rule.

The canonical envelope does not map variant IDs to all nine parameter pairs or publish the
baseline's cell-level metrics. It only embeds detailed headline and robustness values for the
post-result `v0007` selection and points to department-internal V2 artifacts. Research did not
open those artifacts. Consequently, the baseline's exact gross R, net R, halves, cost stresses,
month-end split, best-five-days removal, and stop frequency are **not recoverable from the
canonical envelope**. They must not be inferred from `v0007`.

## What the canonical result does establish

| Check | Canonical evidence | Research interpretation |
|---|---|---|
| Declared grid | 9 variant IDs; profitable share 0.0; mean -1877.22 R | Entire declared grid fails net profitability |
| Multiplicity | 9 grid variants plus 8 sensitivity rows; `variants_tried=17` | Trial total is consistent with 9 + 8 reported evaluations, though sensitivity-row details are not embedded |
| Exploratory best | `v0007`, 5 ATR / 180 min; -1043.38 R; 10,397 trades; max drawdown 1064.19 R | Deeply negative and ineligible for promotion |
| Gross mechanism on `v0007` | Pooled gross +181.0 R; 4/6 symbols predicted sign | Institutional postfix direction partly transfers before costs |
| Costs on `v0007` | Standard net -1043.4 R; 1.5x costs -1655.5 R; doubled costs -2267.7 R | Costs decisively dominate the gross effect |
| Stability on `v0007` | Halves -563.7/-479.7 R; without five best days -1229.8 R; month-end -196.4 R and other -847.0 R | Failure is broad, not a single-period or best-day artifact |
| Stops on `v0007` | 42.8% of trades | The ATR safety stop materially changes the source paper's time-exit mechanism |
| Grid robustness | 0/9 profitable; sensitivity status `sharp`; both parameters failed | No stable profitable neighborhood exists |
| Statistical diagnostics on `v0007` | Reality-check p=1.0; Bayesian mean-R interval below zero; posterior odds 0.0001516 | Diagnostics reinforce rejection; they do not validate selection |
| Matched random entries | Not run after the first rejection criterion failed | Acceptable as an early-stop economy; the omitted test cannot rescue a grid with 0/9 positive cells |
| Holdout | `NONE`; final test not run | Correct; no authorization should be requested for this version |

The primary paper's adverse transaction-cost prior is borne out: a gross postfix effect can exist
without a tradable liquidity-taking CFD strategy.

## Exploratory best-cell cost decomposition

This subsection describes `v0007` only and cannot be applied to the frozen primary cell. Using the
warning's rounded pooled gross result (+181.0 R), the exact standard net result (-1043.379 R), and
10,397 trades:

- gross expectancy is approximately **+0.0174 R/trade**;
- the resolved-cost burden is approximately **1224.38 R total, or 0.1178 R/trade**;
- net expectancy is **-0.10035 R/trade**;
- gross edge covers only about **14.8%** of the standard cost burden; under a linear cost stress,
  costs would need to fall by approximately **85.2%** merely to break even; and
- recomputing from that burden gives about -1655.57 R at 1.5x cost and -2267.76 R at 2x cost,
  matching the rounded canonical warnings (-1655.5 and -2267.7 R). This is an internal
  consistency check, not a new result.

The gross effect is also concentrated. USDCAD (+82.2 R) and EURUSD (+60.5 R) provide about 78.8%
of pooled gross R, while GBPUSD (-10.3 R) and NZDUSD (-20.4 R) have the wrong gross sign. The
four-of-six breadth threshold passes, but it should not be described as uniform cross-pair
evidence.

Month-end performance is especially adverse on a per-trade basis: approximately -0.420 R across
468 month-end trades versus -0.085 R across the other 9,929 trades. Removing month-end would still
leave roughly -847 R, so it cannot rescue the rule. All figures in this subsection inherit the
canonical warning's rounding and selected-cell limitation.

## Integration assessment

Successful portions of the pilot:

- immutable submission identity and SHA-256 survived claim, feedback, execution, and result;
- implementation/testing feedback and a terminal development result were published canonically;
- the fixed development/test boundary and holdout lock were respected;
- the null result was retained rather than hidden.

Remaining integration defects:

1. The result says feedback `FB_FX_LONDON_FIX_REV_20261028T134544Z_1abf` is unanswered, but the
   canonical research reply `FB_FX_LONDON_FIX_REV_REPLY_20261028T151021Z_RESEARCH` answered both
   points and confirmed real rollover swap plus the missing-bar fallback.
2. A terminal completed result exists while the immutable payload remains in
   `Shared_Interface/queue/claimed/`; no corresponding completed-stage payload exists.
3. The canonical result omits the frozen primary cell's parameter mapping and cell-level review
   metrics, so a research consumer cannot independently apply every preregistered gate without
   crossing into V2-owned artifact paths.

These issues do not change the scientific rejection and do not justify a rerun. They are reported
through canonical feedback so the integration trail can be annotated and the queue lifecycle can
be completed safely.

## Final disposition

- Research status: **development failed / rejected**.
- Strategy-registry envelope status: `COMPLETED` (the canonical run status, not profitability).
- Final holdout: prohibited for v1.0.0.
- Same-data redesign: prohibited.
- New specification: not warranted from these results; only genuinely independent evidence could
  reopen the family.
