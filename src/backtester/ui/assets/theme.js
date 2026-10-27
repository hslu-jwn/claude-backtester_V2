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

  // ---- Plotly figures (dcc.Graph): Python builds them with the dark tokens, so recolour here ----
  const tokenOf = (name) => getComputedStyle(document.documentElement).getPropertyValue("--" + name).trim();
  const isLight = () => document.documentElement.dataset.theme === "light";
  const axisKeys = (gd) => Object.keys(gd.layout || {}).filter((k) => /^[xy]axis\d*$/.test(k));
  const getPath = (obj, path) => path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), obj);

  function lightTargets(gd) {
    const t = {
      paper_bgcolor: tokenOf("panel"),
      plot_bgcolor: tokenOf("panel"),
      "font.color": tokenOf("text"),
      "hoverlabel.bgcolor": tokenOf("panel"),
      "hoverlabel.bordercolor": tokenOf("line"),
      "hoverlabel.font.color": tokenOf("text"),
    };
    axisKeys(gd).forEach((a) => {
      t[a + ".gridcolor"] = tokenOf("line");
      t[a + ".zerolinecolor"] = tokenOf("line");
      t[a + ".linecolor"] = tokenOf("line");
      t[a + ".color"] = tokenOf("text");
    });
    return t;
  }

  function recolourPlot(gd) {
    if (!window.Plotly || !gd || !gd.layout || gd._themeBusy) return;
    const applied = gd._themeApplied;
    const themed = applied && gd.layout.paper_bgcolor === applied.paper_bgcolor;
    let update = null;
    if (isLight()) {
      const target = lightTargets(gd);
      if (themed && JSON.stringify(applied) === JSON.stringify(target)) return; // nothing to do
      if (!themed) {
        // a fresh (dark) figure: remember its own values so dark mode can restore them exactly
        gd._themeOrig = {};
        Object.keys(target).forEach((k) => {
          const v = getPath(gd.layout, k);
          gd._themeOrig[k] = v === undefined ? null : v;
        });
      }
      gd._themeApplied = target;
      update = target;
    } else if (themed && gd._themeOrig) {
      update = gd._themeOrig;
      gd._themeApplied = null;
      gd._themeOrig = null;
    } else {
      gd._themeApplied = null;
      return;
    }
    gd._themeBusy = true;
    Promise.resolve(window.Plotly.relayout(gd, update)).finally(() => {
      gd._themeBusy = false;
    });
  }

  function hookPlot(gd) {
    if (gd._themeHooked || typeof gd.on !== "function") return;
    gd._themeHooked = true;
    gd.on("plotly_afterplot", () => recolourPlot(gd));
  }

  function recolourPlotly() {
    document.querySelectorAll(".js-plotly-plot").forEach((gd) => {
      hookPlot(gd);
      recolourPlot(gd);
    });
  }

  let plotlyTimer = null;
  new MutationObserver(() => {
    clearTimeout(plotlyTimer);
    plotlyTimer = setTimeout(recolourPlotly, 100);
  }).observe(document.documentElement, { childList: true, subtree: true });

  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    theme: {
      apply(mode) {
        const light = mode === "light";
        document.documentElement.dataset.theme = light ? "light" : "dark";
        const chart = window.dash_clientside.chart;
        if (chart && chart.applyTheme) chart.applyTheme();
        recolourResults();
        recolourPlotly();
        return light ? "◐ Dark" : "◑ Bright";
      },
    },
  });
})();
