import {
  createWorkflow,
  enabledFields,
  markLoaded,
  requestIntent,
} from "/static/workflows.mjs";
import { evidenceUrl, LEGACY_PREFIX } from "/dashboard/lib.mjs";
import { loadJson, renderScreen } from "/assets/screen.mjs";

const ENTITIES = {
  customer: {
    label: "Customer",
    transactionId: "SSC1",
    mapName: "SSMAPC1",
    generated: "customer_number",
    immutable: "customer_number",
    optionField: "ENT1OPT",
    fields: [
      "customer_number", "first_name", "last_name", "date_of_birth", "house_name",
      "house_number", "postcode", "home_phone", "mobile_phone", "email",
    ],
  },
  motor: {
    label: "Motor policy",
    transactionId: "SSP1",
    mapName: "SSMAPP1",
    generated: "policy_number",
    immutable: "policy_number",
    optionField: "ENP1OPT",
    fields: [
      "policy_number", "customer_number", "issue_date", "expiry_date", "car_make",
      "car_model", "car_value", "registration", "car_colour", "engine_cc",
      "manufacture_date", "accident_count", "policy_premium",
    ],
  },
};

const RULES = {
  customer: {
    inquire: "Enter a customer number to retrieve the record.",
    add: "Enter the customer's details. The customer number is assigned by the system, as the legacy add program does.",
    "load-update": "Enter a customer number and retrieve the live record. The other fields unlock once it is loaded.",
    "submit-update": "Edit the loaded record, then save. The customer number stays fixed.",
  },
  motor: {
    inquire: "Enter the policy number and the customer who holds it. Both are needed to find the policy.",
    add: "Enter the holder's customer number and the policy details. The policy number is assigned by the system.",
    delete: "Enter both numbers. Only a policy held by that customer is deleted.",
    "load-update": "Enter both numbers and retrieve the live policy. The details unlock once it is loaded.",
    "submit-update": "Edit the loaded policy, then save. The policy number stays fixed and the update matches on both numbers.",
  },
};

const SUBMIT_LABELS = {
  inquire: "Inquire",
  add: "Add",
  delete: "Delete policy",
  "load-update": "Retrieve record",
  "submit-update": "Save changes",
};

function requireElement(selector) {
  const element = document.querySelector(selector);
  if (!element) throw new Error(`Missing required DOM element: ${selector}`);
  return element;
}

const status = requireElement("#app-status");
const traceScreen = requireElement("#trace-screen");
const traceMap = requireElement("#trace-map");
const traceBar = requireElement("#trace-bar");
const traceRule = requireElement("#trace-rule");
const requestLog = requireElement("#request-log");
const logCount = requireElement("#log-count");

const state = {};
for (const [entity, spec] of Object.entries(ENTITIES)) {
  const form = requireElement(`#${entity}-form`);
  const operation = form.querySelector(`input[name="${entity}-operation"]:checked`)?.value ?? "inquire";
  state[entity] = {
    ...spec,
    form,
    panel: requireElement(`#${entity}-workspace`),
    tab: requireElement(`#tab-${entity}`),
    submit: requireElement(`#${entity}-submit`),
    steps: requireElement(`#${entity}-steps`),
    rule: requireElement(`#${entity}-rule`),
    result: requireElement(`#${entity}-result`),
    workflow: createWorkflow(entity, operation),
    loaded: null,
  };
  for (const field of spec.fields) requireElement(`#${entity}-${field}`);
}

let activeEntity = "customer";
let evidence = { catalogue: null, mapping: null, findings: null };
let trace = null;
let requestCount = 0;

/* ---------- Status and request log ---------- */

function setStatus(message, kind = "info") {
  status.replaceChildren();
  status.className = "status";
  if (!message) return;
  status.classList.add(`status--${kind}`);
  const mark = document.createElement("span");
  mark.className = "status__mark mono";
  mark.textContent = kind === "error" ? "ERR" : kind === "success" ? "OK" : "i";
  mark.setAttribute("aria-hidden", "true");
  const text = document.createElement("span");
  text.textContent = message;
  status.append(mark, text);
}

function logRequest(method, url, statusCode, elapsed) {
  requestCount += 1;
  logCount.textContent = String(requestCount);
  requestLog.querySelector(".log__empty")?.remove();
  const item = document.createElement("li");
  item.className = `log__item ${statusCode >= 200 && statusCode < 300 ? "log__item--ok" : "log__item--error"}`;
  const parts = [
    ["log__method mono", method],
    ["log__url mono", decodeURIComponent(url)],
    ["log__status mono", statusCode === 0 ? "—" : String(statusCode)],
    ["log__time mono", `${elapsed} ms`],
  ];
  for (const [className, text] of parts) {
    const span = document.createElement("span");
    span.className = className;
    span.textContent = text;
    item.append(span);
  }
  requestLog.prepend(item);
  while (requestLog.children.length > 8) requestLog.lastElementChild.remove();
}

