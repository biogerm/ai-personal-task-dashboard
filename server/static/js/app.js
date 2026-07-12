let lastKnownData = null;
let lastKnownTime = null;

function init() {
  updateClock();
  setInterval(updateClock, 1000);

  updateTheme();
  setInterval(updateTheme, 60000);

  if (typeof carousel !== "undefined") {
    carousel.registerView(
      0,
      "Dashboard",
      document.getElementById("screen-0"),
      () => true,
      (data) => {
        if (data) render(data);
      },
    );
    carousel.registerView(
      1,
      "Focus View",
      document.getElementById("screen-1"),
      (data) =>
        typeof focusView !== "undefined" ? focusView.focusHasData(data) : false,
      (data) => {
        if (typeof focusView !== "undefined" && data) {
          focusView.renderFocusView(data, true);
          if (typeof focusView.animateCards === "function") {
            focusView.animateCards();
          }
        }
      },
      () => {
        if (typeof focusView !== "undefined" && typeof focusView.exitCards === "function") {
          focusView.exitCards();
        }
      }
    );
  }

  fetchTasks();
  setInterval(fetchTasks, 60000);
}

function updateClock() {
  const now = new Date();

  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  const timeStr = `${hours}:${minutes}`;
  document.getElementById("clock").textContent = timeStr;
  const focusClock = document.getElementById("focus-clock");
  if (focusClock) focusClock.textContent = timeStr;

  const options = {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  };
  const dateStr = now.toLocaleDateString("en-US", options);
  document.getElementById("date").textContent = dateStr;
  const focusDate = document.getElementById("focus-date");
  if (focusDate) focusDate.textContent = dateStr;
}

function updateTheme() {
  document.body.classList.remove("dark-theme");
  document.body.classList.add("light-theme");
}

function fetchTasks() {
  fetch("/api/tasks")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      if (data.locale) {
        window.APP_LOCALE = data.locale;
      }
      lastKnownData = data;
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      lastKnownTime = `${hours}:${minutes}`;
      render(data);
      if (typeof focusView !== "undefined") {
        focusView.renderFocusView(data);
      }
      if (typeof carousel !== "undefined") {
        carousel.updateData(data);
        if (!carousel.timerId && data.carousel) {
          carousel.initCarousel(data.carousel, data);
        }
      }
    })
    .catch((error) => {
      console.error("Fetch error:", error);
      updateSyncStatus(null);
    });
}

function render(data) {
  const calendarGrid = document.getElementById("calendar-grid");
  const projectsList = document.getElementById("projects-list");

  calendarGrid.innerHTML = "";
  projectsList.innerHTML = "";

  // Generate Calendar
  generateCalendar(calendarGrid, data.projects || []);

  if (!data.projects || data.projects.length === 0) {
    projectsList.innerHTML =
      '<li class="empty-state">' + t("ui.no_active") + "</li>";
  } else {
    const todayProjects = data.projects.filter((p) => p.urgency === "today");
    const overdueProjects = data.projects.filter(
      (p) => p.urgency === "overdue",
    );
    const allOtherProjects = data.projects.filter(
      (p) => p.urgency !== "today" && p.urgency !== "overdue",
    );

    projectsList.innerHTML = "";

    if (todayProjects.length > 0) {
      const header = document.createElement("li");
      header.className = "list-section-header header-today";
      header.innerHTML = "<span>" + t("ui.due_today") + "</span>";
      projectsList.appendChild(header);
      todayProjects.forEach((p) => projectsList.appendChild(renderProject(p)));
    }

    if (overdueProjects.length > 0) {
      const header = document.createElement("li");
      header.className = "list-section-header header-overdue";
      header.innerHTML = "<span>" + t("ui.overdue") + "</span>";
      projectsList.appendChild(header);
      overdueProjects.forEach((p) =>
        projectsList.appendChild(renderProject(p)),
      );
    }

    if (allOtherProjects.length > 0) {
      const header = document.createElement("li");
      header.className = "list-section-header header-other";
      header.textContent = t("ui.other_projects");
      projectsList.appendChild(header);

      let otherCount = 0;

      for (const project of allOtherProjects) {
        const li = renderProject(project);
        projectsList.appendChild(li);

        // Add dummy indicator to check if we overflow WITH the indicator
        const dummy = document.createElement("li");
        dummy.className = "project-item empty-state";
        dummy.style.padding = "8px 16px";
        dummy.textContent = t("ui.more");
        projectsList.appendChild(dummy);

        const isOverflowing =
          projectsList.scrollHeight > projectsList.clientHeight;

        projectsList.removeChild(dummy);

        if (isOverflowing && otherCount > 0) {
          projectsList.removeChild(li);
          break;
        }

        // If even the first item overflows, we still keep it (don't break immediately on count 0 unless we really have no space, but let's keep at least 1)
        if (isOverflowing && otherCount === 0) {
          // Keep the first item, but break after it
          otherCount++;
          break;
        }

        otherCount++;
      }

      const hiddenOthersCount = allOtherProjects.length - otherCount;
      if (hiddenOthersCount > 0) {
        const moreIndicator = document.createElement("li");
        moreIndicator.className = "project-item empty-state";
        moreIndicator.style.padding = "8px 16px";
        moreIndicator.textContent = t("ui.more_projects", {
          count: hiddenOthersCount,
        });
        projectsList.appendChild(moreIndicator);
      }
    }
  }

  updateSyncStatus(data);
}

