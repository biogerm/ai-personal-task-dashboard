// focus.js
// Implementation of Focus View (M9)

function filterFocusTasks(projects) {
  if (!projects) return [];

  // 1. High priority tasks
  const highPriority = projects.filter(
    (p) => p.priority_label && p.priority_label.toLowerCase() === "high",
  );

  // 2. Today but not high priority tasks
  const todayNonHigh = projects.filter(
    (p) =>
      p.urgency === "today" &&
      (!p.priority_label || p.priority_label.toLowerCase() !== "high"),
  );

  // 3. Sorting rules: overdue -> today -> upcoming -> no-date
  const urgencyWeight = { overdue: 0, today: 1, upcoming: 2, "no-date": 3 };

  const sortFn = (a, b) => {
    const wa = urgencyWeight[a.urgency] ?? 3;
    const wb = urgencyWeight[b.urgency] ?? 3;
    if (wa !== wb) return wa - wb;

    const da = a.due_date || "9999-12-31";
    const db = b.due_date || "9999-12-31";
    return da.localeCompare(db);
  };

  highPriority.sort(sortFn);
  todayNonHigh.sort(sortFn);

  return [...highPriority, ...todayNonHigh];
}

function focusHasData(data) {
  if (!data || !data.projects) return false;
  const tasks = filterFocusTasks(data.projects);
  return tasks.length > 0;
}

function getGridLayout(count) {
  if (count <= 0) return { cols: 1, rows: 1, fillScreen: false };
  if (count === 1) return { cols: 1, rows: 1, fillScreen: false };
  if (count === 2) return { cols: 2, rows: 1, fillScreen: false };
  if (count === 3) return { cols: 3, rows: 1, fillScreen: false };
  if (count === 4) return { cols: 2, rows: 2, fillScreen: true };
  if (count <= 6) return { cols: 2, rows: 3, fillScreen: true };
  if (count <= 9) return { cols: 3, rows: 3, fillScreen: true };
  return { cols: 4, rows: 3, fillScreen: true }; // > 9
}

function renderFocusCard(task, index, isSupplementary) {
  const card = document.createElement("div");
  card.className = "focus-card";

  if (isSupplementary) {
    card.classList.add("focus-card-today");
  } else {
    card.classList.add("focus-card-high");
  }

  const emojiEl = document.createElement("div");
  emojiEl.className = "focus-card-emoji";
  emojiEl.textContent = task.priority_emoji || "🔸";

  const titleEl = document.createElement("div");
  titleEl.className = "focus-card-title";
  titleEl.textContent = task.title;

  const metaEl = document.createElement("div");
  metaEl.className = "focus-card-meta";

  if (task.urgency === "overdue") {
    metaEl.textContent =
      typeof t === "function" ? t("focus.overdue") : "Overdue";
    metaEl.classList.add("date-overdue");
  } else if (task.urgency === "today") {
    metaEl.textContent = typeof t === "function" ? t("focus.today") : "Today";
    metaEl.classList.add("date-today");
  } else if (task.due_date) {
    const due = new Date(task.due_date);
    metaEl.textContent = due.toLocaleDateString(
      typeof window !== "undefined" && window.APP_LOCALE === "zh"
        ? "zh-CN"
        : "en-US",
      { month: "short", day: "numeric" },
    );
  } else {
    metaEl.textContent =
      typeof t === "function" ? t("focus.no_date") : "No Date";
  }

  card.appendChild(emojiEl);
  card.appendChild(titleEl);
  card.appendChild(metaEl);

  // Initial transition state (opacity 0, translateY 20px via CSS)
  card.style.transitionDelay = `${index * 80}ms`;

  return card;
}

function animateCards() {
  const cards = document.querySelectorAll(".focus-card");
  cards.forEach((card) => {
    card.classList.remove("focus-card-enter");
  });

  // trigger reflow
  const grid = document.getElementById("focus-grid");
  if (grid) void grid.offsetHeight;

  cards.forEach((card, index) => {
    setTimeout(() => {
      card.classList.add("focus-card-enter");
    }, index * 80);
  });
}

function renderFocusView(data) {
  const grid = document.getElementById("focus-grid");
  if (!grid) return;

  grid.innerHTML = "";

  if (!data || !data.projects) return;

  const highPriority = data.projects.filter(
    (p) => p.priority_label && p.priority_label.toLowerCase() === "high",
  );
  const todayNonHigh = data.projects.filter(
    (p) =>
      p.urgency === "today" &&
      (!p.priority_label || p.priority_label.toLowerCase() !== "high"),
  );

  const urgencyWeight = { overdue: 0, today: 1, upcoming: 2, "no-date": 3 };
  const sortFn = (a, b) => {
    const wa = urgencyWeight[a.urgency] ?? 3;
    const wb = urgencyWeight[b.urgency] ?? 3;
    if (wa !== wb) return wa - wb;
    const da = a.due_date || "9999-12-31";
    const db = b.due_date || "9999-12-31";
    return da.localeCompare(db);
  };

  highPriority.sort(sortFn);
  todayNonHigh.sort(sortFn);

  let allTasks = [...highPriority, ...todayNonHigh];

  const layout = getGridLayout(allTasks.length);
  const maxTasks = layout.cols * layout.rows;
  if (allTasks.length > maxTasks) {
    allTasks = allTasks.slice(0, maxTasks);
  }

  grid.style.gridTemplateColumns = `repeat(${layout.cols}, 1fr)`;
  grid.style.gridTemplateRows = layout.fillScreen
    ? `repeat(${layout.rows}, 1fr)`
    : "auto";

  if (layout.fillScreen) {
    grid.classList.add("fill-screen");
  } else {
    grid.classList.remove("fill-screen");
    grid.style.gridTemplateColumns = `repeat(${layout.cols}, minmax(0, 280px))`;
  }

  allTasks.forEach((task, idx) => {
    const isSupplementary = !highPriority.includes(task);
    const card = renderFocusCard(task, idx, isSupplementary);
    grid.appendChild(card);
  });

  animateCards();
}

if (typeof window !== "undefined") {
  window.focusView = {
    filterFocusTasks,
    focusHasData,
    getGridLayout,
    renderFocusCard,
    renderFocusView,
    animateCards,
  };
} else if (typeof module !== "undefined") {
  module.exports = {
    filterFocusTasks,
    focusHasData,
    getGridLayout,
    renderFocusCard,
    renderFocusView,
    animateCards,
  };
}
