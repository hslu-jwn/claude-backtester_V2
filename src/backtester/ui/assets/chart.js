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
  const DETAIL_PX = 3; // narrower candles: no markers / labels (unreadable, slow to draw)
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
    spanTimer: null, nonce: 0,
    drawn: {},          // performance.now() when each payload kind was last applied
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
    S.sorted = out;
    return out;
  }

  function invalidate() {
    S.sorted = null;
    if (S.prim && S.prim.requestUpdate) S.prim.requestUpdate();
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
          } else if (!detail) {
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
      setProps("chart-click", { data: { x, n: ++S.nonce } });
    });
    S.chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
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
          return null;
        }
        if (!ensureChart(cfg)) return no();
        S.cfg = cfg;
        S.key = payload.key;
        S.symbol = payload.symbol; S.tf = payload.tf; S.tfmin = payload.tfmin;
        S.digits = payload.digits; S.replay = payload.replay; S.picking = payload.picking;
        S.cursor = payload.cursor;
        S.times = payload.candles.t.slice();
        S.spreads = payload.candles.s.slice();
        S.sessions = payload.sessions;
        S.series.applyOptions({ priceFormat: priceFormat(S.digits) });
        S.series.setData(barsOf(payload.candles));
        clearDrawings();
        S.filters = null;
        if (payload.span) S.span = payload.span;
        if (payload.range) S.chart.timeScale().setVisibleLogicalRange(payload.range);
        else S.chart.timeScale().fitContent();
        showLegend(null);
        showBadges();
        showMessages();
        invalidate();
        view();
        S.drawn.base = performance.now();
        return null; // the selection callback sends the overlay request
      },

      /* Selection (overlay switch, types, filters, sessions) or a new base: show / hide
         what is loaded and request what is missing. */
      select(overlays, types, filters, sessions, base) {
        S.overlaysOn = !!(overlays && overlays.length);
        const sel = types || [];
        S.selected = new Set(sel.filter((v) => !v.includes(".")));
        S.parts = new Set(sel.filter((v) => v.includes(".")));
        S.showSessions = !!(sessions && sessions.length);
        const f = JSON.stringify(filters || []);
        if (f !== S.filters) { clearDrawings(); S.filters = f; view(); }
        showBadges();
        invalidate();
        const req = need(wanted());
        return req || no();
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
        S.messages = payload.messages;
        showMessages();
        showBadges();
        invalidate();
        view();
        S.drawn.overlays = performance.now();
        const req = need(wanted()); // a type ticked while this one was on its way
        return req || no();
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
