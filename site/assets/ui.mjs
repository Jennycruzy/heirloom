// Small DOM and citation helpers shared by the site pages.

import { evidenceUrl, LEGACY_PREFIX, PROJECT_REPOSITORY } from "/dashboard/lib.mjs";

export { PROJECT_REPOSITORY };

const ATTRIBUTES = new Set(["href", "id", "type", "role", "target", "rel", "title", "hidden"]);

export function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(options)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (ATTRIBUTES.has(key) || key.startsWith("data-") || key.startsWith("aria-")) {
      node.setAttribute(key, value === true ? "" : value);
    } else node[key] = value;
  }
  for (const child of [].concat(children)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function linesLabel(ref) {
  return ref.lineStart === ref.lineEnd ? `${ref.lineStart}` : `${ref.lineStart}–${ref.lineEnd}`;
}

function citationItem(label, href, className) {
  return el("li", {}, el("a", { href, target: "_blank", rel: "noopener noreferrer", class: className, text: label }));
}

/** A citation of the pinned GenApp source; `ref.file` is relative to the submodule. */
export function legacyCitation(ref) {
  const name = ref.file.split("/").pop();
  return citationItem(`${name}:${linesLabel(ref)}`, evidenceUrl({ ...ref, file: `${LEGACY_PREFIX}${ref.file}` }));
}

/** A citation of this repository at a given ref, such as the first-pass tag. */
export function projectCitation(ref, gitRef) {
  return citationItem(`${ref.file}:${linesLabel(ref)} @ ${gitRef}`, evidenceUrl(ref, gitRef));
}

export function checkCitation(check) {
  return citationItem(check.name, `${PROJECT_REPOSITORY}/blob/main/${check.file}`, "cite-check");
}

export function formatTime(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${date.toLocaleString("en-GB", {
    day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC",
  })} UTC`;
}
