/* =========================
   UTILITIES
========================= */
const getTextColor = () =>
  getComputedStyle(document.body).getPropertyValue("--text");

/* =========================
   SIDEBAR TOGGLE
========================= */
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  if (window.innerWidth <= 768) {
    sidebar.classList.toggle("show");
  } else {
    sidebar.classList.toggle("collapsed");
  }
}

/* Reset sidebar on resize */
window.addEventListener("resize", () => {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  if (window.innerWidth > 768) {
    sidebar.classList.remove("show");
  }
});

/* =========================
   THEME TOGGLE
========================= */
function setTheme(theme) {
  const icon = document.getElementById("themeIcon");

  if (theme === "dark") {
    document.body.classList.add("dark");
    icon?.classList.replace("bi-moon-fill", "bi-sun-fill");
  } else {
    document.body.classList.remove("dark");
    icon?.classList.replace("bi-sun-fill", "bi-moon-fill");
  }

  localStorage.setItem("theme", theme);
}

function toggleTheme() {
  const isDark = document.body.classList.contains("dark");
  setTheme(isDark ? "light" : "dark");
  updateChartsTheme();
}

/* =========================
   CHARTS
========================= */
let statusChart, usersChart;

function initCharts(data) {
  if (!window.Chart) return;

  statusChart = new Chart(document.getElementById("statusChart"), {
    type: "pie",
    data: {
      labels: ["Available", "Borrowed", "Overdue"],
      datasets: [{ data: data.bookStatus }]
    },
    options: { plugins: { legend: { position: "bottom", labels: { color: getTextColor() }}}}
  });

  usersChart = new Chart(document.getElementById("usersChart"), {
    type: "doughnut",
    data: {
      labels: ["Admins", "Teachers", "Students"],
      datasets: [{ data: data.userRoles }]
    },
    options: { plugins: { legend: { position: "bottom", labels: { color: getTextColor() }}}}
  });
}

function updateChartsTheme() {
  [statusChart, usersChart].forEach(chart => {
    if (!chart) return;
    chart.options.plugins.legend.labels.color = getTextColor();
    chart.update();
  });
}

/* =========================
   INIT
========================= */
document.addEventListener("DOMContentLoaded", () => {
  setTheme(localStorage.getItem("theme") || "light");
  if (window.dashboardData) initCharts(window.dashboardData);
});
