---
name: lint
description: >
  ruff で lint・format チェックし、自動修正できるものを直し、pytest まで通す。
  コードの内部品質を一気通貫で確認・修正する。
when_to_use: >
  lint を走らせたい、import の順番を直したい、コードスタイルを整えたい、
  CI に出る ruff エラーを直したい、PR 前に品質チェックをしたいときに参照する。
allowed-tools:
  - Bash(uv run ruff *)
  - Bash(uv run pytest *)
  - Read
  - Edit
---

# lint → 自動修正 → テスト

## 手順

### 1. lint チェック（現状把握）

```bash
uv run ruff check .
```

エラーがなければ終了。

### 2. 自動修正できるものを一括修正

```bash
uv run ruff check . --fix
uv run ruff format .
```

`[*]` マークのついたエラーは自動修正される。

### 3. 残ったエラーを手動修正

自動修正後に残るのは主に：

| ルール | 意味 | 対処 |
|--------|------|------|
| `E501` | 行が長すぎる | 引数を複数行に分ける |
| `F401` | 未使用 import | import 行を削除する |
| `F841` | 未使用変数 | 変数を削除または `_` に置き換える |

修正後に再度 `uv run ruff check .` でゼロを確認する。

### 4. テストが通ることを確認

```bash
uv run pytest
```

lint 修正でロジックが壊れていないことを確認して完了。

## よくあるエラーと対処

### import の順番（I001）

```python
# before
from dataclasses import dataclass
import subprocess
from shared.errors import FfmpegExecutionError

# after（ruff --fix で自動修正される）
import subprocess
from dataclasses import dataclass
from shared.errors import FfmpegExecutionError
```

### 行が長すぎる（E501）

```python
# before
result = some_function(very_long_argument_one, very_long_argument_two, very_long_argument_three)

# after
result = some_function(
    very_long_argument_one,
    very_long_argument_two,
    very_long_argument_three,
)
```
