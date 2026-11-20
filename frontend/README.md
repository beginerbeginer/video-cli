# frontend

video-cli の GUI（Vite + React + TypeScript + Tailwind + shadcn/ui）。
全体の計画は親 issue #82 を見てください。

## コマンド

Node のバージョンは `.nvmrc` に合わせてください（`engine-strict` なので違うと `npm ci` が止まります）。

```bash
npm ci                   # 依存のインストール
npm run dev              # 開発サーバー（/api は 127.0.0.1:8000 へ proxy）
npm run storybook        # Storybook（http://localhost:6006）
npm test                 # Vitest（部品のテスト + ストーリーのテスト）
npm run lint             # ESLint
npm run build            # 型チェック + 本番ビルド
npm run build-storybook  # Storybook の静的ビルド（storybook-static/）
```

## 開発の流れ: 部品を Storybook で先に作り、あとで画面に組み込む

UI は次の順番で作ります。

1. **作る部品を決める**: Storybook の「はじめに / コンポーネント一覧」に「予定」として載せる
   （データは `src/docs/component-catalog.ts`）
2. **部品を Storybook で作る**: ストーリーを書き、状態ごとの見た目とテストを固める。
   できたら一覧の状態を「作成済み」にする
3. **画面で組み合わせる**: 画面側の issue で、部品を組み合わせて API とつなぐ。
   組み込んだら一覧の状態を「画面で使用中」にする

### 部品と画面の役割分担

| | 部品（`src/components/`） | 画面（画面側の issue で作る） |
|---|---|---|
| 担当 | 表示だけ | データの取得と、部品の組み合わせ |
| データ | **props で受け取る** | API から取って部品に渡す |
| API の呼び出し | **しない**（`fetch` や TanStack Query を使わない） | する |
| 操作の結果 | `onSelect` や `onCancel` などのコールバックで親に伝える | コールバックを受けて API を呼ぶ |

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

| 状態 | 例 |
|---|---|
| 通常 | `Default` / `name: "通常"` |
| 読み込み中 | `Loading` |
| 空 | `Empty`（一覧が 0 件など） |
| エラー | `WithError`（エラーメッセージの表示。`Error` はグローバルと名前がぶつかるので避ける） |
| 長い文字列 | `LongText`（長いファイル名・パス・ログ） |
| ダーク | `Dark`（`globals: { theme: "ダーク" }`） |
| スマホ幅 | `Mobile`（`globals: { viewport: { value: "mobile", isRotated: false } }`） |

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
