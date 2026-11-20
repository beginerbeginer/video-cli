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

| コマンド                  | 内容                                                  |
| ------------------------- | ----------------------------------------------------- |
| `npm run dev`             | 開発サーバー（`/api` は 127.0.0.1:8000 に転送）       |
| `npm run build`           | 型チェックしてから本番ビルド（`dist/`）               |
| `npm run lint`            | ESLint（警告も 0 件でないと失敗: `--max-warnings 0`） |
| `npm run lint:fix`        | ESLint の自動修正                                     |
| `npm run typecheck`       | TypeScript の型チェック（`tsc -b`）                   |
| `npm run format`          | Prettier で整形                                       |
| `npm run format:check`    | 整形されているかの確認                                |
| `npm test`                | Vitest + Testing Library                              |
| `npm run storybook`       | Storybook（http://localhost:6006）                    |
| `npm run build-storybook` | Storybook の静的ビルド（`storybook-static/`）         |

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
- ストーリー（`*.stories.tsx`）と `.storybook/main.ts`: `eslint-plugin-storybook` の `flat/recommended`（`.storybook/preview.tsx` にも React のルールを効かせる）
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
| push / PR                  | `.github/workflows/frontend.yml`                                | `lint` → `typecheck` → `format:check` → `test` → `build` → `build-storybook`   |

## 開発の流れ: 部品を Storybook で先に作り、あとで画面に組み込む

UI は次の順番で作ります。

1. **作る部品を決める**: Storybook の「はじめに / コンポーネント一覧」に「予定」として載せる
   （データは `src/docs/component-catalog.ts`）
2. **部品を Storybook で作る**: ストーリーを書き、状態ごとの見た目とテストを固める。
   できたら一覧の状態を「作成済み」にする
3. **画面で組み合わせる**: 画面側の issue で、部品を組み合わせて API とつなぐ。
   組み込んだら一覧の状態を「画面で使用中」にする

### 部品と画面の役割分担

|                | 部品（`src/components/`）                               | 画面（画面側の issue で作る）    |
| -------------- | ------------------------------------------------------- | -------------------------------- |
| 担当           | 表示だけ                                                | データの取得と、部品の組み合わせ |
| データ         | **props で受け取る**                                    | API から取って部品に渡す         |
| API の呼び出し | **しない**（`fetch` や TanStack Query を使わない）      | する                             |
| 操作の結果     | `onSelect` や `onCancel` などのコールバックで親に伝える | コールバックを受けて API を呼ぶ  |

部品が API を呼ばないので、Storybook では props を変えるだけで
「読み込み中」「エラー」などの状態をすべて再現できます。

## ストーリーの書き方の決まり

### ファイルの置き場所と命名

- ストーリーは部品と同じフォルダに `部品名.stories.tsx` で置く
  - 例: `src/components/ui/button.tsx` → `src/components/ui/button.stories.tsx`
- `meta.title` は `分類/部品名`（例: `UI/Button`）
- ストーリーの export 名は英語の PascalCase、画面に出す名前は `name` で日本語にする
  （export 名はストーリーの URL の ID になるので、英語にしておくとリンクが壊れにくい）

```tsx
export const Loading: Story = {
  name: "読み込み中",
  args: { loading: true },
};
```

### 用意する状態

部品ごとに、意味のある状態をストーリーにします。当てはまらない状態は作らなくてかまいません。

| 状態       | 例                                                                                    |
| ---------- | ------------------------------------------------------------------------------------- |
| 通常       | `Default` / `name: "通常"`                                                            |
| 読み込み中 | `Loading`                                                                             |
| 空         | `Empty`（一覧が 0 件など）                                                            |
| エラー     | `WithError`（エラーメッセージの表示。`Error` はグローバルと名前がぶつかるので避ける） |
| 長い文字列 | `LongText`（長いファイル名・パス・ログ）                                              |
| ダーク     | `Dark`（`globals: { theme: "ダーク" }`）                                              |
| スマホ幅   | `Mobile`（`globals: { viewport: { value: "mobile", isRotated: false } }`）            |

ライト / ダークと PC 幅 / スマホ幅は、Storybook のツールバーからも切り替えられます。

### ストーリーはそのままテストになる

`src/stories.test.tsx` が `src/**/*.stories.tsx` をすべて集め、
各ストーリーを描画して `play` 関数を実行します（portable stories）。
ストーリーを書けば、テストへの登録は不要です。

操作の結果は `play` 関数で確かめます。

```tsx
export const Default: Story = {
  name: "通常",
  args: { onClick: fn() },
  play: async ({ args, canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByRole("button", { name: "実行" }));
    await expect(args.onClick).toHaveBeenCalledTimes(1);
  },
};
```

TDD は次の順番で進めます。

1. Red: 状態のストーリーと、期待する結果を書いた `play` 関数を先に書き、`npm test` で失敗を確かめる
2. Green: 部品を実装して `npm test` を通す
3. Refactor: `npm test` が green のまま整える

`play` で書きにくい細かい振る舞い（関数の分岐など）は、従来どおり `*.test.tsx` に書きます。

### アクセシビリティ

Storybook の「Accessibility」パネル（addon-a11y）で、ストーリーごとに違反がないか確認してください。
