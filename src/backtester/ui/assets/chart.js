/* Chart page in the browser: TradingView Lightweight Charts + our drawings.
   Spec: ROADMAP.md › 4.0a. Data comes from ui/chart_data.py through Dash stores; the
   functions at the bottom are Dash clientside callbacks (window.dash_clientside.chart).

   - The chart is created once and kept: a new range / timeframe only calls setData.
   - Candles sit at logical index x (their position in the loaded range), the same x the
     server uses for drawings, so a drawing's x converts with logicalToCoordinate.
   - One series primitive draws everything that isn't a candle: session lines (below the
     candles), boxes, line segments, markers and labels (above them), culled to the
     visible range. Hover: the nearest hover area / marker within HOVER_PX of the pointer.
   - Overlays: drawings of every loaded type are kept per type; the overlay switch, the
     type panel and its sub-entries only show / hide them. Types not loaded yet for this
     range and filter setting are requested from the server (store chart-need).
   - Replay: the server sends deltas (new candles, added / removed drawings, badges); a
     delta that doesn't start at our cursor is dropped and a reload is requested.
   Nothing here computes trading logic; it only draws what the server sent. */
(function () {
  "use strict";

  const HOVER_PX = 20; // like Plotly's hover distance
  const FOCUS_BEFORE = 60; // candles shown before a focused trade's entry ...
  const FOCUS_AFTER = 30; // ... and after its exit
  const GOTO_MAX_VISIBLE = 500; // "Go to" keeps the zoom up to this many visible candles ...
  const GOTO_VISIBLE = 120; // ... else shows this many
  const EXTEND_DEBOUNCE_MS = 120; // wait for the pan / zoom to settle before asking for more
  const DETAIL_PX = 3;// narrower candles: no markers / labels (unreadable, slow to draw)
  const DASHES = { solid: [], dot: [3, 3], dash: [9, 9] }; // Plotly's patterns at width 1
  const KIND_ORDER = { bf: 0, bo: 1, l: 2, m: 3, t: 4 }; // fills, outlines, lines, markers, labels
  const S = {
    chart: null, series: null, prim: null, el: null,
    legend: null, badgesEl: null, tip: null,
    key: null, cursor: -1, times: [], spreads: [], digits: 5, tfmin: 5,
    symbol: "", tf: "", replay: false, picking: false,
    sessions: [], showSessions: true,
    types: {},          // type -> Map(id -> {d, n})
    index: new Map(),   // id -> type
    order: [],          // overlay types in drawing (registry) order
    loaded: new Set(),  // types whose drawings are at our cursor
    filters: null,      // filter setting the loaded drawings belong to
    selected: new Set(), parts: new Set(), overlaysOn: false,
    badges: {}, messages: [],
    sorted: null,       // cached draw list
    span: null,         // replay span {left, right} in minutes
    spanTimer: null, viewTimer: null, rangeTimer: null, nonce: 0,
    drawn: {},          // performance.now() when each payload kind was last applied
    asked: new Set(),   // "key|side" of the edge loads already requested for this range
    extendTimer: null,
    orderDraw: null,    // the order's drawings {key, items} (a trade focus, ROADMAP 7.6)
    inspections: [],
  };

  // --- helpers ------------------------------------------------------------------------

  function setProps(id, props) {
    const dc = window.dash_clientside;
    if (dc && dc.set_props) dc.set_props(id, props);
  }

  function fmt(p) {
    return p == null ? "" : Number(p).toFixed(S.digits);
  }

  function x1Of(d) {
    return d.x1 == null ? S.cursor : d.x1; // live: to our latest candle
  }

  function kindOf(d) {
    if (d.k === "b") return d.f ? "bf" : "bo";
    return d.k;
  }

  function isShown(type, d) {
    if (!S.overlaysOn || !S.selected.has(type)) return false;
    return d.p == null || S.parts.has(type + "." + d.p);
  }

  function drawList() {
    if (S.sorted) return S.sorted;
    const out = [];
    for (const type of S.order) {
      const m = S.types[type];
      if (!m) continue;
      const list = [];
      for (const { d } of m.values()) if (isShown(type, d) && d.k !== "h") list.push(d);
      list.sort((a, b) => KIND_ORDER[kindOf(a)] - KIND_ORDER[kindOf(b)]);
      out.push(...list);
    }
    if (S.orderDraw && S.orderDraw.key === S.key) { // the opened trade's order: on top of the overlays
      const items = S.orderDraw.items.filter((d) => d.k !== "h");
      items.sort((a, b) => KIND_ORDER[kindOf(a)] - KIND_ORDER[kindOf(b)]);
      out.push(...items);
    }
    S.sorted = out;
    return out;
  }

  function invalidate() {
    S.sorted = null;
    if (S.prim && S.prim.requestUpdate) S.prim.requestUpdate();
  }

  // --- loading bar ----------------------------------------------------------------------
  /* A thin bar at the top of the chart pane (#chart-bar), 0-100 %. Chart load: one server
     request, so staged: request sent (cfg.progress_sent), candles received
     (cfg.progress_received), overlays drawn (100); between the stages it creeps slowly
     towards the next one. */
  const BAR_CREEP_MS = 150; // creep step
  const BAR_CREEP_SHARE = 0.06; // share of the remaining way covered per step
  const BAR_STAGE_CAP = 0.92; // the creep stops at this share of the way to the next stage
  const BAR_GIVE_UP_MS = 30000; // a load that never reports back hides the bar
  const BAR_HOLD_MS = 250; // the full bar stays this long, then fades out
  const BAR_FADE_MS = 350;
  const P = { stage: null, pct: 0, cap: 0, creep: null, giveUp: null, hide: null };

  function barDraw(pct, on) {
    const bar = document.getElementById("chart-bar");
    const fill = document.getElementById("chart-bar-fill");
    if (!bar || !fill) return;
    clearTimeout(P.hide);
    const shown = pct > 0 || on;
    fill.style.transition = pct < (parseFloat(fill.style.width) || 0) ? "none" : ""; // never back
    fill.style.width = Math.max(0, Math.min(pct, 100)) + "%";
    bar.classList.toggle("on", on && shown);
    const label = document.getElementById("chart-bar-pct");
    if (label) label.textContent = on ? Math.round(pct) + " %" : "";
  }

  function barStop() {
    clearInterval(P.creep);
    clearTimeout(P.giveUp);
    P.creep = P.giveUp = null;
  }

  /* Go to stage `pct`; the creep then runs slowly towards `next` (the following stage). */
  function barStage(stage, pct, next) {
    barStop();
    P.stage = stage; P.pct = pct;
    barDraw(pct, true);
    P.creep = setInterval(() => {
      const top = pct + (next - pct) * BAR_STAGE_CAP;
      if (P.pct < top) {
        P.pct += (top - P.pct) * BAR_CREEP_SHARE;
        barDraw(P.pct, true);
      }
    }, BAR_CREEP_MS);
    P.giveUp = setTimeout(barDone, BAR_GIVE_UP_MS);
  }

  function barDone() {
    barStop();
    if (P.stage === null) return;
    P.stage = null;
    barDraw(100, true);
    P.hide = setTimeout(() => {
      const bar = document.getElementById("chart-bar");
      if (bar) bar.classList.remove("on"); // fades out
      P.hide = setTimeout(() => barDraw(0, false), BAR_FADE_MS);
    }, BAR_HOLD_MS);
  }

  function barLoading() { // the request for new candles is on its way
    const cfg = S.cfg || { progress_sent: 10, progress_received: 60 };
    barStage("loading", cfg.progress_sent, cfg.progress_received);
  }

  function barReceived() { // candles are in; overlays may follow
    barStage("overlays", S.cfg.progress_received, 100);
  }

  // --- drawing primitive --------------------------------------------------------------

  function shapePath(ctx, shape, x, y, size) {
    const r = size / 2;
    ctx.beginPath();
    if (shape === "circle") {
      ctx.arc(x, y, r, 0, 2 * Math.PI);
    } else if (shape === "triangle-up") {
      ctx.moveTo(x, y - r); ctx.lineTo(x + r, y + r * 0.8); ctx.lineTo(x - r, y + r * 0.8);
      ctx.closePath();
    } else if (shape === "triangle-down") {
      ctx.moveTo(x, y + r); ctx.lineTo(x + r, y - r * 0.8); ctx.lineTo(x - r, y - r * 0.8);
      ctx.closePath();
    } else if (shape === "star") {
      for (let i = 0; i < 10; i++) {
        const a = -Math.PI / 2 + (i * Math.PI) / 5;
        const rr = i % 2 ? r * 0.45 : r;
        ctx.lineTo(x + rr * Math.cos(a), y + rr * Math.sin(a));
      }
      ctx.closePath();
    } else if (shape === "x") {
      const w = r * 0.35;
      ctx.moveTo(x - r, y - r + w); ctx.lineTo(x - r + w, y - r); ctx.lineTo(x, y - w);
      ctx.lineTo(x + r - w, y - r); ctx.lineTo(x + r, y - r + w); ctx.lineTo(x + w, y);
      ctx.lineTo(x + r, y + r - w); ctx.lineTo(x + r - w, y + r); ctx.lineTo(x, y + w);
      ctx.lineTo(x - r + w, y + r); ctx.lineTo(x - r, y + r - w); ctx.lineTo(x - w, y);
      ctx.closePath();
    }
  }

  function textPlacement(anchor) {
    const [v, h] = (anchor || "middle center").split(" ");
    return {
      baseline: v === "top" ? "bottom" : v === "bottom" ? "top" : "middle",
      dy: v === "top" ? -2 : v === "bottom" ? 2 : 0,
      align: h === "left" ? "right" : h === "right" ? "left" : "center",
      dx: h === "left" ? -2 : h === "right" ? 2 : 0,
    };
  }

  class DrawingsPrimitive {
    constructor() {
      const self = this;
      this._bg = { zOrder: () => "bottom", renderer: () => ({ draw: (t) => self._drawSessions(t) }) };
      this._fg = { zOrder: () => "normal", renderer: () => ({ draw: (t) => self._drawItems(t) }) };
    }
    attached(param) { this.requestUpdate = param.requestUpdate; }
    detached() { this.requestUpdate = null; }
    updateAllViews() {}
    paneViews() { return [this._bg, this._fg]; }

    _drawSessions(target) {
      if (!S.showSessions || !S.sessions.length) return;
      const ts = S.chart.timeScale();
      target.useMediaCoordinateSpace(({ context: ctx, mediaSize }) => {
        ctx.save();
        ctx.lineWidth = S.cfg.session_line_width;
        ctx.setLineDash(DASHES[S.cfg.session_line_dash] || []);
        ctx.font = "10px -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif";
        ctx.textBaseline = "bottom";
        ctx.textAlign = "left";
        for (const [x, color, label] of S.sessions) {
          if (x > S.cursor) continue;
          const X = ts.logicalToCoordinate(x);
          if (X == null || X < -1 || X > mediaSize.width + 1) continue;
          const px = Math.round(X) + 0.5;
          ctx.strokeStyle = color;
          ctx.beginPath(); ctx.moveTo(px, 0); ctx.lineTo(px, mediaSize.height); ctx.stroke();
          ctx.fillStyle = color;
          ctx.fillText(label, px + 3, mediaSize.height - 3);
        }
        ctx.restore();
      });
    }

    _drawItems(target) {
      const list = drawList();
      if (!list.length) return;
      const ts = S.chart.timeScale();
      const series = S.series;
      const range = ts.getVisibleLogicalRange();
      if (!range) return;
      const lo = range.from - 2, hi = range.to + 2;
      const width = ts.width ? ts.width() : 0;
      const detail = !width || width / Math.max(range.to - range.from, 1) >= DETAIL_PX;
      target.useMediaCoordinateSpace(({ context: ctx }) => {
        ctx.save();
        for (const d of list) {
          const xa = d.x0 != null ? d.x0 : d.x;
          const xb = d.x0 != null ? x1Of(d) : d.x;
          if (xb < lo || xa > hi) continue;
          if (d.k === "b") {
            const X0 = ts.logicalToCoordinate(xa), X1 = ts.logicalToCoordinate(xb);
            const Y0 = series.priceToCoordinate(d.y1), Y1 = series.priceToCoordinate(d.y0);
            if (X0 == null || X1 == null || Y0 == null || Y1 == null) continue;
            if (d.f) { ctx.fillStyle = d.f; ctx.fillRect(X0, Y0, X1 - X0, Y1 - Y0); }
            if (d.e) {
              ctx.strokeStyle = d.e; ctx.lineWidth = d.ew || 1;
              ctx.setLineDash(DASHES[d.ed || "solid"]);
              ctx.strokeRect(Math.round(X0) + 0.5, Math.round(Y0) + 0.5,
                             Math.round(X1 - X0), Math.round(Y1 - Y0));
            }
          } else if (d.k === "l") {
            const X0 = ts.logicalToCoordinate(xa), X1 = ts.logicalToCoordinate(xb);
            const Y0 = series.priceToCoordinate(d.y0), Y1 = series.priceToCoordinate(d.y1);
            if (X0 == null || X1 == null || Y0 == null || Y1 == null) continue;
            ctx.strokeStyle = d.c; ctx.lineWidth = d.w || 1;
            ctx.setLineDash(DASHES[d.d || "solid"]);
            const off = (d.w || 1) % 2 ? 0.5 : 0;
            ctx.beginPath();
            ctx.moveTo(X0, Math.round(Y0) + off); ctx.lineTo(X1, Math.round(Y1) + off);
            ctx.stroke();
          } else if (!detail && d.o !== "order") { // the opened order keeps its labels
            continue;
          } else if (d.k === "m") {
            const X = ts.logicalToCoordinate(d.x), Y = series.priceToCoordinate(d.y);
            if (X == null || Y == null) continue;
            ctx.setLineDash([]);
            shapePath(ctx, d.s, X, Y, d.z);
            ctx.fillStyle = d.c; ctx.fill();
            if (d.ow) { ctx.strokeStyle = d.c; ctx.lineWidth = d.ow; ctx.stroke(); }
          } else if (d.k === "t") {
            const X = ts.logicalToCoordinate(d.x), Y = series.priceToCoordinate(d.y);
            if (X == null || Y == null) continue;
            const p = textPlacement(d.a);
            ctx.font = d.z + "px -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif";
            ctx.fillStyle = d.c; ctx.textAlign = p.align; ctx.textBaseline = p.baseline;
            ctx.fillText(d.s, X + p.dx, Y + p.dy);
          }
        }
        ctx.restore();
      });
    }
  }

  // --- hover ----------------------------------------------------------------------------

  function hitTest(px, py) {
    const ts = S.chart.timeScale();
    let best = null, bestDist = HOVER_PX;
    for (const type of S.order) {
      const m = S.types[type];
      if (!m) continue;
      for (const { d } of m.values()) {
        if (!isShown(type, d)) continue;
        if (d.k === "h") {
          const X0 = ts.logicalToCoordinate(d.x0 - 0.5), X1 = ts.logicalToCoordinate(x1Of(d) + 0.5);
          const Y = S.series.priceToCoordinate(d.y);
          if (X0 == null || X1 == null || Y == null || px < X0 || px > X1) continue;
          const dist = Math.abs(py - Y);
          if (dist < bestDist) { best = d; bestDist = dist; }
        } else if (d.k === "m" && d.h) {
          const X = ts.logicalToCoordinate(d.x), Y = S.series.priceToCoordinate(d.y);
          if (X == null || Y == null) continue;
          const dist = Math.hypot(px - X, py - Y);
          if (dist < bestDist) { best = d; bestDist = dist; }
        }
      }
    }
    return best;
  }

  function onCrosshair(param) {
    const tip = S.tip;
    const bar = param.point && param.seriesData ? param.seriesData.get(S.series) : null;
    showLegend(bar, param.logical);
    if (!param.point) { tip.style.display = "none"; return; }
    const hit = hitTest(param.point.x, param.point.y);
    if (!hit) { tip.style.display = "none"; return; }
    tip.textContent = hit.k === "h" ? hit.s : hit.h;
    tip.style.display = "block";
    const W = S.el.clientWidth, H = S.el.clientHeight;
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let left = param.point.x + 14, top = param.point.y + 14;
    if (left + w > W - 60) left = param.point.x - w - 14;
    if (top + h > H - 30) top = Math.max(0, param.point.y - h - 14);
    tip.style.left = Math.max(0, left) + "px";
    tip.style.top = top + "px";
  }

  function showLegend(bar, logical) {
    const head = `${S.symbol} · ${S.tf} · bid · UTC`;
    if (!bar) {
      const i = S.cursor;
      if (i < 0) { S.legend.textContent = head; return; }
      bar = S.series.dataByIndex(i);
      logical = i;
    }
    if (!bar) { S.legend.textContent = head; return; }
    const t = new Date(bar.time * 1000).toISOString().slice(0, 16).replace("T", " ");
    const i = Math.round(logical);
    const spread = S.spreads[i];
    S.legend.textContent =
      `${head}   ${t}   O ${fmt(bar.open)}  H ${fmt(bar.high)}  L ${fmt(bar.low)}  C ${fmt(bar.close)}` +
      (spread == null ? "" : `  spread ${fmt(spread)}`);
  }

  function showBadges() {
    const el = S.badgesEl;
    if (!el) return; // no chart yet (a selection can arrive before the first candles)
    el.textContent = "";
    if (!S.overlaysOn) return;
    for (const type of S.order) {
      if (!S.selected.has(type)) continue;
      for (const b of (S.badges[type] || []).slice().sort((a, c) => a.r - c.r)) {
        const div = document.createElement("div");
        div.className = "chart-badge";
        div.textContent = b.t;
        div.style.background = b.bg;
        div.style.color = b.c;
        div.style.fontSize = b.z + "px";
        el.appendChild(div);
      }
    }
  }

  // --- chart setup ----------------------------------------------------------------------

  function ensureChart(cfg) {
    const el = document.getElementById("chart-lwc");
    if (!el) return false;
    if (S.chart && S.el === el) return true;
    if (S.chart) { // the page was rebuilt (back from the results page): start over
      S.chart.remove();
      S.chart = null;
      S.key = null;
      clearDrawings();
    }
    const L = window.LightweightCharts;
    S.el = el;
    el.textContent = "";
    S.chart = L.createChart(el, {
      autoSize: true,
      layout: {
        background: { type: "solid", color: cfg.background },
        textColor: cfg.text_color,
        fontSize: 12,
        attributionLogo: true, // TradingView's attribution, as the license asks
      },
      grid: {
        vertLines: { visible: cfg.show_grid, color: cfg.grid_color },
        horzLines: { visible: cfg.show_grid, color: cfg.grid_color },
      },
      crosshair: {
        mode: L.CrosshairMode.Normal,
        vertLine: { color: cfg.spike_color, labelBackgroundColor: cfg.text_color },
        horzLine: { color: cfg.spike_color, labelBackgroundColor: cfg.text_color },
      },
      rightPriceScale: { borderColor: cfg.axis_border, scaleMargins: { top: cfg.y_padding, bottom: cfg.y_padding } },
      timeScale: { borderColor: cfg.axis_border, timeVisible: true, secondsVisible: false, rightOffset: 10 },
      localization: { dateFormat: "yyyy-MM-dd" },
    });
    S.series = S.chart.addSeries(L.CandlestickSeries, {
      upColor: cfg.up_body, downColor: cfg.down_body,
      borderVisible: true, borderUpColor: cfg.edge_color, borderDownColor: cfg.edge_color,
      wickUpColor: cfg.wick_color, wickDownColor: cfg.wick_color,
      priceLineVisible: false, lastValueVisible: true,
    });
    S.prim = new DrawingsPrimitive();
    S.series.attachPrimitive(S.prim);
    for (const [name, cls] of [["legend", "chart-legend"], ["badgesEl", "chart-badges"], ["tip", "chart-tip"]]) {
      const div = document.createElement("div");
      div.className = cls;
      el.appendChild(div);
      S[name] = div;
    }
    S.chart.subscribeCrosshairMove(onCrosshair);
    S.chart.subscribeClick((param) => {
      if (!param.point) return;
      const logical = S.chart.timeScale().coordinateToLogical(param.point.x);
      if (logical == null) return;
      const x = Math.round(logical); // the candle under the pointer
      if (x < 0 || x >= S.times.length) return;
      if (!S.replay) {
        const price = S.series.coordinateToPrice(param.point.y);
        const candidates = [
          ...(S.overlaysOn && S.selected.has("trades") ? S.inspections : []),
          ...(S.orderDraw && S.orderDraw.key === S.key ? S.orderDraw.inspections || [] : []),
        ];
        const hit = candidates.slice().reverse().find((item) => {
          const o = item.order;
          const prices = [o.entry, o.sl, o.tp].filter((v) => v != null);
          const inBox = x >= item.x0 && x <= item.x1 && price >= Math.min(...prices) && price <= Math.max(...prices);
          const markerX = S.chart.timeScale().logicalToCoordinate(item.x1);
          const markerY = o.exit == null ? null : S.series.priceToCoordinate(o.exit);
          const onMarker = markerX != null && markerY != null &&
            Math.hypot(param.point.x - markerX, param.point.y - markerY) <= HOVER_PX;
          return inBox || onMarker;
        });
        if (hit) setProps("chart-inspect", {data: {order: hit.order, n: ++S.nonce}});
      }
      setProps("chart-click", { data: { x, n: ++S.nonce } });
    });
    S.chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      clearTimeout(S.rangeTimer);
      S.rangeTimer = setTimeout(reportRange, 250);
      if (!S.replay && range) { // the server needs it to load the days of a timeframe switch
        clearTimeout(S.viewTimer);
        S.viewTimer = setTimeout(() => setProps("chart-viewport", { data: viewNow() }), 250);
        clearTimeout(S.extendTimer);
        S.extendTimer = setTimeout(maybeExtend, EXTEND_DEBOUNCE_MS);
      }
      if (!S.replay || S.picking || !range) return;
      clearTimeout(S.spanTimer);
      S.spanTimer = setTimeout(() => {
        S.span = { left: (S.cursor + 0.5 - range.from) * S.tfmin, right: (range.to - S.cursor - 0.5) * S.tfmin };
        setProps("chart-replay-span", { data: S.span });
      }, 250);
    });
    return true;
  }

  function priceFormat(digits) {
    return { type: "price", precision: digits, minMove: Math.pow(10, -digits) };
  }

  function barsOf(c) {
    const out = new Array(c.t.length);
    for (let i = 0; i < c.t.length; i++) {
      out[i] = { time: c.t[i], open: c.o[i], high: c.h[i], low: c.l[i], close: c.c[i] };
    }
    return out;
  }

  function spanRange() {
    if (!S.span) return null;
    // same rule as span_candles() in pages/chart.py
    const left = Math.min(Math.max(S.span.left / S.tfmin, S.cfg.replay_min_visible), S.cfg.replay_window);
    const right = Math.max(S.span.right / S.tfmin, 1);
    return { from: S.cursor - left + 0.5, to: S.cursor + right + 0.5 };
  }

  /* The visible view as a time (centre of the visible area, UTC seconds) and a number of
     candles, so it can be kept across a timeframe switch (ROADMAP 4.0b part 1). A candle
     at logical x covers x - 0.5 .. x + 0.5. */
  function viewNow() {
    const range = S.chart && S.chart.timeScale().getVisibleLogicalRange();
    const n = S.times.length;
    if (!range || !n) return null;
    const c = (range.from + range.to) / 2;
    const i = Math.min(Math.max(Math.round(c), 0), n - 1);
    const off = Math.min(Math.max(c - i + 0.5, 0), 1);
    return {
      key: S.key, symbol: S.symbol, tf: S.tf,
      center: S.times[i] + off * S.tfmin * 60,
      count: range.to - range.from,
    };
  }

  /* The visible candles as a UTC time range [from, to) for the side panel's "Trades in view"
     (store chart-range): the first visible candle's open .. the last visible candle's close. */
  function reportRange() {
    const range = S.chart && S.chart.timeScale().getVisibleLogicalRange();
    const n = S.times.length;
    if (!range || !n) return;
    const i0 = Math.min(Math.max(Math.round(range.from), 0), n - 1);
    const i1 = Math.min(Math.max(Math.round(range.to), 0), n - 1);
    setProps("chart-range", { data: { symbol: S.symbol, from: S.times[i0], to: S.times[i1] + S.tfmin * 60 } });
  }

  /* Load more days while scrolling (user, 2026-10-19): when fewer than a margin of candles are
     left beyond the view's left / right edge, ask the server for the next chunk of days (store
     chart-more). The margin is the visible width (cfg.extend_margin_screens), at least
     extend_margin_min candles and at most half a chunk (so a very wide view doesn't keep
     loading). One request per range and side: if the server has no more days nothing changes
     and the same edge is not asked again; a new range (key) asks again. */
  function maybeExtend() {
    if (S.replay || S.picking || !S.chart || !S.key || !S.times.length) return;
    const range = S.chart.timeScale().getVisibleLogicalRange();
    if (!range) return;
    const cfg = S.cfg;
    const margin = Math.min(
      Math.max((range.to - range.from) * cfg.extend_margin_screens, cfg.extend_margin_min),
      cfg.extend_candles / 2
    );
    const n = S.times.length;
    const side = range.from < margin ? "left" : range.to > n - 1 - margin ? "right" : null;
    if (!side) return;
    const ask = S.key + "|" + side;
    if (S.asked.has(ask)) return;
    S.asked.add(ask);
    setProps("chart-more", { data: { key: S.key, side, view: viewNow(), n: ++S.nonce } });
  }

  /* Centre the chart on time `v.center` with `v.count` candles visible; prices auto-fit. */
  function showView(v) {
    const t = S.times;
    S.series.priceScale().applyOptions({ autoScale: true });
    if (v.count >= t.length) { // fewer candles than were visible (e.g. D): show them all
      S.chart.timeScale().fitContent();
      return;
    }
    let lo = 0, hi = t.length - 1;
    if (v.center < t[0]) hi = 0;
    while (lo < hi) { // last candle opening at or before the centre time
      const mid = (lo + hi + 1) >> 1;
      if (t[mid] <= v.center) lo = mid; else hi = mid - 1;
    }
    const off = Math.min(Math.max((v.center - t[lo]) / (S.tfmin * 60), 0), 1);
    const c = lo - 0.5 + off;
    S.series.priceScale().applyOptions({ autoScale: true });
    S.chart.timeScale().setVisibleLogicalRange({ from: c - v.count / 2, to: c + v.count / 2 });
  }

  function view() {
    setProps("chart-view", { data: { key: S.key, cursor: S.cursor, types: [...S.loaded] } });
  }

  function need(types) {
    const missing = types.filter((t) => !S.loaded.has(t));
    if (!missing.length || S.key == null) return null;
    return { key: S.key, cursor: S.cursor, types: missing, filters: S.filters, n: ++S.nonce };
  }

  function wanted() {
    return S.overlaysOn ? [...S.selected] : [];
  }

  function clearDrawings() {
    S.types = {}; S.index = new Map(); S.loaded = new Set(); S.badges = {}; S.messages = [];
    S.sorted = null;
  }

  function addDrawing(d) {
    const type = d.o;
    const m = S.types[type] || (S.types[type] = new Map());
    const e = m.get(d.id);
    if (e) e.n += 1; else m.set(d.id, { d, n: 1 });
    S.index.set(d.id, type);
  }

  function removeDrawing(id) {
    const type = S.index.get(id);
    const m = type && S.types[type];
    const e = m && m.get(id);
    if (!e) return;
    if (--e.n <= 0) { m.delete(id); S.index.delete(id); }
  }

  function showMessages() {
    setProps("chart-notes", { children: S.messages.join(" · ") });
  }

  // --- box zoom (ROADMAP 4.0b part 5) ----------------------------------------------------
  /* The zoom button turns the tool on: a transparent layer over the chart pane (not the
     axes) takes the mouse, so the chart can't pan and no candle click reaches the replay;
     drag a rectangle, release: the chart shows exactly that time and price range (price
     axis no longer auto) and the tool turns off. Each zoom remembers the view before it:
     "reset zoom" or a double-click on the chart goes back one step (with none left: the
     whole range, prices auto). A double-click on the price axis = auto-scale (library). */

  const ZOOM_MIN_PX = 6; // smaller drags are ignored (the tool stays on)
  const Z = { on: false, start: null, layer: null, rect: null, history: [] };

  function zoomTool(on) {
    Z.on = !!(on && S.chart && S.times.length);
    const button = document.getElementById("tb-zoom");
    if (button) button.classList.toggle("active", Z.on);
    if (!Z.on) {
      if (Z.layer) Z.layer.style.display = "none";
      Z.start = null;
      return;
    }
    ensureZoomLayer();
    const size = S.chart.paneSize(0);
    Object.assign(Z.layer.style, {
      display: "block", width: S.chart.timeScale().width() + "px", height: size.height + "px",
    });
    Z.rect.style.display = "none";
  }

  function viewState() {
    const ps = S.series.priceScale();
    return {
      range: S.chart.timeScale().getVisibleLogicalRange(),
      auto: ps.options().autoScale,
      price: ps.getVisibleRange(),
    };
  }

  function zoomBack() {
    const v = Z.history.pop();
    const ps = S.series.priceScale();
    if (!v) { ps.setAutoScale(true); S.chart.timeScale().fitContent(); return; }
    if (v.range) S.chart.timeScale().setVisibleLogicalRange(v.range);
    if (v.auto || !v.price) ps.setAutoScale(true); else ps.setVisibleRange(v.price);
  }

  function zoomTo(a, b) {
    const x0 = Math.min(a.x, b.x), x1 = Math.max(a.x, b.x);
    const y0 = Math.min(a.y, b.y), y1 = Math.max(a.y, b.y);
    if (x1 - x0 < ZOOM_MIN_PX || y1 - y0 < ZOOM_MIN_PX) return false;
    const ts = S.chart.timeScale();
    const from = ts.coordinateToLogical(x0), to = ts.coordinateToLogical(x1);
    const top = S.series.coordinateToPrice(y0), bottom = S.series.coordinateToPrice(y1);
    if (from == null || to == null || top == null || bottom == null) return false;
    Z.history.push(viewState());
    ts.setVisibleLogicalRange({ from, to });
    S.series.priceScale().setVisibleRange({ from: bottom, to: top });
    return true;
  }

  function ensureZoomLayer() {
    if (Z.layer && Z.layer.parentElement === S.el) return;
    const layer = document.createElement("div");
    layer.className = "chart-zoom-layer";
    const rect = document.createElement("div");
    rect.className = "chart-zoom-rect";
    layer.appendChild(rect);
    S.el.appendChild(layer);
    const point = (e) => {
      const b = layer.getBoundingClientRect();
      return { x: e.clientX - b.left, y: e.clientY - b.top };
    };
    layer.addEventListener("mousedown", (e) => {
      e.preventDefault();
      Z.start = point(e);
      Object.assign(rect.style, { display: "block", left: Z.start.x + "px", top: Z.start.y + "px", width: "0px", height: "0px" });
    });
    layer.addEventListener("mousemove", (e) => {
      if (!Z.start) return;
      const p = point(e);
      Object.assign(rect.style, {
        left: Math.min(p.x, Z.start.x) + "px", top: Math.min(p.y, Z.start.y) + "px",
        width: Math.abs(p.x - Z.start.x) + "px", height: Math.abs(p.y - Z.start.y) + "px",
      });
    });
    const end = (e) => {
      if (!Z.start) return;
      const done = zoomTo(Z.start, point(e));
      Z.start = null;
      rect.style.display = "none";
      if (done) zoomTool(false);
    };
    layer.addEventListener("mouseup", end);
    layer.addEventListener("mouseleave", end);
    Z.layer = layer;
    Z.rect = rect;
  }

  document.addEventListener("click", (e) => {
    if (e.target.closest("#tb-zoom")) zoomTool(!Z.on);
    else if (e.target.closest("#tb-zoom-reset") && S.chart) { zoomTool(false); zoomBack(); }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && Z.on) zoomTool(false); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setProps("chart-inspect", {data: {order: null, n: ++S.nonce}});
  });
  document.addEventListener("click", (e) => {
    if (S.el && !S.el.contains(e.target) && !e.target.closest("#inspection-panel"))
      setProps("chart-inspect", {data: {order: null, n: ++S.nonce}});
  });
  document.addEventListener("dblclick", (e) => {
    if (!S.chart || Z.on || !Z.history.length || !e.target.closest("#chart-lwc")) return;
    const b = S.el.getBoundingClientRect();
    const inPane = e.clientX - b.left < S.chart.timeScale().width()
      && e.clientY - b.top < S.chart.paneSize(0).height;
    if (inPane) zoomBack(); // on the price axis the library's double-click auto-scales
  });

  // --- screenshot (ROADMAP 4.0b part 3) ---------------------------------------------------

  function fmtTime(sec, dateOnly) {
    const s = new Date(sec * 1000).toISOString();
    return dateOnly ? s.slice(0, 10) : s.slice(0, 16).replace("T", " ");
  }

  /* What the stamp and the file name say: symbol, timeframe, first and last visible
     candle (UTC), the replay time if replay is on, the overlays that are on, the preset. */
  function shotInfo(overlays, preset) {
    const r = S.chart.timeScale().getVisibleLogicalRange();
    const n = S.times.length;
    const i0 = Math.min(Math.max(Math.round(r.from), 0), n - 1);
    const i1 = Math.min(Math.max(Math.round(r.to), 0), n - 1);
    const daily = S.tfmin >= 1440;
    const info = {
      symbol: S.symbol, tf: S.tf, daily,
      from: fmtTime(S.times[i0], daily), to: fmtTime(S.times[i1], daily),
      replay: null, overlays, preset,
    };
    if (S.replay && !S.picking && S.cursor >= 0) {
      info.replay = fmtTime(S.times[S.cursor] + S.tfmin * 60, false); // the replay time
    }
    return info;
  }

  function stampText(info) {
    const parts = [info.symbol, info.tf, `${info.from} → ${info.to} UTC`];
    if (info.replay) {
      const sameDay = info.replay.slice(0, 10) === info.to.slice(0, 10);
      parts.push(`replay at ${sameDay ? info.replay.slice(11) : info.replay}`);
    }
    parts.push(`overlays: ${info.overlays.length ? info.overlays.join(", ") : "none"}`);
    parts.push(`preset: ${info.preset}`);
    return parts.join(" · ");
  }

  function shotFileName(info) {
    const stamp = (t) => t.replace(" ", "T").replace(":", "");
    let name = `${info.symbol}_${info.tf}_${stamp(info.from)}_${stamp(info.to)}_UTC`;
    if (info.replay) name += `_replay-${info.replay.slice(11).replace(":", "")}`;
    return name.replace(/[^A-Za-z0-9_.-]/g, "-") + ".png";
  }

  /* The chart as shown: the library's screenshot (candles, axes, our drawings live in its
     canvas) plus the HTML layers on top of it (legend, trend badges) and the stamp. */
  function shotCanvas(info) {
    const shot = S.chart.takeScreenshot();
    const ctx = shot.getContext("2d");
    const box = S.el.getBoundingClientRect();
    const scale = shot.width / box.width;
    ctx.save();
    ctx.scale(scale, scale);
    const at = (el) => {
      const b = el.getBoundingClientRect();
      return { x: b.left - box.left, y: b.top - box.top, w: b.width, h: b.height };
    };
    const legend = at(S.legend);
    ctx.font = getComputedStyle(S.legend).font;
    ctx.fillStyle = getComputedStyle(S.legend).color;
    ctx.textBaseline = "top";
    ctx.fillText(S.legend.textContent, legend.x, legend.y + 1);
    for (const badge of S.badgesEl.children) {
      const b = at(badge);
      const style = getComputedStyle(badge);
      ctx.fillStyle = style.backgroundColor;
      ctx.fillRect(b.x, b.y, b.w, b.h);
      ctx.fillStyle = style.color;
      ctx.font = style.font;
      ctx.textBaseline = "middle";
      ctx.fillText(badge.textContent, b.x + parseFloat(style.paddingLeft), b.y + b.h / 2);
    }
    // the stamp, bottom left above the time axis
    const text = stampText(info);
    ctx.font = "12px -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, sans-serif";
    const w = ctx.measureText(text).width + 16;
    const h = 22;
    const axis = S.chart.timeScale().height();
    const x = 8, y = box.height - axis - h - 8;
    const token = (name) => getComputedStyle(document.documentElement).getPropertyValue("--" + name).trim();
    ctx.fillStyle = token("panel");
    ctx.strokeStyle = token("line");
    ctx.lineWidth = 1;
    ctx.fillRect(x, y, w, h);
    ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
    ctx.fillStyle = token("text");
    ctx.textBaseline = "middle";
    ctx.fillText(text, x + 8, y + h / 2 + 0.5);
    ctx.restore();
    return shot;
  }

  // --- Dash clientside callbacks ---------------------------------------------------------

  const no = () => window.dash_clientside.no_update;

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    chart: {
      _state: S, // for tests and debugging
      /* Base payload (candles up to the cursor + session lines) -> chart; returns the
         overlay request for the selected types. */
      base(payload, cfg) {
        if (!payload) {
          if (S.chart) { S.series.setData([]); clearDrawings(); S.key = null; S.sessions = []; invalidate(); }
          barDone();
          return null;
        }
        if (!ensureChart(cfg)) return no();
        zoomTool(false); // new candles: box zooms of the old ones are forgotten
        Z.history = [];
        S.series.priceScale().setAutoScale(true);
        // a timeframe switch outside replay keeps the centre time and the candle count
        const before = S.key && !S.replay && !payload.replay ? viewNow() : null;
        // (also for more days of the same timeframe: the days were extended while scrolling)
        const keep = before && before.symbol === payload.symbol;
        S.cfg = cfg;
        if (S.key !== payload.key) S.asked = new Set();
        S.key = payload.key;
        S.symbol = payload.symbol; S.tf = payload.tf; S.tfmin = payload.tfmin;
        S.digits = payload.digits; S.replay = payload.replay; S.picking = payload.picking;
        S.cursor = payload.cursor;
        S.inspections = [];
        S.times = payload.candles.t.slice();
        S.spreads = payload.candles.s.slice();
        S.sessions = payload.sessions;
        S.series.applyOptions({ priceFormat: priceFormat(S.digits) });
        S.series.setData(barsOf(payload.candles));
        clearDrawings();
        S.filters = null;
        if (payload.span) S.span = payload.span;
        if (payload.range) S.chart.timeScale().setVisibleLogicalRange(payload.range);
        else if (keep) showView(before);
        else S.chart.timeScale().fitContent();
        showLegend(null);
        showBadges();
        showMessages();
        invalidate();
        view();
        reportRange();
        S.drawn.base = performance.now();
        barReceived(); // the selection callback finishes the bar if no overlays are needed
        return null; // the selection callback sends the overlay request
      },

      /* Selection (overlay switch, types, filters, sessions) or a new base: show / hide
         what is loaded and request what is missing. */
      select(overlays, types, filters, sessions, base, settings, sweep) {
        S.overlaysOn = !!(overlays && overlays.length);
        const sel = types || [];
        S.selected = new Set(sel.filter((v) => !v.includes(".")));
        S.parts = new Set(sel.filter((v) => v.includes(".")));
        S.showSessions = !!(sessions && sessions.length);
        // drawings depend on the detector switches and the strategy settings (Trades)
        const f = JSON.stringify([filters || [], (settings && settings.key) || "", sweep || null]);
        if (f !== S.filters) { clearDrawings(); S.filters = f; view(); }
        showBadges();
        invalidate();
        const req = need(wanted());
        if (req) { if (P.stage === null) barReceived(); } // overlays on their way
        else if (P.stage === "overlays") barDone();
        return req || no();
      },

      /* The chart inputs changed (symbol, timeframe, days, ...): a new base is requested. */
      loading() {
        if (P.stage !== "loading") barLoading();
        return no();
      },

      /* Overlay payload (full drawings of some types at a cursor). */
      overlays(payload) {
        if (!payload || payload.key !== S.key || payload.filters !== S.filters) return no();
        if (payload.cursor !== S.cursor) return need(payload.requested || []) || no();
        for (const type of Object.keys(payload.types)) {
          if (S.types[type]) for (const id of S.types[type].keys()) S.index.delete(id);
          S.types[type] = new Map();
          for (const d of payload.types[type]) addDrawing(d);
          S.badges[type] = payload.badges[type] || [];
          S.loaded.add(type);
        }
        S.order = payload.order;
        if (payload.inspections) S.inspections = payload.inspections;
        S.messages = payload.messages;
        showMessages();
        showBadges();
        invalidate();
        view();
        S.drawn.overlays = performance.now();
        const req = need(wanted()); // a type ticked while this one was on its way
        if (!req) barDone();
        return req || no();
      },

      /* The order of a trade focus (store chart-order-draw, drawings on this chart's candles). */
      order(payload) {
        S.orderDraw = payload || null;
        invalidate();
        return no();
      },

      /* Trade focus (results page, side panel, Live page): once the focused symbol's (and
         timeframe's) candles are drawn, scroll to the trade and mark the focus done. An order
         focus (ROADMAP 7.6) is marked done also when its candles are not there (the day is not
         cached: the chip says so); an old-form focus waits for its range. The entry / exit
         are CLOSE times: the candle containing the instant just before them. */
      focus(_done, focus) {
        if (!focus || focus.done || !S.chart || S.symbol !== focus.symbol || !S.times.length) {
          return no();
        }
        if (focus.tf && S.tf !== focus.tf) return no(); // the timeframe is on its way
        const t0 = Date.parse(focus.t0) / 1000;
        const t1 = Date.parse(focus.t1) / 1000;
        const last = S.times.length - 1;
        const isOrder = !!focus.order;
        const end = S.times[last] + S.tfmin * 60;
        if (isOrder ? (t0 <= S.times[0] || t0 > end) : (t0 < S.times[0] || t0 > S.times[last])) {
          return isOrder ? Object.assign({}, focus, { done: true }) : no(); // not this range (yet)
        }
        let i0 = 0;
        if (isOrder) {
          while (i0 < last && S.times[i0 + 1] < t0) i0++; // the candle that closed at the entry
        } else {
          while (i0 < last && S.times[i0 + 1] <= t0) i0++; // the candle containing the entry
        }
        let i1 = i0;
        while (i1 < last && S.times[i1 + 1] < t1) i1++; // ... and the exit
        S.series.priceScale().applyOptions({ autoScale: true });
        S.chart.timeScale().setVisibleLogicalRange({
          from: i0 - FOCUS_BEFORE,
          to: i1 + FOCUS_AFTER,
        });
        return Object.assign({}, focus, { done: true });
      },

      /* Screenshot (camera button, or its menu): save the PNG or copy it. */
      shot(_save, _menuSave, _copy, overlaysOn, types, options, store, modified) {
        const trig = (window.dash_clientside.callback_context.triggered || [])[0];
        if (!trig || !trig.value || !S.chart || !S.times.length) return no();
        const sel = overlaysOn && overlaysOn.length ? types || [] : [];
        const labels = (options || [])
          .filter((o) => sel.includes(o.value) && !String(o.value).includes("."))
          .map((o) => String(o.label).trim());
        const preset = ((store && store.preset) || "Default") + (modified ? " (modified)" : "");
        const info = shotInfo(labels, preset);
        const canvas = shotCanvas(info);
        const name = shotFileName(info);
        if (trig.prop_id.startsWith("shot-copy")) {
          if (!navigator.clipboard || !window.ClipboardItem) {
            return "This browser doesn't allow copying images: use Download.";
          }
          return new Promise((resolve) => canvas.toBlob((blob) => {
            navigator.clipboard.write([new ClipboardItem({ "image/png": blob })])
              .then(() => resolve(`Copied ${name}`))
              .catch((e) => resolve(`Copy failed (${e.message}): use Download.`));
          }, "image/png"));
        }
        const a = document.createElement("a");
        a.download = name;
        a.href = canvas.toDataURL("image/png");
        a.click();
        return `Saved ${name}`;
      },

      _shotText: stampText, // for tests and debugging
      _zoom: Z,
      _shotName: shotFileName,

      /* Go to a time (store chart-goto {t, symbol}): once its candle is loaded, centre on
         it (keeping the zoom, or GOTO_VISIBLE candles when zoomed out further than
         GOTO_MAX_VISIBLE) and put the crosshair on it, so the legend shows that candle. */
      goto(target) {
        if (!target || target.done || !S.chart || target.symbol !== S.symbol) return no();
        const t = S.times;
        const n = t.length;
        if (!n || target.t < t[0] || target.t >= t[n - 1] + S.tfmin * 60) return no();
        let j = 0;
        while (j < n - 1 && t[j + 1] <= target.t) j++;
        const r = S.chart.timeScale().getVisibleLogicalRange();
        const shown = r ? r.to - r.from : n;
        const count = shown <= GOTO_MAX_VISIBLE ? shown : Math.min(GOTO_VISIBLE, n);
        S.series.priceScale().applyOptions({ autoScale: true });
        S.chart.timeScale().setVisibleLogicalRange({ from: j - count / 2, to: j + count / 2 });
        const bar = S.series.dataByIndex(j);
        if (bar) setTimeout(() => S.chart.setCrosshairPosition(bar.close, bar.time, S.series), 50);
        return Object.assign({}, target, { done: true });
      },

      /* Replay delta: from our cursor to the next one. */
      delta(delta) {
        if (!delta || delta.key !== S.key) return no();
        if (delta.from !== S.cursor) return { n: ++S.nonce }; // out of step: reload
        if (delta.candles) {
          const bars = barsOf(delta.candles);
          for (const b of bars) S.series.update(b);
          S.times.push(...delta.candles.t);
          S.spreads.push(...delta.candles.s);
          S.sessions = S.sessions.concat(delta.sessions || []);
        }
        if (delta.drop) {
          S.series.pop(delta.drop);
          S.times.length -= delta.drop;
          S.spreads.length -= delta.drop;
          S.sessions = S.sessions.filter((s) => s[0] <= delta.to);
        }
        for (const id of delta.remove) removeDrawing(id);
        for (const d of delta.add) addDrawing(d);
        for (const type of Object.keys(delta.badges)) S.badges[type] = delta.badges[type];
        // types loaded while the delta was on its way are at the old cursor: reload them
        for (const type of [...S.loaded]) {
          if (!delta.types.includes(type)) { S.loaded.delete(type); delete S.types[type]; }
        }
        S.cursor = delta.to;
        S.sorted = null;
        const r = spanRange();
        if (r) S.chart.timeScale().setVisibleLogicalRange(r);
        showLegend(null);
        showBadges();
        invalidate();
        view();
        S.drawn.delta = performance.now();
        const req = need(wanted());
        if (req) setProps("chart-need", { data: req });
        return no();
      },
    },
  });
})();