async function request(method, url, payload) {
  const options = { method, headers: { Accept: "application/json" } };
  if (payload !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(payload);
  }
  const started = performance.now();
  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    logRequest(method, url, 0, Math.round(performance.now() - started));
    throw new Error("The server could not be reached");
  }
  logRequest(method, url, response.status, Math.round(performance.now() - started));
  let body;
  try {
    body = await response.json();
  } catch {
    throw new Error(`Server returned HTTP ${response.status} without valid JSON`);
  }
  if (!response.ok) {
    const error = new Error(body.error || `Request failed with HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return body.data;
}

/* ---------- Form helpers ---------- */

function input(entity, field) {
  return requireElement(`#${entity}-${field}`);
}

function values(entity, fields) {
  return Object.fromEntries(fields.map((field) => [field, input(entity, field).value]));
}

function populate(entity, record) {
  for (const [field, value] of Object.entries(record)) {
    const element = document.querySelector(`#${entity}-${field}`);
    if (element) {
      element.value = value;
      updateCounter(element);
    }
  }
}

function requireValue(entity, field, label) {
  const value = input(entity, field).value.trim();
  if (!value) {
    input(entity, field).focus();
    throw new Error(`${label} is required`);
  }
  return value;
}

function motorUrl(policyNumber, customerNumber) {
  const query = new URLSearchParams({ customer_number: customerNumber });
  return `/api/motor-policies/${encodeURIComponent(policyNumber)}?${query}`;
}

function humanize(field) {
  const text = field.replaceAll("_", " ");
  return text === "engine cc" ? "engine CC" : text;
}

function renderResult(entity, record, previous = null) {
  const { result } = state[entity];
  const list = result.querySelector("dl");
  const nodes = [];
  for (const [field, value] of Object.entries(record)) {
    const cell = document.createElement("div");
    cell.className = "result__cell";
    const term = document.createElement("dt");
    term.textContent = humanize(field);
    const description = document.createElement("dd");
    description.textContent = value === "" ? "—" : value;
    if (value === "") description.classList.add("result__blank");
    if (previous && previous[field] !== value) {
      cell.classList.add("result__cell--changed");
      cell.title = `Was: ${previous[field] || "blank"}`;
    }
    cell.append(term, description);
    nodes.push(cell);
  }
  list.replaceChildren(...nodes);
  result.classList.add("result--filled");
}

function clearResult(entity) {
  const { result } = state[entity];
  result.querySelector("dl").replaceChildren();
  result.classList.remove("result--filled");
}

/* ---------- Field metadata ---------- */

function bmsNameFor(entity, field) {
  const spec = evidence.mapping?.[ENTITIES[entity].transactionId];
  if (!spec) return null;
  return Object.entries(spec.fields).find(([, modern]) => modern === field)?.[0] ?? null;
}

function updateCounter(element) {
  const meta = element.closest(".field")?.querySelector(".field__count");
  if (meta) meta.textContent = `${element.value.length}/${element.maxLength}`;
}

function decorateFields() {
  for (const entity of Object.keys(ENTITIES)) {
    for (const field of ENTITIES[entity].fields) {
      const element = input(entity, field);
      const meta = element.closest(".field").querySelector(".field__meta");
      const bms = bmsNameFor(entity, field);
      const name = document.createElement("span");
      name.className = "field__bms mono";
      name.textContent = bms ?? "";
      const badge = document.createElement("span");
      badge.className = "field__badge mono";
      const count = document.createElement("span");
      count.className = "field__count mono";
      meta.replaceChildren(name, badge, count);
      updateCounter(element);
      element.addEventListener("input", () => updateCounter(element));
    }
  }
}

/* ---------- Workflow ---------- */

function applyWorkflow(entity) {
  const current = state[entity];
  const { workflow, fields } = current;
  const intent = requestIntent(workflow);
  const active = new Set(enabledFields(workflow, fields));

  for (const field of fields) {
    const element = input(entity, field);
    const container = element.closest(".field");
    const inactive = !active.has(field);
    element.disabled = inactive;
    container.classList.toggle("field--inactive", inactive);
    let badge = "";
    let reason = "";
    if (inactive && workflow.operation === "add" && field === current.generated) {
      badge = "Assigned by system";
      reason = "system";
    } else if (inactive && intent === "submit-update" && field === current.immutable) {
      badge = "Record key · locked";
      reason = "locked";
    } else if (inactive) {
      badge = "Not used";
      reason = "unused";
    }
    container.dataset.reason = reason;
    const badgeNode = container.querySelector(".field__badge");
    if (badgeNode) badgeNode.textContent = badge;
  }

  if (workflow.operation === "add") {
    input(entity, current.generated).value = "";
    updateCounter(input(entity, current.generated));
  }

  current.submit.textContent = SUBMIT_LABELS[intent] ?? "Run task";
  current.submit.classList.toggle("button--danger", intent === "delete");
  current.rule.textContent = RULES[entity][intent] ?? "";

  const isUpdate = workflow.operation === "update";
  current.steps.hidden = !isUpdate;
  for (const item of current.steps.children) {
    const done = isUpdate && workflow.step === "edit" && item.dataset.step === "load";
    const now = isUpdate && item.dataset.step === workflow.step;
    item.classList.toggle("steps__item--done", done);
    item.classList.toggle("steps__item--current", now);
    if (now) item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
  }

  if (entity === activeEntity) updateTrace();
  syncHash();
}

function setOperation(entity, operation) {
  const current = state[entity];
  const radio = current.form.querySelector(`input[name="${entity}-operation"][value="${operation}"]`);
  if (!radio) return false;
  radio.checked = true;
  current.workflow = createWorkflow(entity, operation);
  current.loaded = null;
  applyWorkflow(entity);
  return true;
}

/* ---------- Legacy trace ---------- */

function catalogueTask(entity) {
  const { transactionId } = ENTITIES[entity];
  return evidence.catalogue?.tasks.find(
    (task) => task.transactionId === transactionId && task.operation === state[entity].workflow.operation,
  );
}

function relatedFindings(entity) {
  const { transactionId } = ENTITIES[entity];
  const operation = state[entity].workflow.operation;
  return (evidence.findings?.findings ?? []).filter(
    (finding) => finding.transactionId === transactionId && finding.task.toLowerCase().startsWith(operation),
  );
}

function link(text, href) {
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.textContent = text;
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  return anchor;
}

function renderTraceRule(entity) {
  const task = catalogueTask(entity);
  const nodes = [];
  if (task) {
    const heading = document.createElement("p");
    heading.className = "trace__task";
    heading.textContent = `${task.name} · ${task.presentationProgram} → ${task.businessPrograms.join(", ") || "none"}`;
    nodes.push(heading);
    const cites = document.createElement("ul");
    cites.className = "trace__cites";
    cites.setAttribute("role", "list");
    for (const reference of task.sourceEvidence) {
      const item = document.createElement("li");
      const name = reference.file.slice(LEGACY_PREFIX.length).split("/").pop();
      item.append(link(`${name}:${reference.lineStart}–${reference.lineEnd}`, evidenceUrl(reference)));
      cites.append(item);
    }
    nodes.push(cites);
  }
  for (const finding of relatedFindings(entity)) {
    const card = document.createElement("div");
    card.className = "trace__finding";
    const head = document.createElement("p");
    head.className = "trace__finding-head";
    const chip = document.createElement("span");
    chip.className = "chip chip--fixed";
    chip.textContent = `${finding.id} · repaired`;
    const title = document.createElement("strong");
    title.textContent = finding.title;
    head.append(chip, title);
    const body = document.createElement("p");
    body.textContent = finding.legacy;
    card.append(head, body);
    nodes.push(card);
  }
  traceRule.replaceChildren(...nodes);
}

function updateTrace() {
  if (!evidence.catalogue || !evidence.mapping) return;
  const entity = activeEntity;
  const spec = ENTITIES[entity];
  if (!trace || trace.screen.mapName !== spec.mapName) {
    const screen = evidence.catalogue.screens.find((candidate) => candidate.mapName === spec.mapName);
    if (!screen) return;
    trace = renderScreen(traceScreen, screen);
    traceMap.textContent = spec.mapName;
  }
  const current = state[entity];
  const active = enabledFields(current.workflow, current.fields);
  const ids = (fields) => fields
    .map((field) => bmsNameFor(entity, field))
    .filter(Boolean)
    .map((bms) => trace.elementIdForBms(bms))
    .filter(Boolean);
  const optionId = trace.elementIdForBms(spec.optionField);
  trace.highlight([...ids(active), ...(optionId ? [optionId] : [])]);
  trace.lock(current.workflow.operation === "add" ? ids([current.generated]) : []);

  const task = catalogueTask(entity);
  traceBar.textContent = task ? `Option ${task.optionKey} · ${task.name}` : spec.mapName;
  renderTraceRule(entity);
}

/* ---------- Entity tabs ---------- */

function selectEntity(entity, { focus = false } = {}) {
  activeEntity = entity;
  for (const [name, current] of Object.entries(state)) {
    const selected = name === entity;
    current.tab.setAttribute("aria-selected", String(selected));
    current.tab.tabIndex = selected ? 0 : -1;
    current.panel.hidden = !selected;
  }
  if (focus) state[entity].tab.focus();
  updateTrace();
  syncHash();
}

for (const current of Object.values(state)) {
  current.tab.addEventListener("click", () => selectEntity(current.tab.dataset.entity));
  current.tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const names = Object.keys(state);
    const index = names.indexOf(current.tab.dataset.entity);
    const next = event.key === "Home" ? 0
      : event.key === "End" ? names.length - 1
      : (index + (event.key === "ArrowRight" ? 1 : -1) + names.length) % names.length;
    selectEntity(names[next], { focus: true });
  });
}

