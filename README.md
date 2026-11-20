# video-cli

FFmpeg をラップしたシンプルな動画処理 CLI ツール。

## 機能

| 操作 | 説明 |
|------|------|
| trim | 動画を指定した時間範囲で切り出す |
| concat | 複数の動画を結合する（互換あり: copy / 互換なし: 再エンコード） |
| resize | 動画の解像度を変更する |
| volume | 音量を調整する |
| audio_extract | 動画から音声を抽出する |
| thumbnail | 指定秒数のフレームを画像として保存する |
| gif | 動画を GIF に変換する |
| speed | 動画の再生速度を変更する（0.25x〜4.0x） |
| mute | 動画から音声を削除する |
| convert | 動画のフォーマットを変換する（再エンコードなし） |
| rotate | 動画を回転・反転する |
| info | 動画の情報（解像度・コーデック・長さ等）を表示する |
| crop | 動画の指定範囲を切り出す |

## 前提条件

- Python 3.10 以上
- [uv](https://github.com/astral-sh/uv) がインストール済み
- ffmpeg / ffprobe がインストール済みで PATH が通っていること

```bash
brew install ffmpeg
```

## セットアップ

```bash
git clone <repository>
cd video-cli
uv sync
```

## 使い方

```bash
uv run python main.py
```

メニューに従って操作を選択し、ファイルパスや時間を入力する。

### ドライラン

レビュー画面で「ドライランする」を選ぶと、FFmpeg コマンドの確認だけ行い実行しない。

## GUI（React）で使う

ブラウザで操作する GUI。API サーバー（FastAPI）と画面（React）を、別々のターミナルで起動する。

> 1 コマンドでの起動は #91 で追加する予定。それまでは、以下の手順で起動する。

### 前提

- Node.js 26.13.0 以上（`frontend/.nvmrc` のバージョン）
  - `frontend/.npmrc` で `engine-strict=true` にしているので、古い Node.js では `npm ci` が `EBADENGINE` で止まる
  - nvm を使っている場合は、`frontend` で `nvm use` を打つと `.nvmrc` のバージョンに切り替わる
- [uv](https://github.com/astral-sh/uv)
- ffmpeg / ffprobe（CLI と同じ）

### 初回だけ行う準備

リポジトリ直下で、Python の依存を入れる。

```bash
uv sync
```

画面の依存を入れる。

```bash
cd frontend && npm ci
```

### 起動

ターミナルを 2 つ使う。

1. 1 つ目のターミナルで、リポジトリ直下から API サーバーを起動する

   ```bash
   uv run video-gui
   ```

   - http://127.0.0.1:8000 で動く
   - http://127.0.0.1:8000/docs で API の一覧を見られる
   - ポートを変えるときは `uv run video-gui --port 8001` のように指定する（ただし画面の開発サーバーは 8000 番に中継するので、普段は変えない）

2. 2 つ目のターミナルで、リポジトリ直下から画面を起動する

   ```bash
   cd frontend && npm run dev
   ```

3. ブラウザで、2 つ目のターミナルに表示された URL（`Local:` の行。通常は http://localhost:5173/ ）を開く

画面から `/api` へのリクエストは、開発サーバーが API サーバー（http://127.0.0.1:8000）へ中継する。そのため、API サーバーを先に起動しておく。

### 部品の一覧（Storybook）

画面の部品を、画面に組み込む前に 1 つずつ確かめられる。

```bash
cd frontend && npm run storybook
```

ブラウザで、表示された URL（通常は http://localhost:6006/ ）を開く。Storybook だけなら API サーバーは要らない。

### 終了

各ターミナルで `Ctrl+C` を押す。

### よくあるつまずき

- **ポートがすでに使われている**
  - API サーバー: `address already in use` と出て止まる。前に起動した `uv run video-gui` が残っていないか確かめ、止めてから起動し直す
  - 画面: `Port 5173 is in use, trying another one...` と出て、別のポート（5174 など）で起動する。表示された URL を開けば使える
  - Storybook: `Port 6006 is not available.` と出て、別のポートで起動してよいか聞かれる。`y` で進めるか、前の Storybook を止めてから起動し直す
- **ffmpeg / ffprobe が無い**
  - http://127.0.0.1:8000/api/health を開き、`"ffmpeg": false` や `"ffprobe": false` になっていないか確かめる。`false` なら、上の「前提条件」のとおりインストールする
  - 画面に警告を出す処理は、今の雛形にはまだ無い
- **`npm ci` が `EBADENGINE` で止まる**
  - Node.js が古い。`frontend/.nvmrc` のバージョンに切り替えてから、もう一度 `npm ci` を打つ

## プロジェクト構造

```
video-cli/
├── CLAUDE.md            # Claude Code 向け取扱説明書
├── main.py              # エントリーポイント・ディスパッチ
├── domain/              # ドメインモデル（MediaInfo, TrimRange など）
├── shared/              # 共通ユーティリティ（errors, formatters）
├── validation/          # 入力バリデーション
├── ffmpeg/              # FFmpeg ラッパー（probe, runner, commands）
├── ui/                  # プロンプト・メニュー・レビュー UI
├── usecases/            # ユースケースフロー（各機能の flow）
└── tests/               # ユニットテスト
```

## テスト

```bash
uv run pytest
```

## 設計方針

- `handle_*_review`: Dictionary Dispatch で action → FlowResult を変換
- `execute_concat`: Strategy パターンで copy / 再エンコードを切り替え
- `run_*_iteration`: ガード節 + 小関数分割でフロー制御
- if を減らすために抽象クラスを増やさない
