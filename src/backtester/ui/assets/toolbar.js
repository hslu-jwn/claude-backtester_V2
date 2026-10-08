/* Toolbar popovers (ROADMAP 4.0): a button with data-pop="<id>" opens / closes the popover
   with that id; a click outside any open popover (or Escape, once its menus are closed)
   closes it. Pure browser state, no Dash callback: the popovers' contents are ordinary
   Dash components. */
(function () {
  "use strict";

  function closeAll(except) {
    for (const pop of document.querySelectorAll(".tb-pop.open")) {
      if (pop !== except) pop.classList.remove("open");
    }
  }

  document.addEventListener("click", (e) => {
    const button = e.target.closest("[data-pop]");
    if (button) {
      const pop = document.getElementById(button.dataset.pop);
      if (!pop) return;
      closeAll(pop);
      pop.classList.toggle("open");
      return;
    }
    if (e.target.closest(".tb-pop")) return; // inside a popover (incl. its menus)
    closeAll(null);
  });

  // capture phase: runs before the component that may close its menu on the same key
  document.addEventListener(
    "keydown",
    (e) => {
      if (e.key !== "Escape") return;
      // a menu or calendar open inside a popover closes first (the component handles it)
      if (document.querySelector(".tb-pop.open [id^='radix-']")) return;
      closeAll(null);
    },
    true,
  );
})();
