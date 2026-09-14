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

test('fetchAuditEvents adds bounded pagination without malformed paths', async () => {
  const urls = [];
  const api = await loadApi(async (url) => {
    urls.push(url);
    return { json: async () => [] };
  });

  await api.fetchAuditEvents(undefined, 100);
  await api.fetchAuditEvents('clauserunner-obligation-acme-sla', 100, 100);

  assert.deepEqual(urls, [
    '/api/audit?limit=100',
    '/api/obligations/clauserunner-obligation-acme-sla/audit?limit=100&offset=100',
  ]);
  assert.ok(urls.every(url => !url.includes('/obligations//')));
});

test('requestJson handles valid JSON 200 response successfully', async () => {
  const api = await loadApi(async (url) => {
    return {
      status: 200,
      ok: true,
      headers: { get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null },
      json: async () => ({ status: 'healthy' })
    };
  });
  const res = await api.fetchHealth();
  assert.deepEqual(res, { status: 'healthy' });
});

test('requestJson handles empty 240/204 response safely', async () => {
  const api = await loadApi(async (url) => {
    return {
      status: 204,
      ok: true,
      headers: { get: () => null }
    };
  });
  const res = await api.fetchHealth();
  assert.equal(res, null);
});

test('requestJson handles JSON FastAPI error with detail field safely', async () => {
  const api = await loadApi(async (url) => {
    return {
      status: 400,
      ok: false,
      headers: { get: (name) => name.toLowerCase() === 'content-type' ? 'application/json' : null },
      json: async () => ({ detail: 'Invalid inputs provided' })
    };
  });
  await assert.rejects(
    async () => await api.fetchHealth(),
    /Invalid inputs provided/
  );
});

test('requestJson handles plain-text 500 unhandled exceptions safely', async () => {
  const api = await loadApi(async (url) => {
    return {
      status: 500,
      ok: false,
      headers: { get: () => 'text/html' },
      text: async () => 'Internal Server Error'
    };
  });
  await assert.rejects(
    async () => await api.fetchHealth(),
    /Internal Server Error/
  );
});

