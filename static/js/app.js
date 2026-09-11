document.addEventListener("DOMContentLoaded", () => {
  // Live search filter for any table with id="dataTable" and an input with id="liveSearch"
  const search = document.querySelector("#liveSearch");
  const rows = document.querySelectorAll("#dataTable tbody tr[data-search]");
  if (search && rows.length) {
    search.addEventListener("input", () => {
      const q = search.value.toLowerCase();
      rows.forEach((row) => {
        const haystack = row.dataset.search.toLowerCase();
        row.style.display = haystack.includes(q) ? "" : "none";
      });
    });
  }

  // Mobile sidebar toggle
  const toggle = document.querySelector("#menuToggle");
  const sidebar = document.querySelector(".sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove("open");
      }
    });
  }

  // Auto-dismiss flash messages after a few seconds
  document.querySelectorAll(".alert[data-autohide]").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 4500);
  });

  // Confirm before any destructive/marking action
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // Highlight active sidebar link based on current path if not already server-marked
  const path = window.location.pathname;
  document.querySelectorAll(".nav a[href]").forEach((a) => {
    const href = a.getAttribute("href");
    if (href && href !== "/" && path.startsWith(href)) a.classList.add("active");
  });
});
