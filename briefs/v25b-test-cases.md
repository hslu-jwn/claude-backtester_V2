# V2.5b test cases (before implementation)

- Chosen variant: load saved significance, Bayes, skill bounds, sensitivity,
  walk-forward, drawdown, monkey, profile, grid and Monte Carlo diagnostics.
- Other variants and plain runs: research-only values are missing; idea falls back
  to the strategy label. Missing, invalid JSON, invalid nested shapes and nonfinite
  numeric values never break cards. An available profile without skill says none.
- Cache notices creation, edits and deletion of optional files, including MC output.
- Keep verdict/test/development ordering and all existing filter cases. Each new
  sort handles missing values last; plain runs follow research for every sort.
- Cards show required chips and expanded fields, full flags and results links;
  native details start closed; no DataTable or horizontal scroll/fixed wide layout.
- Render 50 cards initially, show 50 more per click; filter/sort/reload reset paging.
- Counts, controls, tooltip, callbacks and new IDs agree; grid idea is optional,
  accepts text, rejects nontext and is persisted in research metadata.
- Run UI tests only and repository-wide ruff; browser checks belong to Opus.
