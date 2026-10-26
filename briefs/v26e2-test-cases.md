# V2.6 look/layout critical cases

- Live: fresh and threshold-boundary heartbeats keep current labels and numbers; old,
  missing or malformed heartbeats show last-seen/last-session labels without a connected
  claim. Missing status keeps the existing empty state. Display threshold defaults to five
  minutes and is adjustable independently of bot controls. Zurich dates respect DST.
- Research: partition detail tiles by displayed missing value, preserving each group's
  order and all tiles; zero is computed, partial N/N_eff remains visible; omit the fold
  when all values exist. Header chips remain unchanged.
- Chart: candle delivery calls neither strategy runs nor higher-timeframe loading;
  callbacks for trades/stats have separate outputs and cannot block the candle callback.
  Stats use the completed overlay run, suppress outcomes in unrevealed review/replay,
  and reject outdated payloads. Existing review no-peek tests must remain green.

## Browser stats regression

- Drive the registered callbacks through Dash's in-process request client: candle result,
  completed trade overlay, then all four formatted stats outputs. Cover default strategy
  and strategy 3, plus completion alongside settings/base changes and unrelated overlays.
- Retain rejection of stale ranges/settings and suppression of review/replay outcomes.