/* ---------- Deep links ---------- */

let applyingHash = false;

function syncHash() {
  if (applyingHash) return;
  const current = state[activeEntity];
  const hash = `#${activeEntity}/${current.workflow.operation}`;
  if (location.hash !== hash) history.replaceState(null, "", hash);
}

function applyHash() {
  const [entity, operation, ...identifiers] = location.hash.slice(1).split("/").map(decodeURIComponent);
  if (!state[entity]) return null;
  applyingHash = true;
  try {
    selectEntity(entity);
    if (operation) setOperation(entity, operation);
    if (entity === "customer" && identifiers[0]) input("customer", "customer_number").value = identifiers[0];
    if (entity === "motor") {
      if (identifiers[0]) input("motor", "policy_number").value = identifiers[0];
      if (identifiers[1]) input("motor", "customer_number").value = identifiers[1];
    }
    for (const field of ENTITIES[entity].fields) updateCounter(input(entity, field));
  } finally {
    applyingHash = false;
  }
  return { entity, operation, identifiers };
}

/* ---------- Task handlers ---------- */

async function runCustomer() {
  const current = state.customer;
  const intent = requestIntent(current.workflow);
  const editable = current.fields.filter((field) => field !== "customer_number");

  if (intent === "add") {
    const record = await request("POST", "/api/customers", values("customer", editable));
    populate("customer", record);
    renderResult("customer", record);
    setStatus(`Customer ${record.customer_number} added. The number was assigned by the system.`, "success");
    return;
  }

  const identifier = requireValue("customer", "customer_number", "Customer number");
  const url = `/api/customers/${encodeURIComponent(identifier)}`;
  if (intent === "inquire" || intent === "load-update") {
    const record = await request("GET", url);
    populate("customer", record);
    renderResult("customer", record);
    if (intent === "load-update") {
      current.loaded = record;
      current.workflow = markLoaded(current.workflow);
      applyWorkflow("customer");
      input("customer", "first_name").focus();
      setStatus(`Customer ${identifier} loaded. Edit the fields, then save.`, "success");
    } else {
      setStatus(`Customer ${identifier} found.`, "success");
    }
    return;
  }

  const record = await request("PUT", url, values("customer", editable));
  populate("customer", record);
  renderResult("customer", record, current.loaded);
  current.loaded = record;
  setStatus(`Customer ${identifier} updated. Changed values are marked in the record.`, "success");
}

