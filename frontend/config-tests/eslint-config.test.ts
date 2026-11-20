// @vitest-environment node
import path from "node:path";

import { ESLint } from "eslint";

const FRONTEND_ROOT = path.resolve(import.meta.dirname, "..");
const FIXTURES_DIR = path.join(import.meta.dirname, "fixtures");
// 型情報つきの lint は初回に TypeScript のプロジェクトを読むので、既定の 5 秒では足りない。
const TYPED_LINT_TIMEOUT_MS = 60_000;

// fixtures は違反をわざと含むので普段の lint からは外している。ここでは ignore を切って直接当てる。
async function lintFixture(name: string, options: ESLint.Options = {}): Promise<ESLint.LintResult> {
  const eslint = new ESLint({ cwd: FRONTEND_ROOT, ignore: false, ...options });
  const [result] = await eslint.lintFiles([path.join(FIXTURES_DIR, name)]);
  if (result === undefined) {
    throw new Error(`${name} の lint 結果がありません`);
  }
  return result;
}

function ruleIdsOf(result: ESLint.LintResult): (string | null)[] {
  return result.messages.map((message) => message.ruleId);
}

describe("eslint の設定", { timeout: TYPED_LINT_TIMEOUT_MS }, () => {
  it("決まりどおりに書いたファイルは警告もエラーも出ない", async () => {
    // Arrange / Act
    const result = await lintFixture("valid.ts");

    // Assert
    expect(result.messages).toStrictEqual([]);
  });

  it("import の順番を崩すと import-x/order のエラーになる", async () => {
    // Arrange / Act
    const result = await lintFixture("unordered-imports.ts");

    // Assert
    expect(ruleIdsOf(result)).toContain("import-x/order");
    expect(result.errorCount).toBeGreaterThan(0);
  });

  it("import の順番の崩れは --fix で組み込みモジュールが先頭に並び直る", async () => {
    // Arrange / Act
    const result = await lintFixture("unordered-imports.ts", { fix: true });

    // Assert
    expect(result.output).toMatch(
      /^import path from "node:path";\n\nimport \{ useState \} from "react";/,
    );
  });

  it("any を書くと no-explicit-any のエラーになる", async () => {
    // Arrange / Act
    const result = await lintFixture("explicit-any.ts");

    // Assert
    expect(ruleIdsOf(result)).toContain("@typescript-eslint/no-explicit-any");
  });

  it("非 null アサーションを書くと no-non-null-assertion のエラーになる", async () => {
    // Arrange / Act
    const result = await lintFixture("non-null-assertion.ts");

    // Assert
    expect(ruleIdsOf(result)).toContain("@typescript-eslint/no-non-null-assertion");
  });

  it("@ts-ignore を書くと ban-ts-comment のエラーになる", async () => {
    // Arrange / Act
    const result = await lintFixture("ts-ignore.ts");

    // Assert
    expect(ruleIdsOf(result)).toContain("@typescript-eslint/ban-ts-comment");
  });

  it("console を書くと no-console のエラーになる", async () => {
    // Arrange / Act
    const result = await lintFixture("console.ts");

    // Assert
    expect(ruleIdsOf(result)).toContain("no-console");
    expect(result.warningCount).toBe(0);
  });
});
