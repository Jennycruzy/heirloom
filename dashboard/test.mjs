import assert from 'node:assert/strict';
import fs from 'node:fs';
import { URL } from 'node:url';
import {
  summarizeCatalogue,
  composeScreen,
  taskStatusLabel,
  evidenceUrl,
  validateExpectedCounts,
  LEGACY_COMMIT
} from './lib.mjs';

function runTests() {
  const catalogueUrl = new URL('../catalogue/genapp.json', import.meta.url);
  const catalogue = JSON.parse(fs.readFileSync(catalogueUrl, 'utf-8'));
  const summary = summarizeCatalogue(catalogue);
  assert.deepStrictEqual(validateExpectedCounts(summary), [], 'Count validation failed');

  for (const screen of catalogue.screens) {
    const sortedElements = [...screen.elements].sort((a, b) => a.sourceOrder - b.sourceOrder);
    const expectedOwner = Array.from({ length: 24 }, () => Array(80).fill(null));

    for (const element of sortedElements) {
      assert(Number.isInteger(element.sourceOrder), `Invalid sourceOrder for ${element.elementId}`);
      assert(Number.isInteger(element.row) && element.row >= 1 && element.row <= 24, `Invalid row for ${element.elementId}`);
      assert(Number.isInteger(element.col) && element.col >= 1 && element.col <= 80, `Invalid col for ${element.elementId}`);
      assert(Number.isInteger(element.length) && element.length >= 1, `Invalid length for ${element.elementId}`);
      assert(element.col + element.length - 1 <= 80, `Element ${element.elementId} exceeds grid`);

      for (let offset = 0; offset < element.length; offset += 1) {
        expectedOwner[element.row - 1][element.col - 1 + offset] = element;
      }
    }

    const { rows, cellMeta } = composeScreen(screen);
    assert.strictEqual(rows.length, 24, 'Screen must have 24 rows');
    assert.strictEqual(cellMeta.length, 24, 'Metadata must have 24 rows');

    for (let rowIndex = 0; rowIndex < 24; rowIndex += 1) {
      assert.strictEqual(rows[rowIndex].length, 80, 'Each row must be 80 characters');
      assert.strictEqual(cellMeta[rowIndex].length, 80, 'Each metadata row must have 80 cells');

      for (let colIndex = 0; colIndex < 80; colIndex += 1) {
        const expected = expectedOwner[rowIndex][colIndex];
        const meta = cellMeta[rowIndex][colIndex];
        if (!expected) {
          assert.deepStrictEqual(meta, {}, `Cell at ${rowIndex + 1},${colIndex + 1} should be empty`);
          continue;
        }

        const tokens = String(expected.attrb ?? '').split(',').map(token => token.trim()).filter(Boolean);
        assert.strictEqual(meta.elementId, expected.elementId);
        assert.strictEqual(meta.role, expected.role);
        assert.strictEqual(meta.protected, Boolean(expected.protected));
        assert.strictEqual(meta.attrb, String(expected.attrb ?? ''));
        assert.strictEqual(meta.isCursor, tokens.includes('IC'));
      }
    }

    const visible = [...sortedElements].reverse().find(element =>
      typeof element.initialValue === 'string' && element.initialValue.trim() !== ''
    );
    assert(visible, `${screen.mapName} must contain visible literal text`);
    const expectedText = visible.initialValue.padEnd(visible.length, ' ').slice(0, visible.length);
    assert.strictEqual(
      rows[visible.row - 1].slice(visible.col - 1, visible.col - 1 + visible.length),
      expectedText
    );
  }

  assert.strictEqual(catalogue.provenance.commit, LEGACY_COMMIT, 'Links must use the pinned GenApp commit');
  for (const task of catalogue.tasks) {
    assert.strictEqual(task.modernParityStatus, 'not-assessed');
    for (const ref of task.sourceEvidence) {
      assert(ref.file.startsWith('legacy/cics-genapp/'), `${ref.file} must be legacy source`);
      const path = ref.file.slice('legacy/cics-genapp/'.length).split('/').map(encodeURIComponent).join('/');
      const expected = `https://github.com/cicsdev/cics-genapp/blob/${LEGACY_COMMIT}/${path}#L${ref.lineStart}-L${ref.lineEnd}`;
      assert.strictEqual(evidenceUrl(ref), expected);
    }
  }
  assert.strictEqual(
    evidenceUrl({ file: 'modern-app/database.py', lineStart: 3, lineEnd: 9 }, 'stage3-first-pass'),
    'https://github.com/Jennycruzy/heirloom/blob/stage3-first-pass/modern-app/database.py#L3-L9'
  );

  for (const taskId of ['T-SSP5-1', 'T-SSP5-2']) {
    const task = catalogue.tasks.find(candidate => candidate.taskId === taskId);
    assert(task, `${taskId} must exist`);
    assert.strictEqual(task.legacySupportStatus, 'screen-only-cannot-determine');
    assert.strictEqual(
      taskStatusLabel(task),
      'Cannot determine — the screen defines this action, but no presentation program was found.'
    );
  }

  console.log('Dashboard core tests passed: 6 screens, 20 tasks, 18 confirmed, 2 cannot determine.');
}

runTests();