async function runMotor() {
  const current = state.motor;
  const intent = requestIntent(current.workflow);
  const editable = current.fields.filter((field) => field !== "policy_number");

  if (intent === "add") {
    requireValue("motor", "customer_number", "Customer number");
    const record = await request("POST", "/api/motor-policies", values("motor", editable));
    populate("motor", record);
    renderResult("motor", record);
    setStatus(`Motor policy ${record.policy_number} added for customer ${record.customer_number}. The number was assigned by the system.`, "success");
    return;
  }

  const policyNumber = requireValue("motor", "policy_number", "Policy number");
  const customerNumber = requireValue("motor", "customer_number", "Customer number");
  const url = motorUrl(policyNumber, customerNumber);

  if (intent === "inquire" || intent === "load-update") {
    const record = await request("GET", url);
    populate("motor", record);
    renderResult("motor", record);
    if (intent === "load-update") {
      current.loaded = record;
      current.workflow = markLoaded(current.workflow);
      applyWorkflow("motor");
      input("motor", "issue_date").focus();
      setStatus(`Policy ${policyNumber} for customer ${customerNumber} loaded. Edit the details, then save.`, "success");
    } else {
      setStatus(`Policy ${policyNumber} held by customer ${customerNumber} found.`, "success");
    }
    return;
  }

  if (intent === "submit-update") {
    const record = await request(
      "PUT",
      `/api/motor-policies/${encodeURIComponent(policyNumber)}`,
      values("motor", editable),
    );
    populate("motor", record);
    renderResult("motor", record, current.loaded);
    current.loaded = record;
    setStatus(`Policy ${policyNumber} updated. Changed values are marked in the record.`, "success");
    return;
  }

  const record = await request("DELETE", url);
  renderResult("motor", record);
  for (const field of current.fields) {
    input("motor", field).value = "";
    updateCounter(input("motor", field));
  }
  setStatus(`Policy ${policyNumber} deleted for customer ${customerNumber}. The record shown is what was removed.`, "success");
}

