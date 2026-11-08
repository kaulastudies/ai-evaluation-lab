import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { createRequire } from 'node:module';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// Resolve the parser through the same dependency chain as the installed lint
// configuration, rather than depending on npm hoisting a transitive package.
const require = createRequire(import.meta.url);
const configRequire = createRequire(require.resolve('eslint-config-next'));
const typescriptRequire = createRequire(configRequire.resolve('typescript-eslint'));
const parser = typescriptRequire('@typescript-eslint/parser');
const root = mkdtempSync(join(tmpdir(), 'proofpay-tooling-'));
mkdirSync(join(root, 'src'));
writeFileSync(join(root, 'src/included.ts'), 'export const included = true;');
writeFileSync(join(root, 'tsconfig.json'), JSON.stringify({ compilerOptions: { strict: true }, include: ['src/**/*.ts'] }));
after(() => {
  parser.clearCaches();
  rmSync(root, { recursive: true, force: true });
});

function parse(filename) {
  const code = 'export const value: number = 42;';
  const filePath = join(root, filename);
  writeFileSync(filePath, code);
  return parser.parseForESLint(code, {
    filePath,
    tsconfigRootDir: root,
    projectService: { allowDefaultProject: ['*.config.ts'] },
  });
}

test('tooling: patched matcher preserves typed linting for explicitly allowed files including dotfiles', () => {
  for (const filename of ['tooling.config.ts', '.hidden.config.ts']) {
    const result = parse(filename);
    assert.ok(result.services.program);
    assert.equal(result.ast.body[0].type, 'ExportNamedDeclaration');
    assert.ok(result.services.program.getSourceFile(join(root, filename)));
  }
});

test('tooling: unmatched files are still denied by the actual parser project-service boundary', () => {
  assert.throws(() => parse('denied.ts'), /was not found by the project service/);
});
