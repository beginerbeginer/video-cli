# video-cli

FFmpeg をラップしたシンプルな動画処理 CLI ツール。

## 機能

| 操作 | 説明 |
|------|------|
| trim | 動画を指定した時間範囲で切り出す |
| concat | 複数の動画を結合する（互換あり: copy / 互換なし: 再エンコード） |
| resize | 動画の解像度を変更する |

## 前提条件

- Python 3.10 以上
- ffmpeg / ffprobe がインストール済みで PATH が通っていること

```bash
brew install ffmpeg
```

## セットアップ

```bash
git clone <repository>
cd video-cli
pip install -e .
```

## 使い方

```bash
python main.py
```

メニューに従って操作を選択し、ファイルパスや時間を入力する。

### ドライラン

レビュー画面で「ドライランする」を選ぶと、FFmpeg コマンドの確認だけ行い実行しない。

## プロジェクト構造

```
video-cli/
├── main.py              # エントリーポイント・ディスパッチ
├── domain/              # ドメインモデル（MediaInfo, TrimRange など）
├── shared/              # 共通ユーティリティ（errors, formatters）
├── validation/          # 入力バリデーション
├── ffmpeg/              # FFmpeg ラッパー（probe, runner, strategy）
├── ui/                  # プロンプト・メニュー・レビュー UI
├── usecases/            # ユースケースフロー（trim / concat / resize）
└── tests/               # ユニットテスト
```

## テスト

```bash
python -m pytest tests/ -v
```

## 設計方針

- `handle_*_review`: Dictionary Dispatch で action → FlowResult を変換
- `execute_concat`: Strategy パターンで copy / 再エンコードを切り替え
- `run_*_iteration`: ガード節 + 小関数分割でフロー制御
- if を減らすために抽象クラスを増やさない
