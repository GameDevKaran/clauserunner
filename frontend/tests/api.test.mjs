import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import ts from 'typescript';

async function loadApi(fetchMock) {
  const source = await readFile(new URL('../src/api.ts', import.meta.url), 'utf8');
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const module = { exports: {} };

  vm.runInNewContext(compiled, {
    exports: module.exports,
    fetch: fetchMock,
    module,
    window: { location: { port: '' } },
  });

  return module.exports;
}

test('fetchAuditEvents uses the global endpoint when no obligation is supplied', async () => {
  const urls = [];
  const api = await loadApi(async (url) => {
    urls.push(url);
    return { json: async () => [] };
  });

  await api.fetchAuditEvents();

  assert.deepEqual(urls, ['/api/audit']);
  assert.ok(!urls[0].includes('/obligations//audit'));
});

test('fetchAuditEvents preserves the obligation-specific endpoint', async () => {
  const urls = [];
  const api = await loadApi(async (url) => {
    urls.push(url);
    return { json: async () => [] };
  });

  await api.fetchAuditEvents('clauserunner-obligation-acme-sla');

  assert.deepEqual(urls, [
    '/api/obligations/clauserunner-obligation-acme-sla/audit',
  ]);
});
