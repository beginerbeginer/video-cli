---
name: test
description: uv run pytest でテストを実行する。失敗したテストがあれば原因を特定して修正する。
allowed-tools:
  - Bash(uv run pytest *)
  - Read
  - Grep
---

`uv run pytest` を実行してください。

1. `uv run pytest -v` を実行する
2. 失敗したテストがあれば、エラーメッセージとスタックトレースを読んで原因を特定する
3. 修正して再度 `uv run pytest` を実行し、全テスト green を確認する
4. 結果を報告する
