# frontend

video-cli の新しい GUI（React + TypeScript + Vite + Tailwind CSS + shadcn/ui）。
API（FastAPI）とは HTTP だけでつながる。開発中は Vite の proxy で `/api` を `http://127.0.0.1:8000` に転送する。

## 使い方

```bash
cd frontend
nvm use            # .nvmrc の Node（LTS）に合わせる
npm install        # Git フック（lefthook）もここで入る
npm run dev        # 開発サーバー
```

| コマンド               | 内容                                                  |
| ---------------------- | ----------------------------------------------------- |
| `npm run dev`          | 開発サーバー（`/api` は 127.0.0.1:8000 に転送）       |
| `npm run build`        | 型チェックしてから本番ビルド（`dist/`）               |
| `npm run lint`         | ESLint（警告も 0 件でないと失敗: `--max-warnings 0`） |
| `npm run lint:fix`     | ESLint の自動修正                                     |
| `npm run typecheck`    | TypeScript の型チェック（`tsc -b`）                   |
| `npm run format`       | Prettier で整形                                       |
| `npm run format:check` | 整形されているかの確認                                |
| `npm test`             | Vitest + Testing Library                              |

## 厳しくしている設定

このあと書くコードはすべてこの設定の上で書く。ルールに引っかかったときは、ルールを外さずにコードを直す。

### TypeScript（`tsconfig.strict.json`、app と node の両方が継承）

- `strict`
- `noUncheckedIndexedAccess`（配列・辞書の要素は `undefined` かもしれないものとして扱う）
- `exactOptionalPropertyTypes`（省略可能なプロパティに `undefined` を明示的に入れられない）
- `noImplicitOverride` / `noImplicitReturns` / `noPropertyAccessFromIndexSignature`
- `noFallthroughCasesInSwitch` / `noUnusedLocals` / `noUnusedParameters`
- `allowUnreachableCode: false` / `allowUnusedLabels: false`
- `forceConsistentCasingInFileNames` / `noUncheckedSideEffectImports`
- `erasableSyntaxOnly`（`enum` など、型を消すだけでは JS にならない構文を禁止）
- `verbatimModuleSyntax` / `isolatedModules` / `allowJs: false`

### ESLint（`eslint.config.ts`）

- `typescript-eslint` の `strictTypeChecked` と `stylisticTypeChecked`（`projectService` で型情報を使う）
  - `any`・非 null アサーション（`!`）を禁止
  - `@ts-ignore` / `@ts-nocheck` を禁止。`@ts-expect-error` は 10 文字以上の説明つきのときだけ許す
  - 型の import は `import type` にそろえる（`consistent-type-imports`、`consistent-type-specifier-style`）
  - 追加: `switch-exhaustiveness-check`、`strict-boolean-expressions`、`prefer-readonly`、`require-array-sort-compare`、`consistent-type-exports`、`no-import-type-side-effects`
- import（`eslint-plugin-import-x` + TypeScript リゾルバ）
  - 順番とグループ分けを強制し、`--fix` で並べ替える（組み込み → 外部 → `@/` → 相対 → 型。グループ間は空行、各グループ内はアルファベット順）
  - 重複・循環参照・自分自身の import・存在しないパス・`package.json` に無いパッケージ・無駄なパス区切りを禁止
- React: `@eslint-react` の `strict-type-checked`、`react-hooks` の `recommended-latest`、`react-refresh`
- アクセシビリティ: `eslint-plugin-jsx-a11y-x` の `strict`
- `eslint-plugin-unicorn` の `recommended`
- テストファイル（`*.test.ts(x)`）だけ: `@vitest/eslint-plugin`、`eslint-plugin-testing-library`、`eslint-plugin-jest-dom`
- `console`・`debugger`・`alert` を禁止
- 使われていない `eslint-disable` コメントもエラーにする
- 見た目のルールは `eslint-config-prettier` で切り、整形は Prettier に任せる

`config-tests/` に、「import の順番を崩す」「`any` を書く」などの見本（`fixtures/`）を置き、それが実際にエラーになることを `npm test` で確かめている。

### 整形（Prettier）

- `prettier-plugin-tailwindcss` で Tailwind のクラス順をそろえる（`cn()` / `cva()` / `clsx()` の中も対象）

## 書いた時点で自動でチェックされる仕組み

| タイミング                 | 仕組み                                                          | 内容                                                                           |
| -------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| エディタで保存したとき     | `.vscode/settings.json`（推奨拡張は `.vscode/extensions.json`） | Prettier で整形し、ESLint の自動修正をかける                                   |
| Claude Code が編集した直後 | `.claude/settings.json` の PostToolUse フック                   | Prettier と `eslint --fix` をかけ、直しきれない違反を Claude に返す            |
| コミットするとき           | `lefthook.yml`（リポジトリ直下）                                | ステージしたファイルに `eslint --fix` と Prettier。TS を変えたときは型チェック |
| push / PR                  | `.github/workflows/frontend.yml`                                | `lint` → `typecheck` → `format:check` → `test` → `build`                       |
