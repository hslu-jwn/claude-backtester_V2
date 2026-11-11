# R022 independent review packet

Date: 2026-11-05  
Reviewer: reusable quantitative-skeptic research sub-agent (`gpt-5.6-terra`, medium)  
Artifact: `strategies/drafts/M15_REALIZED_SEMIVARIANCE_IMBALANCE_BATCH__v0.1.0.json`  
Bound SHA-256: `a1f1c26471b8be419e760a88ab4cb8bb75df616fd0097b21ba42de372f2b9085`

## Verdict

Suitable for V2 compatibility preflight; not queue-ready. No run or holdout is authorized.

The skeptic confirmed that two 60-return windows ending 15 returns apart have a 75-return union and
therefore require exactly 76 consecutive closes. Both imbalance values are fully observed at the
signal boundary while ATR is frozen through t-1. Zero-variation, threshold equality, persistence,
and direct extreme-sign-flip semantics match the Boolean rule. The four-cell grid, common fills,
state, risk and gates, plus `344+4=348` ledger are coherent. R022 is mechanically distinct from the
return, wick, M15 close-sign and efficiency families; maximum single-return variance share and
invalid/zero-window diagnostics expose one-jump and microstructure sensitivity. Liu et al. remains a
non-transferable daily Chinese-commodity boundary, not direct validation.
