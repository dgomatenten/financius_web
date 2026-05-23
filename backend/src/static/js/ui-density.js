(function () {
  const key = "uiDensityMode";
  const body = document.body;
  const btn = document.getElementById("densityToggleBtn");

  function apply(mode) {
    const compact = mode === "compact";
    body.classList.toggle("compact", compact);
    if (btn) {
      btn.textContent = compact ? "Comfort" : "Compact";
      btn.setAttribute("aria-pressed", compact ? "true" : "false");
    }
  }

  const savedMode = localStorage.getItem(key) || "comfortable";
  apply(savedMode);

  if (btn) {
    btn.addEventListener("click", function () {
      const next = body.classList.contains("compact") ? "comfortable" : "compact";
      localStorage.setItem(key, next);
      apply(next);
    });
  }
})();
