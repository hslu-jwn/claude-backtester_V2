/* Top-bar gear opens the existing Live connection fold without duplicating its form. */
(function () {
  let pending = location.pathname === "/live" && location.hash === "#connection";
  function openConnection() {
    if (!pending || location.pathname !== "/live" || location.hash !== "#connection") return;
    const fold = document.getElementById("tr-section");
    if (fold) {
      pending = false;
      fold.open = true;
      fold.scrollIntoView({ block: "start", behavior: "smooth" });
    }
  }
  function requestOpen() {
    pending = location.pathname === "/live" && location.hash === "#connection";
    openConnection();
  }
  new MutationObserver(openConnection).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener("hashchange", requestOpen);
  document.addEventListener("click", function (event) {
    if (event.target.closest("#nav-settings")) setTimeout(requestOpen, 0);
  });
  openConnection();
})();
