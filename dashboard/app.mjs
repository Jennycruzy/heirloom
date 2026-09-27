import {
  summarizeCatalogue,
  taskStatusLabel,
  evidenceUrl,
  validateExpectedCounts,
  LEGACY_PREFIX,
} from "./lib.mjs";
import { loadJson, renderScreen } from "/assets/screen.mjs";

function requireElement(id) {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing required DOM element: #${id}`);
  return element;
}

const elements = Object.fromEntries(
  [
    "data-status", "provenance-commit", "screen-count", "task-count", "confirmed-count",
    "uncertain-count", "screen-tabs", "screen-title", "terminal-grid", "inspector",
    "inspector-hint", "scope-chip", "task-list", "task-details",
  ].map((id) => [id, requireElement(id)]),
);

let catalogue;
let scope = {};
let handle = null;
let selectedElement = null;
let activeScreen = null;

function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(options)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of [].concat(children)) {
    if (child === null || child === undefined) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function shortTitle(screen) {
  return screen.title.replace(/^General Insurance\s+/i, "").replace(/\s+Menu$/i, "");
}

function sourceLink(reference) {
  const name = reference.file.slice(LEGACY_PREFIX.length);
  const lines = reference.lineStart === reference.lineEnd
    ? `${reference.lineStart}` : `${reference.lineStart}–${reference.lineEnd}`;
  return el("a", {
    href: evidenceUrl(reference), target: "_blank", rel: "noopener noreferrer",
    text: `${name}:${lines}`,
  });
}

/* ---------- Counts ---------- */

function renderCounts(summary) {
  elements["screen-count"].textContent = summary.screenCount;
  elements["task-count"].textContent = summary.taskCount;
  elements["confirmed-count"].textContent = summary.confirmedTaskCount;
  elements["uncertain-count"].textContent = summary.cannotDetermineCount;
}

/* ---------- Inspector ---------- */

function describeRole(element) {
  if (!element.protected) return element.role === "option" ? "Option entry" : "Clerk entry";
  return {
    title: "Title", label: "Label", menuOption: "Menu option", hint: "Hint",
    separator: "Field stopper", error: "Error message line",
  }[element.role] ?? element.role;
}

function renderInspector(element) {
  const grid = elements.inspector;
  if (!element) {
    grid.replaceChildren();
    elements["inspector-hint"].textContent = "Hover or click a field on the screen.";
    return;
  }
  elements["inspector-hint"].textContent = selectedElement === element.elementId
    ? "Pinned. Click the field again to release it."
    : "Click to pin this field.";
  const initial = element.initialValue && element.initialValue.trim()
    ? `“${element.initialValue.trimEnd()}”` : "—";
  const rows = [
    ["BMS name", element.bmsName ?? "unnamed literal", true],
    ["Role", describeRole(element)],
    ["Position", `row ${element.row}, column ${element.col}`],
    ["Length", `${element.length} character${element.length === 1 ? "" : "s"}`],
    ["Attributes", element.attrb || "—", true],
    ["Numeric", element.numeric ? "yes" : "no"],
    ["Initial value", initial, true],
  ];
  const nodes = rows.map(([term, value, mono]) => el("div", {}, [
    el("dt", { text: term }),
    el("dd", { class: mono ? "mono" : null, text: value }),
  ]));
  if (element.sourceRef) {
    nodes.push(el("div", { class: "inspector__source" }, [
      el("dt", { text: "Source" }),
      el("dd", {}, sourceLink(element.sourceRef)),
    ]));
  }
  grid.replaceChildren(...nodes);
}

function elementFromEvent(event) {
  const id = event.target?.dataset?.element;
  if (!id || !handle) return null;
  const element = handle.elements.get(id);
  return element && element.role !== "separator" ? element : null;
}

function wireInspector() {
  const grid = elements["terminal-grid"];
  grid.addEventListener("pointerover", (event) => {
    const element = elementFromEvent(event);
    if (!element) return;
    handle.hover([element.elementId]);
    if (!selectedElement) renderInspector(element);
  });
  grid.addEventListener("pointerleave", () => {
    handle?.hover([]);
    if (!selectedElement) renderInspector(null);
  });
  grid.addEventListener("click", (event) => {
    const element = elementFromEvent(event);
    if (!element) return;
    selectedElement = selectedElement === element.elementId ? null : element.elementId;
    handle.highlight(selectedElement ? [selectedElement] : []);
    renderInspector(element);
  });
}

/* ---------- Tasks ---------- */

function modernLink(task) {
  const entity = scope[task.transactionId];
  if (!entity || task.legacySupportStatus !== "map-and-program-confirmed") return null;
  return `/app/#${entity}/${task.operation}`;
}

function renderTask(task) {
  for (const button of elements["task-list"].querySelectorAll("button")) {
    button.setAttribute("aria-pressed", String(button.dataset.task === task.taskId));
  }
  const uncertain = task.legacySupportStatus === "screen-only-cannot-determine";
  const link = modernLink(task);
  const facts = [
    ["Outcome", task.outcome],
    ["Operation", task.operation],
    ["Presentation program", task.presentationProgram ?? "None found"],
    ["Business programs", task.businessPrograms.length ? task.businessPrograms.join(", ") : "None found"],
    ["Modern application", link ? "Implemented in the clerk workspace" : "Outside the modernization scope"],
  ];
  const detail = [
    el("p", { class: "task-detail__key mono", text: `Option ${task.optionKey} · ${task.taskId}` }),
    el("h3", { class: "task-detail__name", text: task.name }),
    el("p", { class: `task-detail__status ${uncertain ? "task-detail__status--unsure" : ""}`, text: taskStatusLabel(task) }),
    el("dl", { class: "task-detail__facts" }, facts.map(([term, value]) => el("div", {}, [
      el("dt", { text: term }), el("dd", { text: value }),
    ]))),
    task.note ? el("p", { class: "task-detail__note", text: task.note }) : null,
    el("h4", { class: "task-detail__subhead", text: "Source evidence" }),
    el("ul", { class: "task-detail__cites", role: "list" }, task.sourceEvidence.map((reference) => el("li", {}, [
      sourceLink(reference),
      reference.excerpt ? el("code", { text: reference.excerpt.trim() }) : null,
    ]))),
    link ? el("a", { class: "button task-detail__open", href: link }, ["Open this task in the workspace ", el("span", { class: "button__arrow", "aria-hidden": "true", text: "→" })]) : null,
  ];
  elements["task-details"].replaceChildren(...detail.filter(Boolean));
  syncHash(task.taskId);
}

function renderTasks(screen, preferredTaskId) {
  const tasks = catalogue.tasks.filter((task) => task.transactionId === screen.transactionId);
  elements["task-list"].replaceChildren(...tasks.map((task) => {
    const uncertain = task.legacySupportStatus === "screen-only-cannot-determine";
    const button = el("button", { type: "button", class: "task-item", "data-task": task.taskId, "aria-pressed": "false" }, [
      el("span", { class: "task-item__key mono", text: task.optionKey }),
      el("span", { class: "task-item__name", text: task.name }),
      el("span", { class: `chip ${uncertain ? "chip--unsure" : "chip--fixed"}`, text: uncertain ? "Cannot determine" : "Confirmed" }),
    ]);
    button.addEventListener("click", () => renderTask(task));
    return el("li", {}, button);
  }));
  const inScope = Boolean(scope[screen.transactionId]);
  elements["scope-chip"].textContent = inScope ? "Modernized" : "Not modernized";
  elements["scope-chip"].className = `chip ${inScope ? "chip--ink" : ""}`;
  const first = tasks.find((task) => task.taskId === preferredTaskId) ?? tasks[0];
  if (first) renderTask(first);
  else elements["task-details"].replaceChildren(el("p", { class: "muted", text: "No actions are defined on this screen." }));
}

/* ---------- Screens ---------- */

function selectScreen(mapName, { taskId, focus = false } = {}) {
  const screen = catalogue.screens.find((candidate) => candidate.mapName === mapName) ?? catalogue.screens[0];
  activeScreen = screen;
  for (const tab of elements["screen-tabs"].children) {
    const selected = tab.dataset.map === screen.mapName;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    if (selected && focus) tab.focus();
  }
  elements["screen-title"].textContent = `${screen.mapName} · ${screen.transactionId} · ${screen.title}`;
  handle = renderScreen(elements["terminal-grid"], screen);
  selectedElement = null;
  renderInspector(null);
  renderTasks(screen, taskId);
}

function renderTabs() {
  const tabs = catalogue.screens.map((screen) => {
    const tab = el("button", {
      type: "button", role: "tab", class: "screen-tab", "data-map": screen.mapName,
      "aria-controls": "terminal-grid", "aria-selected": "false",
    }, [
      el("span", { class: "screen-tab__code mono", text: screen.transactionId }),
      el("span", { class: "screen-tab__name", text: shortTitle(screen) }),
      scope[screen.transactionId] ? el("span", { class: "screen-tab__flag", title: "Modernized", "aria-label": "modernized" }) : null,
    ]);
    tab.addEventListener("click", () => selectScreen(screen.mapName));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const names = catalogue.screens.map((candidate) => candidate.mapName);
      const index = names.indexOf(screen.mapName);
      const next = event.key === "Home" ? 0
        : event.key === "End" ? names.length - 1
        : (index + (event.key === "ArrowRight" ? 1 : -1) + names.length) % names.length;
      selectScreen(names[next], { focus: true });
    });
    return tab;
  });
  elements["screen-tabs"].replaceChildren(...tabs);
}