const RUNNERS = { customer: runCustomer, motor: runMotor };

for (const [entity, current] of Object.entries(state)) {
  current.form.addEventListener("change", (event) => {
    if (event.target.name !== `${entity}-operation`) return;
    current.workflow = createWorkflow(entity, event.target.value);
    current.loaded = null;
    applyWorkflow(entity);
    setStatus("");
  });

  current.form.addEventListener("submit", async (event) => {
    event.preventDefault();
    current.submit.disabled = true;
    current.form.setAttribute("aria-busy", "true");
    try {
      await RUNNERS[entity]();
    } catch (error) {
      const hint = error.status === 404 && entity === "motor"
        ? " A policy is found only together with the customer who holds it."
        : "";
      setStatus(`${ENTITIES[entity].label} task failed: ${error.message}.${hint}`, "error");
    } finally {
      current.submit.disabled = false;
      current.form.removeAttribute("aria-busy");
    }
  });

  current.form.addEventListener("reset", () => {
    setTimeout(() => {
      clearResult(entity);
      setStatus("");
      const operation = current.form.querySelector(`input[name="${entity}-operation"]:checked`)?.value ?? "inquire";
      current.workflow = createWorkflow(entity, operation);
      current.loaded = null;
      applyWorkflow(entity);
      for (const field of current.fields) updateCounter(input(entity, field));
    }, 0);
  });
}

for (const button of document.querySelectorAll(".sample")) {
  button.addEventListener("click", () => {
    const entity = button.dataset.sample;
    selectEntity(entity);
    if (state[entity].workflow.operation === "add") setOperation(entity, "inquire");
    else if (state[entity].workflow.operation === "update" && state[entity].workflow.step === "edit") {
      setOperation(entity, "update");
    }
    if (entity === "customer") input("customer", "customer_number").value = button.dataset.customer;
    else {
      input("motor", "policy_number").value = button.dataset.policy;
      input("motor", "customer_number").value = button.dataset.customer;
    }
    for (const field of ENTITIES[entity].fields) updateCounter(input(entity, field));
    state[entity].submit.focus();
  });
}

/* ---------- Boot ---------- */

// Render both forms without touching the URL, so a shared link is read intact.
applyingHash = true;
for (const entity of Object.keys(state)) applyWorkflow(entity);
applyingHash = false;
const deepLink = applyHash();
if (!deepLink) selectEntity("customer");
window.addEventListener("hashchange", applyHash);

setStatus("Ready. Try customer CUST000001, or policy POL001 held by customer CUST000001.");

const [catalogue, mapping, findings] = await Promise.allSettled([
  loadJson("/catalogue/genapp.json"),
  loadJson("/evidence/mapping.json"),
  loadJson("/evidence/findings.json"),
]);
evidence = {
  catalogue: catalogue.status === "fulfilled" ? catalogue.value : null,
  mapping: mapping.status === "fulfilled" ? mapping.value : null,
  findings: findings.status === "fulfilled" ? findings.value : null,
};
decorateFields();
if (evidence.catalogue && evidence.mapping) updateTrace();
else traceRule.textContent = "The legacy catalogue could not be loaded, so the trace is unavailable.";

// A shared inquiry link runs straight away: it only reads.
if (deepLink?.operation === "inquire" && deepLink.identifiers.length > 0) {
  state[deepLink.entity].form.requestSubmit();
}
