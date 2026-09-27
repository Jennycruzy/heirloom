import {
  summarizeCatalogue,
  composeScreen,
  taskStatusLabel,
  evidenceUrl,
  validateExpectedCounts,
} from "./lib.mjs";

const requiredIds = [
  "data-status",
  "screen-count",
  "task-count",
  "confirmed-count",
  "uncertain-count",
  "screen-select",
  "task-select",
  "screen-title",
  "terminal-grid",
  "task-details",
  "task-name",
  "task-status",
  "task-outcome",
  "task-operation",
  "task-legacy-status",
  "task-modern-status",
  "task-programs",
  "task-note",
  "task-evidence",
];

const elements = Object.fromEntries(
  requiredIds.map((id) => {
    const element = document.getElementById(id);
    if (!element) {
      throw new Error(`Missing required DOM element: #${id}`);
    }
    return [id, element];
  }),
);

let catalogue;

function replaceChildren(parent, children) {
  parent.replaceChildren(...children);
}

function createOption(value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  return option;
}

function renderCounts(summary) {
  elements["screen-count"].textContent = `${summary.screenCount} screens`;
  elements["task-count"].textContent = `${summary.taskCount} screen-defined actions`;
  elements["confirmed-count"].textContent = `${summary.confirmedTaskCount} map-and-program-confirmed tasks`;
  elements["uncertain-count"].textContent = `${summary.cannotDetermineCount} screen-only/cannot-determine actions`;
}

function renderScreen(screen) {
  elements["screen-title"].textContent = `${screen.transactionId} — ${screen.title} (${screen.mapName})`;
  const { rows, cellMeta } = composeScreen(screen);
  const cells = [];

  for (let rowIndex = 0; rowIndex < 24; rowIndex += 1) {
    for (let colIndex = 0; colIndex < 80; colIndex += 1) {
      const span = document.createElement("span");
      span.classList.add("cell");
      span.textContent = rows[rowIndex][colIndex];

      const metadata = cellMeta[rowIndex][colIndex];
      if (metadata.elementId) {
        span.classList.add(metadata.protected ? "cell--protected" : "cell--editable");
        if (metadata.role === "menuOption" || metadata.role === "option") {
          span.classList.add("cell--menu-option");
        }
        if (metadata.isCursor) {
          span.classList.add("cell--cursor");
        }
        if (metadata.role === "error") {
          span.classList.add("cell--error");
        }
      }

      cells.push(span);
    }
  }

  replaceChildren(elements["terminal-grid"], cells);
}

function setLabelledText(element, label, value) {
  element.textContent = `${label}: ${value}`;
}

function renderEvidence(task) {
  const introduction = document.createElement("p");
  introduction.textContent = "Source evidence:";
  const list = document.createElement("ul");

  for (const reference of task.sourceEvidence) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = evidenceUrl(reference);
    link.textContent = `${reference.file}, lines ${reference.lineStart}–${reference.lineEnd}`;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    item.appendChild(link);
    list.appendChild(item);
  }

  replaceChildren(elements["task-evidence"], [introduction, list]);
}

function renderTask(task) {
  elements["task-name"].textContent = task.name;
  elements["task-status"].textContent = taskStatusLabel(task);
  elements["task-status"].classList.toggle(
    "status--uncertain",
    task.legacySupportStatus === "screen-only-cannot-determine",
  );
  setLabelledText(elements["task-outcome"], "Outcome", task.outcome);
  setLabelledText(elements["task-operation"], "Operation", task.operation);
  setLabelledText(elements["task-legacy-status"], "Legacy support", task.legacySupportStatus);
  setLabelledText(elements["task-modern-status"], "Modern parity", task.modernParityStatus);
  setLabelledText(
    elements["task-programs"],
    "Business programs",
    task.businessPrograms.length > 0 ? task.businessPrograms.join(", ") : "None found",
  );
  setLabelledText(elements["task-note"], "Note", task.note || "No additional note.");
  renderEvidence(task);
}

function renderTasksForScreen(screen) {
  const tasks = catalogue.tasks.filter(
    (task) => task.transactionId === screen.transactionId,
  );
  const options = tasks.map((task) =>
    createOption(task.taskId, `${task.optionKey} — ${task.name}`),
  );
  replaceChildren(elements["task-select"], options);

  if (tasks.length > 0) {
    elements["task-select"].value = tasks[0].taskId;
    renderTask(tasks[0]);
  }
}

function renderSelectedScreen() {
  const screen = catalogue.screens.find(
    (candidate) => candidate.mapName === elements["screen-select"].value,
  );
  if (!screen) {
    throw new Error(`Unknown screen: ${elements["screen-select"].value}`);
  }
  renderScreen(screen);
  renderTasksForScreen(screen);
}

function populateScreens() {
  const options = catalogue.screens.map((screen) =>
    createOption(screen.mapName, `${screen.transactionId} — ${screen.title}`),
  );
  replaceChildren(elements["screen-select"], options);
  elements["screen-select"].value = catalogue.screens[0].mapName;
}

function showLoadError(error) {
  elements["data-status"].textContent = `Dashboard could not load: ${error.message}`;
  elements["data-status"].className = "status--error";
  for (const id of ["screen-count", "task-count", "confirmed-count", "uncertain-count"]) {
    elements[id].textContent = "—";
  }
  console.error(error);
}

async function initialize() {
  try {
    const response = await fetch("../catalogue/genapp.json");
    if (!response.ok) {
      throw new Error(`Catalogue request failed with HTTP ${response.status}`);
    }

    catalogue = await response.json();
    const summary = summarizeCatalogue(catalogue);
    renderCounts(summary);

    const mismatches = validateExpectedCounts(summary);
    if (mismatches.length > 0) {
      elements["data-status"].textContent = `Catalogue data error: ${mismatches.join("; ")}`;
      elements["data-status"].className = "status--error";
    } else {
      elements["data-status"].textContent = "Catalogue verified against the Stage 1 expectations.";
      elements["data-status"].className = "status--ok";
    }

    populateScreens();
    renderSelectedScreen();

    elements["screen-select"].addEventListener("change", () => {
      try {
        renderSelectedScreen();
      } catch (error) {
        showLoadError(error);
      }
    });

    elements["task-select"].addEventListener("change", () => {
      try {
        const task = catalogue.tasks.find(
          (candidate) => candidate.taskId === elements["task-select"].value,
        );
        if (!task) {
          throw new Error(`Unknown task: ${elements["task-select"].value}`);
        }
        renderTask(task);
      } catch (error) {
        showLoadError(error);
      }
    });
  } catch (error) {
    showLoadError(error);
  }
}

initialize();
