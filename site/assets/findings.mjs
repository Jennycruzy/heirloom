import { loadJson } from "/assets/screen.mjs";
import { el, legacyCitation, projectCitation, checkCitation } from "/assets/ui.mjs";

function findingItem(finding, tag, open) {
  const bodyId = `finding-${finding.id}-body`;
  const summary = el("button", {
    type: "button", class: "finding__summary", "aria-expanded": String(open), "aria-controls": bodyId,
  }, [
    el("span", { class: "finding__id", text: finding.id }),
    el("span", {}, [
      el("span", { class: "finding__title", text: finding.title }),
      el("span", { class: "finding__task", text: `${finding.transactionId} · ${finding.task}` }),
    ]),
    el("span", { class: "chip chip--fixed" }, [el("span", { class: "dot", "aria-hidden": "true" }), "Repaired"]),
    el("span", { class: "finding__toggle", "aria-hidden": "true" }),
  ]);

  const column = (kind, heading, text, citations) => el("div", { class: `evidence-col evidence-col--${kind}` }, [
    el("h4", {}, [el("span", { class: "dot", "aria-hidden": "true" }), heading]),
    el("p", { text }),
    el("ul", { class: "cites", role: "list" }, citations),
  ]);

  const body = el("div", { class: "finding__body", id: bodyId, hidden: !open }, [
    column("legacy", "Legacy source", finding.legacy, finding.legacyEvidence.map(legacyCitation)),
    column("gap", "First pass", finding.firstPass, finding.firstPassEvidence.map((ref) => projectCitation(ref, tag))),
    column("fixed", "Repair · fails before, passes after", finding.repair, finding.regressionChecks.map(checkCitation)),
  ]);

  summary.addEventListener("click", () => {
    const expanded = summary.getAttribute("aria-expanded") === "true";
    summary.setAttribute("aria-expanded", String(!expanded));
    body.hidden = expanded;
  });

  return el("li", { class: "finding", id: finding.id, "data-transaction": finding.transactionId }, [summary, body]);
}

function setupFindings(findings) {
  const list = document.getElementById("findings-list");
  const tag = findings.source.firstPassRef;
  const requested = location.hash.slice(1);
  const openId = findings.findings.some((finding) => finding.id === requested) ? requested : findings.findings[0].id;
  list.replaceChildren(...findings.findings.map((finding) => findingItem(finding, tag, finding.id === openId)));
  if (requested === openId) document.getElementById(openId)?.scrollIntoView({ block: "start" });

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

try {
  const findings = await loadJson("/evidence/findings.json");
  setupFindings(findings);
  setupUncertain(findings);
} catch (error) {
  document.getElementById("findings-list").replaceChildren(
    el("li", { class: "finding finding--placeholder", text: `Findings could not be loaded: ${error.message}` }),
  );
}
