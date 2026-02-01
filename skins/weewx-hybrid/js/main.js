(function () {
  const apiBase = document.documentElement.dataset.apiBase || "/api";

  async function tryStatusPing() {
    try {
      const res = await fetch(`${apiBase}/status`, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      const footer = document.querySelector(".site-footer");
      if (!footer) return;
      const status = data.status || "unknown";
      footer.innerHTML = `API status: ${status}`;
    } catch (err) {
      // Ignore if API not running
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tryStatusPing);
  } else {
    tryStatusPing();
  }
})();