function syncHash(taskId) {
  if (!activeScreen) return;
  const hash = `#${activeScreen.mapName}/${taskId}`;
  if (location.hash !== hash) history.replaceState(null, "", hash);
}

function showLoadError(error) {
  elements["data-status"].textContent = `The dashboard could not load: ${error.message}`;
  elements["data-status"].className = "data-status data-status--error";
  console.error(error);
}

async function initialize() {
  try {
    const [loaded, mapping] = await Promise.all([
      loadJson("/catalogue/genapp.json"),
      loadJson("/evidence/mapping.json").catch(() => ({})),
    ]);
    catalogue = loaded;
    scope = Object.fromEntries(Object.entries(mapping).map(([transaction, spec]) => [transaction, spec.entity]));

    const summary = summarizeCatalogue(catalogue);
    renderCounts(summary);
    const mismatches = validateExpectedCounts(summary);
    if (mismatches.length > 0) {
      elements["data-status"].textContent = `Catalogue data error: ${mismatches.join("; ")}`;
      elements["data-status"].className = "data-status data-status--error";
    } else {
      elements["data-status"].textContent = "Catalogue loaded and checked: 6 screens, 20 actions, 18 confirmed by program, 2 recorded as cannot determine.";
      elements["data-status"].className = "data-status data-status--ok";
    }
    if (catalogue.provenance?.commit) {
      elements["provenance-commit"].textContent = `GenApp ${catalogue.provenance.commit.slice(0, 7)}`;
    }

    renderTabs();
    wireInspector();
    const [mapName, taskId] = location.hash.slice(1).split("/");
    selectScreen(mapName || catalogue.screens[0].mapName, { taskId });
  } catch (error) {
    showLoadError(error);
  }
}

initialize();
