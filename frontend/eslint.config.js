import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import storybook from "eslint-plugin-storybook";
import { defineConfig, globalIgnores } from "eslint/config";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig([
  globalIgnores(["dist", "storybook-static", "!.storybook"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat["recommended-latest"],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
  },
  {
    // shadcn/ui の生成物は buttonVariants などコンポーネント以外も export する流儀なので、
    // 生成物を書き換えて追従コストを上げるより、このディレクトリだけルールを外す。
    files: ["src/components/ui/**/*.tsx"],
    rules: { "react-refresh/only-export-components": "off" },
  },
  {
    // ストーリーと Storybook の設定は Vite の HMR の対象外なので、react-refresh のルールは関係ない。
    files: ["**/*.stories.tsx", ".storybook/**/*.{ts,tsx}"],
    rules: { "react-refresh/only-export-components": "off" },
  },
  ...storybook.configs["flat/recommended"],
]);
