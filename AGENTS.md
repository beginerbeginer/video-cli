# AGENTS.md

## プロジェクト概要

FFmpeg をラップしたシンプルな動画処理 CLI ツール。
Python 製、外部ライブラリへの実行時依存なし。パッケージ管理は `uv`。

## コマンド

```bash
# アプリ起動
uv run python main.py

# テスト実行
uv run pytest

# テスト（詳細表示）
uv run pytest -v
```

## アーキテクチャ

依存の向きは一方向のみ（上位が下位を参照し、逆方向は禁止）。

```
domain/        ← ドメインモデル（MediaInfo, TrimRange など）。外部依存なし
ffmpeg/        ← FFmpeg/ffprobe ラッパー。domain を参照
validation/    ← 入力バリデーション。domain を参照
shared/        ← 共通ユーティリティ（errors, formatters）
ui/            ← プロンプト・メニュー・レビュー画面
usecases/      ← ユースケースフロー。ffmpeg/validation/ui を組み合わせる
main.py        ← エントリーポイント・ディスパッチ
```

## Review guidelines

- 依存方向がアーキテクチャのルールに違反していないか確認する。
- 一時ファイル・外部プロセス・例外処理でリソースリークが起きないか重視する。
- テストが問題の再発防止として具体的な失敗条件を固定できているか確認する。
- UI（ask_* など）は mock し、ビジネスロジックを過剰に mock していないか確認する。
- `uv run pytest` と lint/format の実行結果、または未実行理由を確認する。

## 新機能追加の手順（厳守）

**ファイルを変更する前に必ず issue を作ること。**

```
1. gh ic                          # issue 作成
2. git checkout -b chore/N-説明   # N は issue 番号
3. テストを書いて Red を確認
4. 実装して Green にする
5. gh pc でPR作成
6. gh pr checks N --watch でCI確認
7. gh pm N でマージ
8. git checkout main && git pull
```

## 各機能の実装パターン

新機能は必ず以下の4つをセットで実装する：

| ファイル | 役割 |
|---------|------|
| `ffmpeg/commands.py` | `build_XXX_command()` 追加 |
| `usecases/xxx_flow.py` | `XxxForm`, `run_xxx_flow()` など |
| `tests/test_xxx_flow.py` | フローのテスト |
| `tests/test_commands.py` | コマンド生成のテスト |

さらに `domain/operations.py`・`ui/main_menu.py`・`main.py` の3箇所を更新する。

## コミットメッセージのルール

**Why（なぜそうしたのか）を日本語で書く。**  
How（どう変えたか）はコードを見ればわかるので書かない。

```
変更の要約（1行）

変更した理由・背景を説明する。
何が問題で、なぜこの変更が必要だったのかを書く。

Co-Authored-By: <ツール名> (<実際のモデル名>) <noreply アドレス>
```

### AI ツール / モデルの記載（Co-Authored-By）

- Co-Authored-By には **実際に使っている AI ツールとモデル** を書く。モデル名をこのファイルや過去のコミットから書き写さない
- Codex なら、ツール名は `Codex`、モデル名は今のセッションで実際に動いているモデルを書く（例の形: `Co-Authored-By: Codex (<モデル名>) <noreply@openai.com>`）
- ツール自身がコミット用の attribution 行を指定する場合（Claude Code など）は、その行をそのまま使う
- AI を使っていないコミットには付けない

### PR

- 本文は `.github/pull_request_template.md` に沿って書く
- 「使用した AI ツール / モデル」の区画（`<!-- ai-attribution:start -->` 〜 `<!-- ai-attribution:end -->`）は、ワークフロー `pr-ai-attribution` が各コミットの Co-Authored-By から自動で書き込む。手で書かない・消さない

## issue と PR のラベル

ラベルの名前・説明・色は `.github/labels.json` で管理する。main にマージされるとワークフロー `sync-labels` が GitHub に反映する（手動実行も可）。ラベルを増やす・変えるときは、GitHub の画面ではなくこのファイルを直す。

**種類**: issue 1 つにつき 1 つ付ける

| ラベル | 役割 |
|---|---|
| `feat` | 新しい機能を追加する |
| `infra` | 内部の改善・リファクタリング・開発環境の整備。利用者から見た機能は変わらない |
| `まとめ` | 複数の issue を束ねる親 issue や、ロードマップ |

**取り組み**: 該当するときだけ付ける

| ラベル | 役割 |
|---|---|
| `GUI刷新` | GUI を React + FastAPI に作り直す取り組み（#82）に属する |

**領域**: 変更する場所。1 つ以上付ける

| ラベル | 役割 |
|---|---|
| `領域:CLI` | ターミナルで使う CLI（`ui/cli/`, `main.py`） |
| `領域:ロジック` | 動画処理のルールと入力チェック（`domain/`, `usecases/`, `validation/`, `shared/`） |
| `領域:FFmpeg` | FFmpeg・ffprobe の呼び出し（`ffmpeg/`） |
| `領域:API` | Python の API サーバー（`api/`） |
| `領域:フロント` | React の画面（`frontend/`） |
| `領域:開発環境` | CI、lint、テスト基盤、Claude Code の設定、ドキュメント |

**付け方**

- issue を作るときは、種類を 1 つ、領域を 1 つ以上付け、該当すれば取り組みも付ける
- PR には、対応する issue と同じラベルを付ける
- PR の `領域:*` は、変更したパスからワークフロー `labeler` も自動で付ける（`.github/labeler.yml`）。自動で付かなかった領域は手で足す

## コードコメントのルール

コメントには **Why not** を書く（なぜ他の選択肢を選ばなかったか）。  
What/How は書かない（コードを読めばわかる）。

## テストのルール

- TDD: Red → Green の順番を守る
- UI（ask_* など）は mock する。ビジネスロジックは mock しない
- `uv run pytest` が green の状態でのみリファクタリングする

## gh コマンドのエイリアス

| エイリアス | 説明 |
|-----------|------|
| `gh ic` | issue 作成 |
| `gh pc` | PR 作成（main へ） |
| `gh pm N` | PR マージ＆ブランチ削除 |
| `gh il` | issue 一覧 |
| `gh mypr` | 自分の PR 一覧 |
