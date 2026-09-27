import { evidenceUrl, LEGACY_PREFIX, PROJECT_REPOSITORY } from "/dashboard/lib.mjs";
import { loadJson, renderScreen } from "/assets/screen.mjs";

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(options)) {
    if (value === undefined || value === null) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("data-") || key.startsWith("aria-") || key === "role" || key === "href" || key === "id" || key === "type" || key === "hidden") {
      if (value === true) node.setAttribute(key, "");
      else if (value !== false) node.setAttribute(key, value);
    } else node[key] = value;
  }
  for (const child of [].concat(children)) {
    if (child === null || child === undefined) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function linesLabel(ref) {
  return ref.lineStart === ref.lineEnd ? `${ref.lineStart}` : `${ref.lineStart}–${ref.lineEnd}`;
}

function citationLink(label, href) {
  return el("li", {}, el("a", { href, target: "_blank", rel: "noopener noreferrer", text: label }));
}

function legacyCitation(ref) {
  const name = ref.file.split("/").pop();
  return citationLink(
    `${name}:${linesLabel(ref)}`,
    evidenceUrl({ ...ref, file: `${LEGACY_PREFIX}${ref.file}` }),
  );
}

function firstPassCitation(ref, tag) {
  return citationLink(`${ref.file}:${linesLabel(ref)} @ ${tag}`, evidenceUrl(ref, tag));
}

function checkCitation(check) {
  const href = `${PROJECT_REPOSITORY}/blob/main/${check.file}`;
  return el("li", {}, [
    el("a", { href, target: "_blank", rel: "noopener noreferrer", class: "cite-check", text: check.name }),
  ]);
}

/* ---------- Hero screen ---------- */

function setupHero(catalogue, mapping) {
  const container = document.getElementById("hero-screen");
  const label = document.getElementById("hero-screen-label");
  const probeName = document.getElementById("probe-name");
  const probeDetail = document.getElementById("probe-detail");
  const buttons = [...document.querySelectorAll(".screen-switch__button")];
  const modernNames = {};
  for (const spec of Object.values(mapping)) Object.assign(modernNames, spec.fields);

  let handle;
  let index = 0;
  let timer;
  let pinned = false;

  function describe(element) {
    probeName.textContent = element.bmsName ?? element.elementId;
    const parts = [
      `Row ${element.row}, column ${element.col}`,
      `${element.length} character${element.length === 1 ? "" : "s"}`,
      element.protected ? "protected" : "clerk entry",
    ];
    if (element.numeric) parts.push("numeric");
    const modern = element.bmsName ? modernNames[element.bmsName] : null;
    probeDetail.replaceChildren(
      parts.join(" · "),
      modern ? el("span", {}, [" → modern field ", el("span", { class: "mono", text: modern })]) : "",
    );
  }

  function step() {
    if (!handle || handle.inputs.length === 0) return;
    const element = handle.inputs[index % handle.inputs.length];
    handle.highlight([element.elementId]);
    describe(element);
    index += 1;
  }

  function start() {
    clearInterval(timer);
    step();
    if (!reducedMotion) timer = setInterval(() => { if (!pinned) step(); }, 2200);
  }

  function show(mapName) {
    const screen = catalogue.screens.find((candidate) => candidate.mapName === mapName);
    if (!screen) return;
    handle = renderScreen(container, screen);
    label.textContent = `${screen.mapName} · ${screen.transactionId} · 24×80`;
    for (const button of buttons) button.setAttribute("aria-pressed", String(button.dataset.map === mapName));
    index = 0;
    start();
  }

  container.addEventListener("pointerover", (event) => {
    const id = event.target?.dataset?.element;
    if (!id || !handle) return;
    const element = handle.elements.get(id);
    if (!element || element.role === "separator") return;
    pinned = true;
    handle.highlight([id]);
    describe(element);
  });
  container.addEventListener("pointerleave", () => { pinned = false; });

  for (const button of buttons) button.addEventListener("click", () => show(button.dataset.map));
  show("SSMAPC1");
}

/* ---------- Ledger ---------- */

function setupLedger(findings) {
  const { baseline, repaired } = findings;
  const values = {
    "baseline.application": `${baseline.applicationChecksPassed}/${baseline.applicationChecksTotal}`,
    "baseline.parity": `${baseline.parityChecksPassed}/${baseline.parityChecksTotal}`,
    "baseline.gaps": `${baseline.workflowGaps} found`,
    "repaired.application": `${repaired.applicationChecksPassed}/${repaired.applicationChecksTotal}`,
    "repaired.parity": `${repaired.parityChecksPassed}/${repaired.parityChecksTotal}`,
    "repaired.gaps": `${repaired.workflowGapsOpen} open`,
    "repaired.review": repaired.finalReview,
  };
  for (const node of document.querySelectorAll("[data-ledger]")) {
    const value = values[node.dataset.ledger];
    if (value) node.textContent = value;
  }
}

/* ---------- Findings ---------- */

function findingItem(finding, tag, open) {
  const bodyId = `finding-${finding.id}-body`;
  const summary = el("button", {
    type: "button",
    class: "finding__summary",
    "aria-expanded": String(open),
    "aria-controls": bodyId,
  }, [
    el("span", { class: "finding__id", text: finding.id }),
    el("span", {}, [
      el("span", { class: "finding__title", text: finding.title }),
      el("span", { class: "finding__task", text: `${finding.transactionId} · ${finding.task}` }),
    ]),
    el("span", { class: "chip chip--fixed" }, [el("span", { class: "dot", "aria-hidden": "true" }), "Repaired"]),
    el("span", { class: "finding__toggle", "aria-hidden": "true", text: "+" }),
  ]);

  const body = el("div", { class: "finding__body", id: bodyId, hidden: !open }, [
    el("div", { class: "evidence-col evidence-col--legacy" }, [
      el("h4", {}, [el("span", { class: "dot", "aria-hidden": "true" }), "Legacy source"]),
      el("p", { text: finding.legacy }),
      el("ul", { class: "cites", role: "list" }, finding.legacyEvidence.map(legacyCitation)),
    ]),
    el("div", { class: "evidence-col evidence-col--gap" }, [
      el("h4", {}, [el("span", { class: "dot", "aria-hidden": "true" }), "First pass"]),
      el("p", { text: finding.firstPass }),
      el("ul", { class: "cites", role: "list" }, finding.firstPassEvidence.map((ref) => firstPassCitation(ref, tag))),
    ]),
    el("div", { class: "evidence-col evidence-col--fixed" }, [
      el("h4", {}, [el("span", { class: "dot", "aria-hidden": "true" }), "Repair · fails before, passes after"]),
      el("p", { text: finding.repair }),
      el("ul", { class: "cites", role: "list" }, finding.regressionChecks.map(checkCitation)),
    ]),
  ]);

  summary.addEventListener("click", () => {
    const expanded = summary.getAttribute("aria-expanded") === "true";
    summary.setAttribute("aria-expanded", String(!expanded));
    body.hidden = expanded;
  });

  return el("li", { class: "finding", "data-transaction": finding.transactionId }, [summary, body]);
}

function setupFindings(findings) {
  const list = document.getElementById("findings-list");
  const tag = findings.source.firstPassRef;
  list.replaceChildren(...findings.findings.map((finding, position) => findingItem(finding, tag, position === 0)));

  const counts = { all: findings.findings.length };
  for (const finding of findings.findings) counts[finding.transactionId] = (counts[finding.transactionId] ?? 0) + 1;
  for (const node of document.querySelectorAll("[data-count]")) node.textContent = counts[node.dataset.count] ?? 0;

  const filters = [...document.querySelectorAll(".filter")];
  for (const filter of filters) {
    filter.addEventListener("click", () => {
      const value = filter.dataset.filter;
      for (const other of filters) other.setAttribute("aria-pressed", String(other === filter));
      for (const item of list.children) item.hidden = value !== "all" && item.dataset.transaction !== value;
    });
  }
}

function setupUncertain(findings) {
  const list = document.getElementById("uncertain-list");
  for (const item of findings.uncertain) {
    list.append(el("li", { class: "boundary__item" }, [
      el("span", { class: "chip chip--unsure", text: "Cannot determine" }),
      el("h3", { text: item.title }),
      el("p", { text: item.detail }),
      item.legacyEvidence ? el("ul", { class: "cites", role: "list" }, item.legacyEvidence.map(legacyCitation)) : null,
    ]));
  }
}

/* ---------- Verification ---------- */

function formatTime(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${date.toLocaleString("en-GB", {
    day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC",
  })} UTC`;
}

function setupVerification(report) {
  const line = document.getElementById("verified-line");
  const meta = document.getElementById("verification-meta");
  const suites = document.getElementById("suites");
  const ok = report.status === "pass";
  const commit = report.sourceCommit ? report.sourceCommit.slice(0, 7) : "unknown";

  line.dataset.state = ok ? "pass" : "fail";
  line.replaceChildren(
    el("span", { class: `dot${ok ? " dot--live" : ""}`, "aria-hidden": "true" }),
    el("span", {}, [
      `${report.summary.passed}/${report.summary.total} checks ${ok ? "passing" : "— some failing"} across ${report.suites.length} suites · `,
      el("a", { href: "#verification", text: `verified ${formatTime(report.generatedAt)}` }),
    ]),
  );

  meta.replaceChildren(
    `Last run ${formatTime(report.generatedAt)} against commit `,
    el("a", { href: `${PROJECT_REPOSITORY}/commit/${report.sourceCommit}`, text: commit }),
    report.workingTreeClean ? " (clean working tree)." : " with uncommitted changes in the working tree.",
    " Raw record: ",
    el("a", { href: "/evidence/verification.json", text: "verification.json" }),
  );

  suites.replaceChildren(
    ...report.suites.map((item) => el("div", { class: "suite" }, [
      el("span", {
        class: `suite__status chip ${item.status === "pass" ? "chip--fixed" : "chip--gap"}`,
        text: item.status === "pass" ? "Pass" : "Fail",
      }),
      el("span", { class: "suite__name", text: item.name[0].toUpperCase() + item.name.slice(1) }),
      el("span", { class: "suite__count", text: `${item.passed}/${item.total}` }),
      el("span", { class: "suite__desc", text: item.description }),
    ])),
    el("div", { class: "suite__total" }, [
      el("span", { text: "All suites" }),
      el("strong", { class: "num", text: `${report.summary.passed}/${report.summary.total}` }),
    ]),
  );
}

function verificationUnavailable(error) {
  const line = document.getElementById("verified-line");
  line.replaceChildren(
    el("span", { class: "dot", "aria-hidden": "true" }),
    el("span", { text: "No published verification record. Run python3 scripts/verify.py." }),
  );
  document.getElementById("suites").replaceChildren(
    el("div", { class: "suite suite--placeholder", text: `Verification record unavailable: ${error.message}` }),
  );
}

/* ---------- Boot ---------- */

const [catalogue, mapping, findings, verification] = await Promise.allSettled([
  loadJson("/catalogue/genapp.json"),
  loadJson("/evidence/mapping.json"),
  loadJson("/evidence/findings.json"),
  loadJson("/evidence/verification.json"),
]);

if (catalogue.status === "fulfilled" && mapping.status === "fulfilled") {
  setupHero(catalogue.value, mapping.value);
} else {
  document.getElementById("probe-detail").textContent = "The legacy catalogue could not be loaded.";
}

if (findings.status === "fulfilled") {
  setupLedger(findings.value);
  setupFindings(findings.value);
  setupUncertain(findings.value);
} else {
  document.getElementById("findings-list").replaceChildren(
    el("li", { class: "finding finding--placeholder", text: `Findings could not be loaded: ${findings.reason.message}` }),
  );
}

if (verification.status === "fulfilled") setupVerification(verification.value);
else verificationUnavailable(verification.reason);
