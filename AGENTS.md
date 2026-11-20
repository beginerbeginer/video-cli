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

**1 行目は `種類: 日本語の要約` にする（[Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/)）。**  
**本文には Why（なぜそうしたのか）を日本語で書く。**  
How（どう変えたか）はコードを見ればわかるので書かない。

```
種類: 変更の要約（1行。例: feat: 動画の分割機能を追加する）

変更した理由・背景を説明する。
何が問題で、なぜこの変更が必要だったのかを書く。

Co-Authored-By: <ツール名> (<実際のモデル名>) <noreply アドレス>
```

### 種類（1 行目の先頭）

種類は英語の小文字で書き、`: `（コロンと半角空白）のあとに日本語の要約を書く。範囲を示したいときは `fix(ffmpeg): ...` のようにかっこで添えてよい。

| 種類 | 意味 | バージョン |
|---|---|---|
| `feat` | 機能の追加 | マイナーを上げる |
| `fix` | 不具合の修正（セキュリティの修正を含む） | パッチを上げる |
| `perf` | 性能の改善 | パッチを上げる |
| `feat!` / `fix!`、または本文に `BREAKING CHANGE:` | 互換性を壊す変更 | メジャーを上げる（0.x の間はマイナー） |
| `refactor` / `test` / `docs` / `ci` / `build` / `chore` / `style` / `revert` | 利用者から見た動きが変わらない変更 | 上げない（リリースに載らない） |

- `feat` ラベルの issue は `feat` のコミットになる。`infra` ラベルの issue は主に `refactor` / `ci` / `chore` / `docs` などになる
- 1 つのコミットに種類の違う変更を混ぜない。混ざるならコミットを分ける
- 形が違うコミットは CI（`conventional-commits` の `commits`）が警告を出す。失敗にはしないが、リリースに載らなくなるので直す

### AI ツール / モデルの記載（Co-Authored-By）

- Co-Authored-By には **実際に使っている AI ツールとモデル** を書く。モデル名をこのファイルや過去のコミットから書き写さない
- Codex なら、ツール名は `Codex`、モデル名は今のセッションで実際に動いているモデルを書く（例の形: `Co-Authored-By: Codex (<モデル名>) <noreply@openai.com>`）
- ツール自身がコミット用の attribution 行を指定する場合（Claude Code など）は、その行をそのまま使う
- AI を使っていないコミットには付けない

### PR

- PR のタイトルもコミットと同じ `種類: 日本語の要約` の形にする。形が違うと CI（`conventional-commits` の `pr-title`）が失敗する
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

## リリースのルール

### バージョン番号: セマンティックバージョニング（SemVer）

番号は `メジャー.マイナー.パッチ` で表し、タグ名には `v` を付ける（例: `v1.4.2`）。

| 変更の種類 | 上げる数字 | 例 |
|---|---|---|
| 互換性を壊す変更（今までの使い方ができなくなる） | メジャー | `1.4.2` → `2.0.0` |
| 機能の追加（今までの使い方はそのまま使える） | マイナー | `1.4.2` → `1.5.0` |
| 不具合の修正・セキュリティの修正 | パッチ | `1.4.2` → `1.4.3` |

- 上の数字を上げたら、下の数字は 0 に戻す
- どの数字を上げるかは、前回のリリースから main に入ったコミットの種類で決まる（「コミットメッセージのルール」の表）
- 今は `0.x` の段階。互換性を壊す変更でも、1.0.0 になるまではマイナーを上げる（`release-please-config.json` の `bump-minor-pre-major`）
- GUI 刷新（#82）が終わった時点（#99 のマージ後）で `1.0.0` を出す。そのときは、コミットの本文に `Release-As: 1.0.0` と書いたコミットを main に入れる

### 既存のタグの扱いと、バージョンが食い違ったときの直し方

release-please を入れる前（2026-05-22）に、手で作ったタグが 2 つある。`v0.2.0`（GitHub Releases あり）と `v0.3.0`（タグだけ）。このタグは消さない・付け替えない。

