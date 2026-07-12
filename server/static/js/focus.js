// focus.js
// Implementation of Focus View (M9)

// --- TESTING MODE ---
const USE_MOCK = false;
const MOCK_COUNT = 10;
// --------------------

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
  if (count === 1) return { cols: 1, rows: 1, fillScreen: true };
  if (count === 2) return { cols: 1, rows: 2, fillScreen: true }; // 1 column, 2 rows ensures horizontal cards
  if (count === 3) return { cols: 2, rows: 2, fillScreen: true }; // 2x2 grid for 3 items
  if (count === 4) return { cols: 2, rows: 2, fillScreen: true };
  if (count <= 6) return { cols: 2, rows: 3, fillScreen: true }; // 2 columns, 3 rows for better horizontal aspect ratio
  if (count <= 9) return { cols: 3, rows: 3, fillScreen: true };
  return { cols: 4, rows: 3, fillScreen: true }; // > 9
}

function renderFocusCard(task, index, isSupplementary, animate = false) {
  const card = document.createElement("div");
  card.className = "focus-card";

  if (isSupplementary) {
    card.classList.add("focus-card-today");
  } else {
    card.classList.add("focus-card-high");
  }

  const leftEl = document.createElement("div");
  leftEl.className = "focus-card-left";

  const titleEl = document.createElement("div");
  titleEl.className = "focus-card-title";
  titleEl.textContent = task.title;
  leftEl.appendChild(titleEl);

  const rightEl = document.createElement("div");
  rightEl.className = "focus-card-right";

  if (task.urgency === "today") {
    card.classList.add("shake-target");
  }

  if (task.urgency === "overdue" || task.urgency === "today") {
    const vertEl = document.createElement("div");
    vertEl.className = "countdown-vertical";
    vertEl.textContent = "已到期";
    rightEl.appendChild(vertEl);
  } else if (task.due_date) {
    const due = new Date(task.due_date);
    const todayDate = new Date();
    due.setHours(0, 0, 0, 0);
    todayDate.setHours(0, 0, 0, 0);
    const diffTime = due.getTime() - todayDate.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays > 0) {
      const numEl = document.createElement("div");
      numEl.className = "countdown-number";
      numEl.textContent = diffDays;
      
      const textEl = document.createElement("div");
      textEl.className = "countdown-text";
      textEl.textContent = "天";
      
      rightEl.appendChild(numEl);
      rightEl.appendChild(textEl);
    }
  }

  card.appendChild(leftEl);
  if (rightEl.childNodes.length > 0) {
    card.appendChild(rightEl);
  } else {
    card.classList.add("focus-card-no-date");
  }

  if (animate) {
    card.style.transitionDelay = `${index * 80}ms`;
  } else {
    card.style.transitionDelay = `0ms`;
  }

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

function exitCards() {
  const cards = document.querySelectorAll(".focus-card");
  cards.forEach((card) => {
    card.classList.remove("focus-card-enter");
  });
}

function renderFocusView(data, animate = false) {
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

  if (typeof window !== "undefined" && USE_MOCK) {
    const mockCount = MOCK_COUNT;
    if (!isNaN(mockCount)) {
      // Extended pool of mock titles
      let MOCK_TITLES = [
        "检查基金出售并转换",
        "更新Google Home任务视图",
        "查看Sportby二手雪板记录",
        "申请美国签证",
        "Get a work certificate from HR",
        "Put my iPhone 13 advertisement online again",
        "Print traffic accident pdf in the office"
      ];
      
      // Shuffle the mock titles randomly
      for (let i = MOCK_TITLES.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [MOCK_TITLES[i], MOCK_TITLES[j]] = [MOCK_TITLES[j], MOCK_TITLES[i]];
      }

      allTasks = [];
      for(let i=0; i<mockCount; i++) {
        // Randomly assign today/overdue/no-date to make it realistic
        const rand = Math.random();
        let urgency = "upcoming";
        let hasDate = true;
        if (rand < 0.2) urgency = "overdue";
        else if (rand < 0.5) urgency = "today";
        else if (rand < 0.8) { urgency = "upcoming"; hasDate = false; }
        
        allTasks.push({
          id: "mock_" + i,
          title: MOCK_TITLES[i % MOCK_TITLES.length],
          priority_emoji: "🔸",
          urgency: urgency,
          due_date: hasDate ? new Date(Date.now() + 86400000 * Math.floor(Math.random()*5)).toISOString() : null
        });
      }
    }
  }

  const layout = getGridLayout(allTasks.length);
  const maxTasks = layout.cols * layout.rows;
  if (allTasks.length > maxTasks) {
    allTasks = allTasks.slice(0, maxTasks);
  }

  grid.setAttribute("data-count", allTasks.length);

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
    const card = renderFocusCard(task, idx, isSupplementary, animate);
    
    if (!animate) {
      card.style.transition = "none";
      card.classList.add("focus-card-enter");
      setTimeout(() => { if (card) card.style.transition = ""; }, 50);
    }
    
    grid.appendChild(card);
  });
}

if (typeof window !== "undefined") {
  window.focusView = {
    filterFocusTasks,
    focusHasData,
    getGridLayout,
    renderFocusCard,
    renderFocusView,
    animateCards,
    exitCards,
  };

  // Add shaking animation interval for today's cards every 17 seconds
  // (17 is a prime number that avoids resonance with 60s data fetches and 300s screen switches)
  setInterval(() => {
    const todayCards = document.querySelectorAll('.shake-target');
    todayCards.forEach(card => {
      card.classList.add('shake');
      setTimeout(() => {
        card.classList.remove('shake');
      }, 600); // match animation duration
    });
  }, 17000);

} else if (typeof module !== "undefined") {
  module.exports = {
    filterFocusTasks,
    focusHasData,
    getGridLayout,
    renderFocusCard,
    renderFocusView,
    animateCards,
    exitCards,
  };
}
