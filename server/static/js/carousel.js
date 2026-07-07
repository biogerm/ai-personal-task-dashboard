const carousel = (function () {
  let views = [];
  let currentIndex = 0;
  let timerId = null;
  let currentData = null;
  let currentIntervalSeconds = 300;

  function registerView(id, name, element, hasDataFn, onEnterFn, onExitFn) {
    if (!element) {
      console.warn(`Carousel: element for view ${name} is null`);
      return;
    }
    views.push({
      id,
      name,
      element,
      hasDataFn,
      onEnterFn,
      onExitFn,
    });
  }

  function initCarousel(config, data) {
    if (!config || views.length === 0) return;

    currentData = data;
    currentIntervalSeconds = config.intervalSeconds || 300;

    // Find first view with data
    let startIndex = 0;
    for (let i = 0; i < views.length; i++) {
      if (views[i].hasDataFn && views[i].hasDataFn(currentData)) {
        startIndex = i;
        break;
      }
    }

    currentIndex = startIndex;
    // Set initial display
    views.forEach((v, index) => {
      if (index === currentIndex) {
        v.element.style.display = "flex";
        v.element.style.opacity = "1";
      } else {
        v.element.style.display = "none";
        v.element.style.opacity = "0";
      }
    });

    if (views[currentIndex].onEnterFn) {
      views[currentIndex].onEnterFn(currentData);
    }

    if (views.length > 1) {
      startTimer(currentIntervalSeconds);
    }
  }

  function switchToNext() {
    if (views.length <= 1) return;

    let targetIndex = currentIndex;
    let found = false;

    for (let i = 1; i < views.length; i++) {
      const nextIndex = (currentIndex + i) % views.length;
      if (
        views[nextIndex].hasDataFn &&
        views[nextIndex].hasDataFn(currentData)
      ) {
        targetIndex = nextIndex;
        found = true;
        break;
      }
    }

    if (found && targetIndex !== currentIndex) {
      switchToView(targetIndex);
    }
  }

  function switchToView(targetIndex) {
    const oldView = views[currentIndex];
    const newView = views[targetIndex];

    if (oldView) {
      oldView.element.style.opacity = "0";
      if (oldView.onExitFn) {
        oldView.onExitFn();
      }
    }

    setTimeout(() => {
      if (oldView) {
        oldView.element.style.display = "none";
      }
      if (newView) {
        newView.element.style.display = "flex";
        // requestAnimationFrame fallback for Node.js testing
        if (typeof requestAnimationFrame !== "undefined") {
          requestAnimationFrame(() => {
            newView.element.style.opacity = "1";
          });
        } else {
          newView.element.style.opacity = "1";
        }

        if (newView.onEnterFn) {
          newView.onEnterFn(currentData);
        }
      }
    }, 500);

    currentIndex = targetIndex;

    if (timerId) {
      stopTimer();
      startTimer(currentIntervalSeconds);
    }
  }

  function startTimer(seconds) {
    if (seconds) currentIntervalSeconds = seconds;
    stopTimer();
    timerId = setInterval(() => {
      switchToNext();
    }, currentIntervalSeconds * 1000);
  }

  function stopTimer() {
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
  }

  function updateData(data) {
    currentData = data;
  }

  return {
    get views() {
      return views;
    },
    get currentIndex() {
      return currentIndex;
    },
    get timerId() {
      return timerId;
    },
    get currentData() {
      return currentData;
    },
    registerView,
    initCarousel,
    switchToNext,
    switchToView,
    startTimer,
    stopTimer,
    updateData,
    // for testing
    _reset: () => {
      views = [];
      currentIndex = 0;
      stopTimer();
      currentData = null;
    },
  };
})();

if (typeof window !== "undefined") {
  window.carousel = carousel;
}
if (typeof module !== "undefined") {
  module.exports = carousel;
}