- release-please は、`.release-please-manifest.json` の版と同じ名前の GitHub Releases を「前回のリリース」として探し、無ければ同じ名前の Git タグを探す。見つかれば、そこから後のコミットで次の版を決める。このときは `bootstrap-sha` を使わない
- 今はマニフェストが `0.3.0` なので、前回のリリースはタグ `v0.3.0` になる。下の「リリースの手順」の 5 にある「出発点は `0.1.0`」「`bootstrap-sha` より前を含めない」は、タグが見つからないときだけの動きで、今は当てはまらない
- マニフェストの版が既存のタグより古いと、release-please は既存のタグと同じ版を作ろうとして、`Duplicate release tag` で失敗する（#118 のマージ後に起きた失敗がこれ。#124 で直した）
- `tests/test_release_please_config.py` が、マニフェストが既存のタグより古くならないこと、`pyproject.toml`・`uv.lock` と同じ版であることを確かめる。手で作ったタグはテストの `MANUAL_RELEASE_TAGS` にも書いてある（CI はタグを取ってこないため）

食い違ったときの直し方:

1. `git fetch origin --tags` でタグを取ってきてから、`git tag -l` で最新のタグを確かめる。タグを取らずに調べると、既存のタグを見落とす
2. `.release-please-manifest.json`・`pyproject.toml`・`uv.lock`（video-cli の行）を、最新のタグの版にそろえる
3. `CHANGELOG.md` に、既存のタグと同じかそれより古い版の項目ができていたら消す。その変更は、次の版の項目に載る
4. コミットの種類は `chore` か `ci` にする。`feat` や `fix` にすると、release-please がそれを機能や修正として数えてしまう
5. 次の版を決まりと違う番号にしたいときだけ、コミットの本文に `Release-As: x.y.z` を書く。マニフェストを直せば、ふつうは要らない

### リリースの手順（release-please）

1. PR を main にマージすると、ワークフロー `release-please` が動き、次のバージョンと `CHANGELOG.md` の更新を書いた「リリース用の PR」（タイトルは `chore(main): release 0.x.y`）を作る。すでにあれば内容を更新する
2. リリースに載る種類（`feat` / `fix` / `perf` / 互換性を壊す変更）のコミットが無いあいだは、リリース用の PR は作られない
3. オーナーがリリース用の PR をマージすると、`v0.x.y` の Git タグと GitHub Releases が作られる
4. バージョンを書き換えるファイルは `pyproject.toml` と `uv.lock`（video-cli の行だけ）。設定は `release-please-config.json`、今のバージョンは `.release-please-manifest.json` にある
5. 出発点は `0.1.0`。`bootstrap-sha` に指定したコミットより前の履歴は、最初のリリースに含めない

- ワークフローの手動実行（Actions → release-please → Run workflow）でも、リリース用の PR を作り直せる
- リポジトリの Settings → Actions → General の「Allow GitHub Actions to create and approve pull requests」が無効だと、リリース用の PR を作れない
- 別のファイルのバージョンも書き換えたいとき（例: `frontend/package.json`）は、`release-please-config.json` の `packages["."].extra-files` に `{ "type": "json", "path": "frontend/package.json", "jsonpath": "$.version" }` を足す。そのファイルの今のバージョンは `.release-please-manifest.json` と同じにしておく

### 注意: リリース用の PR では CI が自動で動かない

release-please は `GITHUB_TOKEN` でリリース用の PR を作る。GitHub の制限で、`GITHUB_TOKEN` が起こした操作からはほかのワークフロー（`test` や `conventional-commits`）が起動しない。リリース用の PR はバージョンと CHANGELOG だけを変えるので、今はこのままでよい。

CI を動かしたくなったときの対処:

- 手早く済ませるなら: リリース用の PR のブランチに、人が空でないコミットを 1 つ push する（人の操作なので CI が動く）
- 恒久的には: GitHub App のトークン（`actions/create-github-app-token`）か、権限を絞った fine-grained personal access token をシークレットに登録し、`release-please-action` の `token` に渡す

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
