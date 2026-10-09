/* Toolbar popovers (ROADMAP 4.0): a button with data-pop="<id>" opens / closes the popover
   with that id; a click outside any open popover (or Escape, once its menus are closed)
   closes it. Modals (ROADMAP 4.1, the settings panel): a button with data-modal="<id>"
   opens the modal with that id (and closes the popovers), data-modal-close="<id>", a click
   on the backdrop or Escape closes it. Pure browser state, no Dash callback: the contents
   are ordinary Dash components. */
(function () {
  "use strict";

  function closeAll(except) {
    for (const pop of document.querySelectorAll(".tb-pop.open")) {
      if (pop !== except) pop.classList.remove("open");
    }
  }

  function openModal() {
    return document.querySelector(".st-backdrop.open");
  }

  document.addEventListener("click", (e) => {
    // a dropdown option is removed from the page when it is picked, before this click
    // arrives: it was inside whatever holds the dropdown, never an outside click
    if (!e.target.isConnected) return;
    const opener = e.target.closest("[data-modal]");
    if (opener) {
      const modal = document.getElementById(opener.dataset.modal);
      if (modal) { closeAll(null); modal.classList.add("open"); }
      return;
    }
    const closer = e.target.closest("[data-modal-close]");
    if (closer) {
      const modal = document.getElementById(closer.dataset.modalClose);
      if (modal) modal.classList.remove("open");
      return;
    }
    if (e.target.classList && e.target.classList.contains("st-backdrop")) {
      e.target.classList.remove("open"); // click on the dimmed backdrop
      return;
    }
    if (openModal()) return; // clicks inside the modal leave the popovers alone
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
      // a menu or calendar open inside a popover / the modal closes first (the component)
      if (document.querySelector(".tb-pop.open [id^='radix-'], .st-backdrop.open [id^='radix-']")) {
        return;
      }
      const modal = openModal();
      if (modal) { modal.classList.remove("open"); return; }
      closeAll(null);
    },
    true,
  );
})();