function generateCalendar(container, projects) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const dayOfWeek = today.getDay(); // 0 is Sunday, 1 is Monday
  const offset = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // days since Monday

  const startDate = new Date(today);
  startDate.setDate(startDate.getDate() - offset);

  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  // Create headers
  days.forEach((day) => {
    const d = document.createElement("div");
    d.className = "cal-header";
    d.textContent = day;
    container.appendChild(d);
  });

  // Create 28 days
  for (let i = 0; i < 28; i++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(startDate.getDate() + i);

    const cell = document.createElement("div");
    cell.className = "cal-cell";

    if (currentDate.getTime() === today.getTime()) {
      cell.classList.add("today");
    }

    const dateDiv = document.createElement("div");
    dateDiv.className = "cal-date";
    dateDiv.textContent = currentDate.getDate();
    cell.appendChild(dateDiv);

    const dateStr =
      currentDate.getFullYear() +
      "-" +
      String(currentDate.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(currentDate.getDate()).padStart(2, "0");

    projects.forEach((p) => {
      if (p.due_date && p.due_date.startsWith(dateStr) && p.abbr) {
        const chip = document.createElement("div");
        chip.className = "cal-task-chip";

        let priorityClass = "chip-none";
        if (p.priority_label) {
          const pl = p.priority_label.toLowerCase();
          if (pl === "high") priorityClass = "chip-high";
          else if (pl === "medium") priorityClass = "chip-medium";
          else if (pl === "low") priorityClass = "chip-low";
        }
        chip.classList.add(priorityClass);
        chip.textContent = p.abbr;
        cell.appendChild(chip);
      }
    });

    container.appendChild(cell);
  }
}

