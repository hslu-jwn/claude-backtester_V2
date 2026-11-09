# Pre-holiday equity-premium candidate scan

Date: 2026-11-02  
Decision: **reject for index-CFD research; the large-firm premium is insignificant out of sample
and much of the original timing uses excluded opening/last-hour returns**.

## Candidate boundary

The last trading day before an exchange holiday is known in advance and historically had a
positive unconditional market return. A valid current candidate would need an authoritative
historical holiday calendar, a fixed post-opening/pre-final-30-minute interval, a transferable
large-cap index effect, modern stability, and net cost room. Small-stock cross-sectional survival
cannot justify an index proxy.

## Primary evidence

- Robert A. Ariel, “High Stock Returns before Holidays: Existence and Evidence on Possible
  Causes,” *Journal of Finance* 45(5), 1990, 1611–1626,
  [publisher record/abstract opened](https://doi.org/10.1111/j.1540-6261.1990.tb03731.x).
  In 1963–1982, the eight annual pre-holiday days produced mean returns nine to fourteen times
  ordinary-day means; a 1983–1986 post-test was also examined. Hourly Dow evidence showed positive
  returns throughout the day, but the pattern began with a positive overnight/opening return and
  the last hour contributed roughly one third of the total. The study predates modern index
  futures/CFD costs and does not establish an executable interior-session net return.

- Kuan-Cheng Ko and Nien-Tzu Yang, “The Pre-Holiday Premium of Ariel (1990) Has Largely Become a
  Small-Firm Effect Out of Sample,” *Critical Finance Review* 13(3–4), 2024, 531–538,
  [publisher abstract opened](https://doi.org/10.1561/104.00000111). The authors first reproduce
  Ariel, then extend the sample through 1983–2019. The pre-holiday effect survives only among small
  firms; for large firms, pre-holiday versus ordinary-day return differences are insignificant,
  especially after 1990. This is direct adverse evidence for S&P 500/Nasdaq-100 proxy transfer.

## Admission-gate assessment

1. **Independent estimand: pass.** A predetermined holiday premium is not a price-shock or
   opening-range signal.
2. **Transferable primary evidence: fail.** The modern out-of-sample premium is a small-firm
   effect, not a large-cap index effect.
3. **Causal supported inputs: blocked.** The current contract does not publish a versioned exchange
   holiday/early-close calendar; inferring holidays from absent bars would be circular.
4. **Executable horizon: fail.** A material share of the original return occurs at the open and in
   the last hour. The source does not preregister a 10:30–15:30 New York interior interval.
5. **Cost feasibility: fail.** No modern positive large-index gross margin remains to absorb CFD
   spread, commission, and slippage.
6. **Modern stability: fail.** Large-firm significance largely disappears after the original
   sample and especially after 1990.
7. **Bounded multiplicity: fail if rescued.** Choosing holidays, early closes, indices, entry
   hours, or a small-cap proxy after the large-cap failure would create a new search family.

## Decision

Create no pre-holiday index strategy, holiday subset, early-close rule, or interior-hour scan. Do
not transfer the surviving small-firm effect to US500/NAS100, and do not use price-file gaps as a
holiday calendar. The original anomaly remains historically interesting but fails the platform's
modern stability and execution gates.

Reconsider only with independent modern evidence for a predefined large-cap index-futures
interior-session interval, an authoritative point-in-time holiday calendar, and results net of
executable costs.
