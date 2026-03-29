/* Minimal JavaScript */
document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("meetings-form");
  var tabButtons = document.querySelectorAll("[data-tab-target]");
  var fileInput = document.getElementById("meeting-file");
  var fileLabel = document.getElementById("meeting-file-label");
  var transcriptInput = document.getElementById("transcript");
  var alertBox = document.getElementById("meetings-inline-alert");
  var submitButton = document.getElementById("meetings-submit-button");
  var statusInput = document.getElementById("meeting-status-step-input");
  var statusProcessing = document.getElementById(
    "meeting-status-step-processing",
  );
  var statusResults = document.getElementById("meeting-status-step-results");
  var statusLineOne = document.getElementById("meeting-status-line-1");
  var statusLineTwo = document.getElementById("meeting-status-line-2");
  var summaryCount = document.getElementById("summary-count");
  var tasksCount = document.getElementById("tasks-count");
  var priorityCount = document.getElementById("priority-count");
  var summaryContent = document.getElementById("summary-content");
  var tasksContent = document.getElementById("tasks-content");
  var priorityContent = document.getElementById("priority-content");

  if (!tabButtons.length) {
    return;
  }

  var activateTab = function (targetId) {
    tabButtons.forEach(function (button) {
      var isActive = button.getAttribute("data-tab-target") === targetId;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    document.querySelectorAll(".meetings-tab-panel").forEach(function (panel) {
      var isActive = panel.id === targetId;
      panel.classList.toggle("is-active", isActive);
      panel.hidden = !isActive;
    });
  };

  tabButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      activateTab(button.getAttribute("data-tab-target"));
    });
  });

  var escapeHtml = function (value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  };

  var setStatusState = function (state) {
    [statusInput, statusProcessing, statusResults].forEach(function (element) {
      if (!element) {
        return;
      }
      element.classList.remove("is-active", "is-complete", "is-pending");
    });

    [statusLineOne, statusLineTwo].forEach(function (element) {
      if (!element) {
        return;
      }
      element.classList.remove("is-complete");
    });

    if (state === "processing") {
      statusInput.classList.add("is-complete");
      statusProcessing.classList.add("is-active");
      statusResults.classList.add("is-pending");
      statusLineOne.classList.add("is-complete");
      return;
    }

    if (state === "complete") {
      statusInput.classList.add("is-complete");
      statusProcessing.classList.add("is-complete");
      statusResults.classList.add("is-active");
      statusLineOne.classList.add("is-complete");
      statusLineTwo.classList.add("is-complete");
      return;
    }

    statusInput.classList.add("is-active");
    statusProcessing.classList.add("is-pending");
    statusResults.classList.add("is-pending");
  };

  var setAlertMessage = function (message) {
    if (!alertBox) {
      return;
    }

    if (message) {
      alertBox.textContent = message;
      alertBox.classList.remove("is-hidden");
      return;
    }

    alertBox.textContent = "";
    alertBox.classList.add("is-hidden");
  };

  var updateCount = function (element, text) {
    if (!element) {
      return;
    }

    if (text) {
      element.textContent = text;
      element.classList.remove("is-hidden");
      return;
    }

    element.textContent = "";
    element.classList.add("is-hidden");
  };

  var renderSummary = function (summary) {
    if (!summaryContent) {
      return;
    }

    if (summary.length) {
      summaryContent.innerHTML =
        '<ul class="meetings-summary-list">' +
        summary
          .map(function (point) {
            return "<li>" + escapeHtml(point) + "</li>";
          })
          .join("") +
        "</ul>";
      return;
    }

    summaryContent.innerHTML =
      '<p class="meetings-empty-copy">Run the analysis to view a clean summary of decisions and important discussion.</p>';
  };

  var renderTasks = function (tasks) {
    if (!tasksContent) {
      return;
    }

    if (tasks.length) {
      tasksContent.innerHTML =
        '<div class="meetings-task-list">' +
        tasks
          .map(function (task) {
            var priorityClass =
              "meetings-priority-" +
              String(task.priority || "medium").toLowerCase();
            return (
              '<article class="meetings-task-row">' +
              '<div class="meetings-task-main">' +
              "<strong>" +
              escapeHtml(task.task || "") +
              "</strong>" +
              "<span>" +
              escapeHtml(task.owner || "") +
              "</span>" +
              "</div>" +
              '<span class="meetings-task-priority ' +
              priorityClass +
              '">' +
              escapeHtml(task.priority || "Medium") +
              "</span>" +
              "</article>"
            );
          })
          .join("") +
        "</div>";
      return;
    }

    tasksContent.innerHTML =
      '<p class="meetings-empty-copy">Action items will appear here once the meeting transcript is processed.</p>';
  };

  var renderPriorityTasks = function (tasks) {
    if (!priorityContent) {
      return;
    }

    if (tasks.length) {
      priorityContent.innerHTML =
        '<div class="meetings-priority-grid">' +
        tasks
          .map(function (task) {
            return (
              '<article class="meetings-priority-card">' +
              '<span class="meetings-priority-dot" aria-hidden="true"></span>' +
              "<div>" +
              "<strong>" +
              escapeHtml(task.task || "") +
              "</strong>" +
              "<p>" +
              escapeHtml(task.owner || "") +
              "</p>" +
              "</div>" +
              "</article>"
            );
          })
          .join("") +
        "</div>";
      return;
    }

    priorityContent.innerHTML =
      '<p class="meetings-empty-copy">High-priority tasks will be isolated here after analysis.</p>';
  };

  var renderMeetingResult = function (payload) {
    var result = payload.result || null;
    var summary = result && Array.isArray(result.summary) ? result.summary : [];
    var tasks = result && Array.isArray(result.tasks) ? result.tasks : [];
    var highPriority =
      result && Array.isArray(result.high_priority_tasks)
        ? result.high_priority_tasks
        : [];

    if (transcriptInput && typeof payload.transcript_input === "string") {
      transcriptInput.value = payload.transcript_input;
    }

    setAlertMessage(payload.error_message || "");
    updateCount(summaryCount, summary.length ? summary.length + " points" : "");
    updateCount(tasksCount, tasks.length ? tasks.length + " tasks" : "");
    updateCount(
      priorityCount,
      highPriority.length ? highPriority.length + " urgent" : "",
    );

    renderSummary(summary);
    renderTasks(tasks);
    renderPriorityTasks(highPriority);

    if (payload.ok && result) {
      setStatusState("complete");
      return;
    }

    setStatusState("idle");
  };

  if (fileInput && fileLabel) {
    fileInput.addEventListener("change", function () {
      if (fileInput.files && fileInput.files.length) {
        fileLabel.textContent = fileInput.files[0].name;
        return;
      }

      fileLabel.textContent = "Supports `.txt` and `.mp3`";
    });
  }

  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var formData = new FormData(form);
      submitButton.disabled = true;
      submitButton.textContent = "Analyzing...";
      setAlertMessage("");
      setStatusState("processing");

      fetch(form.action || window.location.href, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Request failed with status " + response.status);
          }
          return response.json();
        })
        .then(function (payload) {
          renderMeetingResult(payload);
        })
        .catch(function () {
          setAlertMessage(
            "Meeting processing failed. Check the transcript format and AI configuration.",
          );
          setStatusState("idle");
        })
        .finally(function () {
          submitButton.disabled = false;
          submitButton.textContent = "Analyze Meeting";
        });
    });
  }

  activateTab(tabButtons[0].getAttribute("data-tab-target"));
});