function renderProject(project) {
  const li = document.createElement("li");
  li.className = "project-item";

  const leftContent = document.createElement("div");
  leftContent.style.display = "flex";
  leftContent.style.alignItems = "center";
  leftContent.style.flex = "1";
  leftContent.style.overflow = "hidden";

  const iconSpan = document.createElement("span");
  iconSpan.className = "project-icon";
  iconSpan.style.display = "flex";
  iconSpan.style.alignItems = "center";
  iconSpan.style.justifyContent = "center";
  iconSpan.style.width = "24px";
  iconSpan.style.height = "24px";
  iconSpan.style.marginRight = "12px";
  iconSpan.style.fontSize = "1.2rem";
  iconSpan.style.flexShrink = "0";

  if (project.priority_emoji) {
    iconSpan.textContent = project.priority_emoji;
  } else {
    iconSpan.textContent = "🔸";
  }

  const titleSpan = document.createElement("span");
  titleSpan.className = "project-title";
  if (project.urgency === "today") {
    titleSpan.classList.add("title-today");
  } else if (project.urgency === "overdue") {
    titleSpan.classList.add("title-overdue");
  } else {
    titleSpan.classList.add("title-other");
  }
  titleSpan.textContent = project.title;

  leftContent.appendChild(iconSpan);
  leftContent.appendChild(titleSpan);

  const rightContent = document.createElement("div");
  rightContent.style.display = "flex";
  rightContent.style.alignItems = "center";
  rightContent.style.flexShrink = "0";
  rightContent.style.marginLeft = "12px";

  const sourceIcon = document.createElement("span");
  sourceIcon.style.marginRight = "8px";
  sourceIcon.style.display = "flex";
  sourceIcon.style.alignItems = "center";
  sourceIcon.style.color = "var(--text-secondary)";
  sourceIcon.style.opacity = "0.5";

  if (project.is_ios_reminder) {
    sourceIcon.innerHTML =
      '<svg viewBox="0 0 384 512" width="14" height="14" fill="currentColor"><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 24 184.8 8 273.5q-9 59.4 20 114.1c11.1 21.1 25.5 49.2 58.1 48.1 31.1-1.1 42.6-20.2 81.3-20.2 38.6 0 49.6 19.3 82.2 19.3 33.4 0 44.8-23.7 64.6-54.8 22-34.8 31.5-68.5 32-70.2-2.1-1.3-30.6-15.9-30.6-55.9zM201.2 129.5c18.5-22.6 30.6-54.2 27.2-85.5-25.5 1-56.1 17.2-75 39.8-16.7 19.9-30 52-25.8 82.2 28.5 2.2 55.1-13.9 73.6-36.5z"/></svg>';
  } else {
    sourceIcon.innerHTML =
      '<svg class="notion-icon" viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.933zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.139c-.093-.514.28-.887.747-.933zM1.936 1.035l13.31-.98c1.634-.14 2.055-.047 3.082.7l4.249 2.986c.7.513.934.653.934 1.213v16.378c0 1.026-.373 1.634-1.68 1.726l-15.458.934c-.98.047-1.448-.093-1.962-.747l-3.129-4.06c-.56-.747-.793-1.306-.793-1.96V2.667c0-.839.374-1.54 1.447-1.632z"/></svg>';
  }
  rightContent.appendChild(sourceIcon);

  let dateText = "";
  let urgencyClass = "";

  switch (project.urgency) {
    case "overdue":
      dateText = t("ui.overdue_tag");
      urgencyClass = "urgency-overdue";
      break;
    case "today":
      dateText = t("ui.today_tag");
      urgencyClass = "urgency-today";
      break;
    case "upcoming":
      if (project.due_date) {
        const due = new Date(project.due_date);
        dateText = due.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        });
      }
      urgencyClass = "urgency-upcoming";
      break;
    case "no-date":
    default:
      urgencyClass = "urgency-no-date";
      break;
  }

  if (urgencyClass) {
    li.classList.add(urgencyClass);
  }

  if (dateText) {
    const dateSpan = document.createElement("span");
    dateSpan.className = "reminder-date";
    dateSpan.textContent = dateText;
    rightContent.appendChild(dateSpan);
  }

  if (project.priority_label) {
    let priorityClass = "";
    if (project.priority_label.toLowerCase() === "high") {
      priorityClass = "priority-high";
    } else if (project.priority_label.toLowerCase() === "medium") {
      priorityClass = "priority-medium";
    } else if (project.priority_label.toLowerCase() === "low") {
      priorityClass = "priority-low";
    }

    if (priorityClass) {
      li.classList.add(priorityClass);
    }
  }

  li.appendChild(leftContent);
  li.appendChild(rightContent);

  return li;
}

function updateSyncStatus(data) {
  const statusSpan = document.getElementById("sync-status");
  statusSpan.className = "";

  if (!data) {
    statusSpan.textContent = t("ui.offline", {
      time: lastKnownTime || t("ui.unknown"),
    });
    statusSpan.classList.add("offline");
    return;
  }

  const sources = data.sources || {};
  let errorSources = [];
  let isPending = true;

  for (const key in sources) {
    if (sources[key].status === "error") {
      errorSources.push(key);
    }
    if (sources[key].status !== "pending") {
      isPending = false;
    }
  }

  if (errorSources.length > 0) {
    statusSpan.textContent = t("ui.sync_failed", {
      sources: errorSources.join(", "),
    });
    statusSpan.classList.add("offline");
  } else if (isPending) {
    statusSpan.textContent = t("ui.loading");
  } else {
    const updateDate = new Date(data.last_updated);
    const hours = String(updateDate.getHours()).padStart(2, "0");
    const minutes = String(updateDate.getMinutes()).padStart(2, "0");
    statusSpan.textContent = t("ui.last_sync", { time: `${hours}:${minutes}` });
  }
}

document.addEventListener("DOMContentLoaded", init);
