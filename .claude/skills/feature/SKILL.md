---
name: feature
description: 新機能を plan→issue→TDD→verify→merge の流れで実装する
tools: Bash(uv run pytest*), Bash(git *), Bash(gh *), Read, Edit, Write, Grep, Glob
---

## フロー

### 1. 探索・設計
- 実装対象の機能を確認する
- 既存コードのパターンを把握する（domain/, ffmpeg/, validation/, usecases/, ui/, tests/）
- 参考にすべき既存ファイルを特定する

### 2. GitHub issue 作成・ブランチ切り出し
- issue がなければ `gh issue create` で作成する（ラベル: feat）
- `git checkout -b chore/N-機能名` でブランチを切る

### 3. TDD: Red → Green → Refactor
t_wada スタイルで進める（twada スキルの原則に従う）。

**Red**
- テストを先に書く
- `uv run pytest tests/test_xxx.py -v` で失敗を確認する

**Green**
- テストが通る最小限の実装を書く
- `uv run pytest tests/test_xxx.py -v` で通過を確認する

**Refactor**
- 重複・責務の混在を取り除く
- テストが引き続き通ることを確認する

### 4. 全テスト確認
- `uv run pytest` で既存テストが壊れていないことを確認する

### 5. 動作確認
- `uv run python main.py` で実際に機能を操作して動作確認する
- 正常系・異常系の両方を確認する

### 6. PR 作成・マージ
- `git add` → `git commit`（Why を日本語で）
- `gh pr create --base main --title "..." --body "closes #N" --label "feat" --label "test"`
- CI（GitHub Actions）が通ったことを確認してからマージ
- `gh pr merge N --merge --delete-branch`
- `git checkout main && git pull`
