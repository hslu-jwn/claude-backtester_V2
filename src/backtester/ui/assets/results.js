/* Results page (ROADMAP 3.6): the equity curve in R with Lightweight Charts, like the main
   chart. Data from pages/results.py `equity_payload` (UTC seconds, cumulative R gross and
   net, net drawdown <= 0). Pane 0: net (area) and gross (line); pane 1: the drawdown,
   shaded below 0. A Dash clientside callback (window.dash_clientside.results.equity). */
(function () {
  "use strict";

  const R = { chart: null, el: null };
  const rFormat = { type: "custom", minMove: 0.01, formatter: (v) => v.toFixed(2) + " R" };

  function draw(data, tries) {
    const el = document.getElementById("rs-equity");
    if (!el) {
      // the overview is rendered in the same update: wait for it a few frames
      if (tries < 20) requestAnimationFrame(() => draw(data, tries + 1));
      return;
    }
    if (R.chart) { R.chart.remove(); R.chart = null; }
    const L = window.LightweightCharts;
    R.el = el;
    el.textContent = "";
    const chart = L.createChart(el, {
      autoSize: true,
      layout: {
        background: { type: "solid", color: "#ffffff" },
        textColor: "#131722",
        fontSize: 12,
        attributionLogo: true,
        panes: { separatorColor: "#e0e3eb" },
      },
      grid: { vertLines: { visible: false }, horzLines: { color: "#f0f3fa" } },
      rightPriceScale: { borderColor: "#e0e3eb" },
      timeScale: { borderColor: "#e0e3eb", timeVisible: true, secondsVisible: false },
      localization: { dateFormat: "yyyy-MM-dd" },
      crosshair: { mode: L.CrosshairMode.Normal },
    });
    const c = data.colors;
    const net = chart.addSeries(L.AreaSeries, {
      lineColor: c.net, topColor: c.net + "33", bottomColor: c.net + "05", lineWidth: 2,
      priceFormat: rFormat, title: "Net",
    });
    const gross = chart.addSeries(L.LineSeries, {
      color: c.gross, lineWidth: 1, lineStyle: L.LineStyle.Dashed,
      priceFormat: rFormat, title: "Gross",
    });
    const dd = chart.addSeries(L.BaselineSeries, {
      baseValue: { type: "price", price: 0 },
      topLineColor: "rgba(0,0,0,0)", topFillColor1: "rgba(0,0,0,0)", topFillColor2: "rgba(0,0,0,0)",
      bottomLineColor: c.dd, bottomFillColor1: c.dd + "26", bottomFillColor2: c.dd + "59",
      lineWidth: 1, priceFormat: rFormat, title: "Drawdown",
    }, 1);
    const pts = (key) => data.t.map((t, i) => ({ time: t, value: data[key][i] }));
    net.setData(pts("net"));
    gross.setData(pts("gross"));
    dd.setData(pts("dd"));
    const panes = chart.panes();
    if (panes.length > 1) { panes[0].setHeight(300); panes[1].setHeight(110); }
    chart.timeScale().fitContent();
    R.chart = chart;
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    results: {
      _state: R,
      equity(data) {
        if (!data || !data.t || !data.t.length) {
          if (R.chart) { R.chart.remove(); R.chart = null; }
          return null;
        }
        draw(data, 0);
        return null;
      },
    },
  });
})();
