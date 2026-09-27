// Renders a catalogue screen as a live 24x80 terminal grid.
// Shared by the landing page, the clerk workspace and the dashboard.

import { composeScreen } from "/dashboard/lib.mjs";

export async function loadJson(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`${url} returned HTTP ${response.status}`);
  return response.json();
}

function cellClass(meta, character) {
  const classes = ["screen__cell"];
  if (!meta.elementId) return classes;
  const attributes = meta.attrb.split(",").map((token) => token.trim());
  if (!meta.protected) classes.push("screen__cell--input");
  else if (meta.role === "menuOption" || meta.role === "option") classes.push("screen__cell--option");
  else if (character.trim()) classes.push("screen__cell--text");
  if (attributes.includes("BRT")) classes.push("screen__cell--bright");
  if (meta.role === "error") classes.push("screen__cell--error");
  return classes;
}

/**
 * Render `screen` into `container` and return a handle for highlighting.
 * Cells are plain spans; the grid is announced as one image with a text label.
 */
export function renderScreen(container, screen) {
  const { rows, cellMeta } = composeScreen(screen);
  const cellsByElement = new Map();
  const fragment = document.createDocumentFragment();

  for (let row = 0; row < 24; row += 1) {
    for (let col = 0; col < 80; col += 1) {
      const character = rows[row][col];
      const meta = cellMeta[row][col];
      const cell = document.createElement("span");
      cell.className = cellClass(meta, character).join(" ");
      cell.textContent = character;
      if (meta.elementId) {
        cell.dataset.element = meta.elementId;
        if (!cellsByElement.has(meta.elementId)) cellsByElement.set(meta.elementId, []);
        cellsByElement.get(meta.elementId).push(cell);
      }
      fragment.appendChild(cell);
    }
  }

  container.classList.add("screen");
  container.setAttribute("role", "img");
  container.setAttribute(
    "aria-label",
    `${screen.mapName} reconstructed from source as a 24 row by 80 column screen: ${screen.title}`,
  );
  container.replaceChildren(fragment);

  const elements = new Map(screen.elements.map((element) => [element.elementId, element]));

  function mark(ids, className) {
    for (const cells of cellsByElement.values()) {
      for (const cell of cells) cell.classList.remove(className);
    }
    for (const id of ids) {
      for (const cell of cellsByElement.get(id) ?? []) cell.classList.add(className);
    }
  }

  return {
    screen,
    elements,
    inputs: screen.elements.filter((element) => element.role === "input" && !element.protected),
    elementIdForBms(bmsName) {
      return screen.elements.find((element) => element.bmsName === bmsName)?.elementId ?? null;
    },
    highlight(ids) { mark(ids, "screen__cell--active"); },
    lock(ids) { mark(ids, "screen__cell--locked"); },
    hover(ids) { mark(ids, "screen__cell--hover"); },
  };
}
