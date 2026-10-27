/* Dark / bright switch (V2.7): sets data-theme on <html> (the CSS tokens in theme.css follow)
   and recolours the charts that are open, without reloading any data. A Dash clientside
   callback (window.dash_clientside.theme.apply) runs it from the remembered mode. */
(function () {
  "use strict";

  function recolourResults() {
    const R = (window.dash_clientside.results || {})._state;
    if (!R || !R.chart) return;
    const token = (name) => getComputedStyle(document.documentElement).getPropertyValue("--" + name).trim();
    R.chart.applyOptions({
      layout: {
        background: { type: "solid", color: token("panel") },
        textColor: token("text"),
        panes: { separatorColor: token("line") },
      },
      grid: { horzLines: { color: token("line") } },
      rightPriceScale: { borderColor: token("line") },
      timeScale: { borderColor: token("line") },
    });
  }

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    theme: {
      apply(mode) {
        const light = mode === "light";
        document.documentElement.dataset.theme = light ? "light" : "dark";
        const chart = window.dash_clientside.chart;
        if (chart && chart.applyTheme) chart.applyTheme();
        recolourResults();
        return light ? "◐ Dark" : "◑ Bright";
      },
    },
  });
})();
