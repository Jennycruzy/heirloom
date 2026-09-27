export function summarizeCatalogue(catalogue) {
  if (!catalogue.screens || !Array.isArray(catalogue.screens)) {
    throw new Error('Catalogue missing screens array');
  }
  if (!catalogue.tasks || !Array.isArray(catalogue.tasks)) {
    throw new Error('Catalogue missing tasks array');
  }

  const screenCount = catalogue.screens.length;
  const taskCount = catalogue.tasks.length;
  const confirmedTaskCount = catalogue.tasks.filter(
    task => task.legacySupportStatus === 'map-and-program-confirmed'
  ).length;
  const cannotDetermineCount = catalogue.tasks.filter(
    task => task.legacySupportStatus === 'screen-only-cannot-determine'
  ).length;

  return { screenCount, taskCount, confirmedTaskCount, cannotDetermineCount };
}

export function composeScreen(screen) {
  if (!screen || typeof screen !== 'object' || !Array.isArray(screen.elements)) {
    throw new Error('Invalid screen format');
  }

  const elements = [...screen.elements].sort((a, b) => a.sourceOrder - b.sourceOrder);
  const rows = Array.from({ length: 24 }, () => Array(80).fill(' '));
  const cellMeta = Array.from({ length: 24 }, () =>
    Array.from({ length: 80 }, () => ({}))
  );

  for (const element of elements) {
    if (
      !element ||
      typeof element !== 'object' ||
      !Number.isInteger(element.sourceOrder) ||
      !Number.isInteger(element.row) ||
      !Number.isInteger(element.col) ||
      !Number.isInteger(element.length) ||
      element.row < 1 ||
      element.row > 24 ||
      element.col < 1 ||
      element.col > 80 ||
      element.length < 1 ||
      element.col + element.length - 1 > 80 ||
      typeof element.elementId !== 'string' ||
      element.elementId.trim() === ''
    ) {
      throw new Error(`Invalid element: ${JSON.stringify(element)}`);
    }

    const attrTokens = String(element.attrb ?? '')
      .split(',')
      .map(token => token.trim())
      .filter(Boolean);
    const isCursor = attrTokens.includes('IC');
    const content = (typeof element.initialValue === 'string' ? element.initialValue : '')
      .padEnd(element.length, ' ')
      .slice(0, element.length);

    for (let offset = 0; offset < element.length; offset += 1) {
      const row = element.row - 1;
      const col = element.col - 1 + offset;
      rows[row][col] = content[offset] || ' ';
      cellMeta[row][col] = {
        elementId: element.elementId,
        role: element.role,
        protected: Boolean(element.protected),
        attrb: String(element.attrb ?? ''),
        isCursor
      };
    }
  }

  return { rows: rows.map(row => row.join('')), cellMeta };
}

export function taskStatusLabel(task) {
  if (task.legacySupportStatus === 'screen-only-cannot-determine') {
    return 'Cannot determine — the screen defines this action, but no presentation program was found.';
  }
  return 'Confirmed in the legacy screen and presentation program.';
}

export const LEGACY_PREFIX = 'legacy/cics-genapp/';
export const LEGACY_REPOSITORY = 'https://github.com/cicsdev/cics-genapp';
export const LEGACY_COMMIT = 'f6f3f4b2580d31b7d8dcc31ce3e3676f4cceaaaa';
export const PROJECT_REPOSITORY = 'https://github.com/Jennycruzy/heirloom';

function encodePath(path) {
  return path.split('/').map(encodeURIComponent).join('/');
}

// Files inside the pinned submodule are not browsable under this repository's
// URL on GitHub, so legacy citations link to the upstream file at the pinned
// commit. Everything else links to this repository at the given ref.
export function evidenceUrl(ref, projectRef = 'main') {
  if (
    !ref ||
    Array.isArray(ref) ||
    typeof ref !== 'object' ||
    typeof ref.file !== 'string' ||
    ref.file.trim() === '' ||
    !Number.isInteger(ref.lineStart) ||
    !Number.isInteger(ref.lineEnd) ||
    ref.lineStart < 1 ||
    ref.lineEnd < ref.lineStart
  ) {
    throw new Error('Invalid evidence reference');
  }

  const lines = `#L${ref.lineStart}-L${ref.lineEnd}`;
  if (ref.file.startsWith(LEGACY_PREFIX)) {
    const legacyPath = encodePath(ref.file.slice(LEGACY_PREFIX.length));
    return `${LEGACY_REPOSITORY}/blob/${LEGACY_COMMIT}/${legacyPath}${lines}`;
  }
  return `${PROJECT_REPOSITORY}/blob/${encodeURIComponent(projectRef)}/${encodePath(ref.file)}${lines}`;
}

export function validateExpectedCounts(summary) {
  const mismatches = [];
  if (summary.screenCount !== 6) mismatches.push(`Expected 6 screens, found ${summary.screenCount}`);
  if (summary.taskCount !== 20) mismatches.push(`Expected 20 tasks, found ${summary.taskCount}`);
  if (summary.confirmedTaskCount !== 18) mismatches.push(`Expected 18 confirmed tasks, found ${summary.confirmedTaskCount}`);
  if (summary.cannotDetermineCount !== 2) mismatches.push(`Expected 2 cannot-determine tasks, found ${summary.cannotDetermineCount}`);
  return mismatches;
}
