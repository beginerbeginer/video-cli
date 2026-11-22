import js from "@eslint/js";
import eslintReact from "@eslint-react/eslint-plugin";
import vitest from "@vitest/eslint-plugin";
import { defineConfig, globalIgnores } from "eslint/config";
import prettier from "eslint-config-prettier/flat";
import { createTypeScriptImportResolver } from "eslint-import-resolver-typescript";
import { importX } from "eslint-plugin-import-x";
import jestDom from "eslint-plugin-jest-dom";
import jsxA11y from "eslint-plugin-jsx-a11y-x";
import reactHooks from "eslint-plugin-react-hooks";
import { reactRefresh } from "eslint-plugin-react-refresh";
import testingLibrary from "eslint-plugin-testing-library";
import unicorn from "eslint-plugin-unicorn";
import globals from "globals";
import { configs as tseslintConfigs } from "typescript-eslint";

const TEST_FILES = ["**/*.test.{ts,tsx}"];

export default defineConfig([
  // fixtures は「違反を検出できるか」を確かめるための見本なので、普段の lint からは外す。
  globalIgnores(["dist", "coverage", "config-tests/fixtures"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslintConfigs.strictTypeChecked,
      tseslintConfigs.stylisticTypeChecked,
      importX.flatConfigs.recommended,
      importX.flatConfigs.typescript,
      unicorn.configs.recommended,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    settings: {
      "import-x/resolver-next": [
        createTypeScriptImportResolver({
          alwaysTryTypes: true,
          project: "tsconfig.json",
        }),
      ],
    },
    linterOptions: {
      reportUnusedDisableDirectives: "error",
      reportUnusedInlineConfigs: "error",
    },
    rules: {
      // 型の抜け道を塞ぐ
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-non-null-assertion": "error",
      "@typescript-eslint/ban-ts-comment": [
        "error",
        {
          "ts-expect-error": "allow-with-description",
          "ts-ignore": true,
          "ts-nocheck": true,
          "ts-check": false,
          minimumDescriptionLength: 10,
        },
      ],
      "@typescript-eslint/consistent-type-imports": [
        "error",
        { prefer: "type-imports", fixStyle: "separate-type-imports" },
      ],
      "@typescript-eslint/consistent-type-exports": "error",
      "@typescript-eslint/no-import-type-side-effects": "error",
      "@typescript-eslint/switch-exhaustiveness-check": "error",
      "@typescript-eslint/strict-boolean-expressions": "error",
      "@typescript-eslint/prefer-readonly": "error",
      "@typescript-eslint/require-array-sort-compare": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_", caughtErrors: "all" },
      ],

      // import の決まり
      "import-x/order": [
        "error",
        {
          groups: ["builtin", "external", "internal", ["parent", "sibling", "index"], "type"],
          pathGroups: [{ pattern: "@/**", group: "internal" }],
          "newlines-between": "always",
          alphabetize: { order: "asc", caseInsensitive: true },
        },
      ],
      "import-x/no-duplicates": ["error", { "prefer-inline": false }],
      "import-x/no-cycle": "error",
      "import-x/no-self-import": "error",
      "import-x/no-useless-path-segments": "error",
      "import-x/no-unresolved": "error",
      "import-x/no-extraneous-dependencies": "error",
      "import-x/first": "error",
      "import-x/newline-after-import": "error",
      "import-x/consistent-type-specifier-style": ["error", "prefer-top-level"],

      // デバッグ用コードを残さない
      "no-console": "error",
      "no-debugger": "error",
      "no-alert": "error",

      // unicorn の中で、このプロジェクトの書き方と合わないものだけ調整する
      "unicorn/filename-case": [
        "error",
        // React コンポーネントは PascalCase のファイル名にする慣習なので、kebab-case と並べて許す。
        { cases: { kebabCase: true, pascalCase: true } },
      ],
      "unicorn/name-replacements": [
        "error",
        {
          // props は React の、utils は shadcn/ui の（`@/lib/utils` を前提に部品を生成する）決まった名前なので、
          // ルールを切らずにこの 2 語だけ置き換え対象から外す。
          replacements: { props: false, utils: false },
        },
      ],
    },
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [
      eslintReact.configs["strict-type-checked"],
      reactHooks.configs.flat["recommended-latest"],
      jsxA11y.configs.strict,
      reactRefresh.configs.vite(),
    ],
  },
  {
    // shadcn/ui の生成物は buttonVariants などコンポーネント以外も export する流儀なので、
    // 生成物を書き換えて追従コストを上げるより、このディレクトリだけルールを外す。
    files: ["src/components/ui/**/*.tsx"],
    rules: { "react-refresh/only-export-components": "off" },
  },
  {
    files: TEST_FILES,
    extends: [
      vitest.configs.recommended,
      testingLibrary.configs["flat/react"],
      jestDom.configs["flat/recommended"],
    ],
    languageOptions: { globals: vitest.environments.env.globals },
    rules: {
      "vitest/consistent-test-it": ["error", { fn: "it" }],
      "vitest/no-focused-tests": "error",
      "vitest/no-disabled-tests": "error",
      "vitest/require-top-level-describe": "error",
      "vitest/prefer-strict-equal": "error",
    },
  },
  {
    files: ["*.config.ts", "config-tests/**/*.ts"],
    languageOptions: { globals: globals.node },
  },
  // 整形は Prettier に任せるので、衝突する見た目のルールは最後にまとめて切る。
  prettier,
]);
