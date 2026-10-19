/* Settings dialog: a click on a row's reset button (↺, data-path = its widget path) goes into the
   store st-reset-click. One store instead of one wildcard input per button: with 200+ of them the
   Dash renderer needed ~30 s to start the chart page. */
(function () {
  "use strict";
  let clicks = 0;
  document.addEventListener("click", (e) => {
    const button = e.target.closest(".st-reset");
    if (!button || !button.dataset.path) return;
    const dc = window.dash_clientside;
    if (dc && dc.set_props) dc.set_props("st-reset-click", { data: { path: button.dataset.path, n: ++clicks } });
  });

  /* Apply what the settings callback computed (store st-apply): widget values and row classes,
     only where they differ from what is shown. Writing a pattern-matched id with set_props
     keeps Dash's layout in step, so a rebuilt page shows the same. */
  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    settings: {
      apply(data) {
        const dc = window.dash_clientside;
        if (!data) return dc.no_update;
        for (const [path, cls] of Object.entries(data.classes || {})) {
          const id = { path, type: "st-row" };
          const el = document.getElementById(JSON.stringify(id));
          if (el && el.className !== cls) dc.set_props(id, { className: cls });
        }
        for (const [path, value] of Object.entries(data.values || {})) {
          dc.set_props({ path, type: "st-field" }, { value });
        }
        return dc.no_update;
      },
    },
  });
})();
