const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const ts = require('typescript');
const axios = require('axios');

// Load the actual TypeScript helper using the project's existing compiler.
const source = fs.readFileSync(path.join(__dirname, '../src/api/base-url.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText;
const exportsObject = {};
vm.runInNewContext(compiled, { exports: exportsObject });
const { getApiBaseUrl } = exportsObject;

for (const [name, configuredUrl, expected] of [
  ['default development proxy', undefined, '/api/analyze/'],
  ['empty setting', '', '/api/analyze/'],
  ['blank setting', '   ', '/api/analyze/'],
  ['root setting', '/', '/api/analyze/'],
  ['relative API base', '/api', '/api/analyze/'],
  ['trailing slash', '/api/', '/api/analyze/'],
  ['backend origin', 'http://localhost:8000', 'http://localhost:8000/api/analyze/'],
  ['backend origin with trailing slash', 'http://127.0.0.1:8000/', 'http://127.0.0.1:8000/api/analyze/'],
  ['absolute API base', 'https://example.com/api', 'https://example.com/api/analyze/'],
  ['absolute API base with whitespace', ' https://example.com/api/ ', 'https://example.com/api/analyze/'],
  ['custom deployment prefix', 'https://example.com/repolens/api/', 'https://example.com/repolens/api/analyze/'],
]) {
  test(`analysis URL: ${name}`, () => {
    const client = axios.create({ baseURL: getApiBaseUrl(configuredUrl) });
    assert.equal(client.getUri({ url: '/analyze/' }), expected);
  });
}

test('a backend origin prefixes every API endpoint consistently', () => {
  const client = axios.create({ baseURL: getApiBaseUrl('http://localhost:8000') });
  for (const endpoint of ['/analyze/123', '/diagrams/types', '/chat/', '/health/123']) {
    assert.equal(client.getUri({ url: endpoint }), `http://localhost:8000/api${endpoint}`);
  }
});
