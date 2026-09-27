import { loadJson, renderScreen } from "/assets/screen.mjs";
import { el, formatTime } from "/assets/ui.mjs";

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---------- Live legacy screen ---------- */

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

  function show(mapName) {
    const screen = catalogue.screens.find((candidate) => candidate.mapName === mapName);
    if (!screen) return;
    handle = renderScreen(container, screen);
    label.textContent = `${screen.mapName} · ${screen.transactionId} · 24×80`;
    for (const button of buttons) button.setAttribute("aria-pressed", String(button.dataset.map === mapName));
    index = 0;
    clearInterval(timer);
    step();
    if (!reducedMotion) timer = setInterval(() => { if (!pinned) step(); }, 2200);
  }

  container.addEventListener("pointerover", (event) => {
    const id = event.target?.dataset?.element;
    const element = id && handle?.elements.get(id);
    if (!element || element.role === "separator") return;
    pinned = true;
    handle.highlight([id]);
    describe(element);
  });
  container.addEventListener("pointerleave", () => { pinned = false; });

  for (const button of buttons) button.addEventListener("click", () => show(button.dataset.map));
  show("SSMAPC1");
}

/* ---------- Numbers from the published evidence ---------- */

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
    if (values[node.dataset.ledger]) node.textContent = values[node.dataset.ledger];
  }
  const stat = document.querySelector('[data-stat="findings"]');
  if (stat) stat.textContent = findings.findings.length;
}

function setupVerified(report) {
  const line = document.getElementById("verified-line");
  const ok = report.status === "pass";
  line.dataset.state = ok ? "pass" : "fail";
  line.replaceChildren(
    el("span", { class: `dot${ok ? " dot--live" : ""}`, "aria-hidden": "true" }),
    el("span", {}, [
      `${report.summary.passed}/${report.summary.total} checks ${ok ? "passing" : "— some failing"} · `,
      el("a", { href: "/verification/", text: `verified ${formatTime(report.generatedAt)}` }),
    ]),
  );
  const stat = document.querySelector('[data-stat="verification"]');
  if (stat) stat.replaceChildren(`${report.summary.passed}`, el("small", { text: `/${report.summary.total}` }));
}

const [catalogue, mapping, findings, verification] = await Promise.allSettled([
  loadJson("/catalogue/genapp.json"),
  loadJson("/evidence/mapping.json"),
  loadJson("/evidence/findings.json"),
  loadJson("/evidence/verification.json"),
]);

if (catalogue.status === "fulfilled" && mapping.status === "fulfilled") setupHero(catalogue.value, mapping.value);
else document.getElementById("probe-detail").textContent = "The legacy catalogue could not be loaded.";

if (findings.status === "fulfilled") setupLedger(findings.value);

if (verification.status === "fulfilled") setupVerified(verification.value);
else {
  document.getElementById("verified-line").replaceChildren(
    el("span", { class: "dot", "aria-hidden": "true" }),
    el("span", { text: "No published verification record. Run python3 scripts/verify.py." }),
  );
}
