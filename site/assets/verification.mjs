import { loadJson } from "/assets/screen.mjs";
import { el, formatTime, PROJECT_REPOSITORY } from "/assets/ui.mjs";

function capitalize(text) {
  return text[0].toUpperCase() + text.slice(1);
}

function render(report) {
  const ok = report.status === "pass";
  const total = document.getElementById("verification-total");
  total.classList.toggle("verification__total--fail", !ok);
  total.querySelector(".verification__total-value").textContent = `${report.summary.passed}/${report.summary.total}`;
  total.querySelector(".verification__total-label").textContent = ok ? "All checks passing" : "Some checks failing";

  const commit = report.sourceCommit ? report.sourceCommit.slice(0, 7) : "unknown";
  document.getElementById("verification-meta").replaceChildren(
    `Last run ${formatTime(report.generatedAt)} against commit `,
    el("a", { href: `${PROJECT_REPOSITORY}/commit/${report.sourceCommit}`, text: commit }),
    report.workingTreeClean ? " with a clean working tree. " : " with uncommitted changes in the working tree. ",
    "Raw record: ",
    el("a", { href: "/evidence/verification.json", text: "verification.json" }),
  );

  document.getElementById("suites").replaceChildren(...report.suites.map((suite) => el("div", { class: "suite" }, [
    el("span", {
      class: `suite__status chip ${suite.status === "pass" ? "chip--fixed" : "chip--gap"}`,
      text: suite.status === "pass" ? "Pass" : "Fail",
    }),
    el("span", { class: "suite__name", text: capitalize(suite.name) }),
    el("span", { class: "suite__count", text: `${suite.passed}/${suite.total}` }),
    el("span", { class: "suite__desc", text: suite.description }),
    el("code", { class: "suite__command", text: suite.command }),
  ])));
}

try {
  render(await loadJson("/evidence/verification.json"));
} catch (error) {
  document.getElementById("suites").replaceChildren(
    el("div", { class: "suite suite--placeholder", text: `Verification record unavailable: ${error.message}. Run python3 scripts/verify.py.` }),
  );
}
