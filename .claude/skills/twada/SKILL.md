---
name: twada
description: t_wada スタイルの TDD でコードを書く。テストを先に書き、Red→Green→Refactor サイクルで進む。リファクタリングの設計判断も t_wada の考え方に従う。
allowed-tools: Bash(uv run pytest *) Bash(uv run pytest)
---

# t_wada スタイル TDD

## 基本原則

**if を減らしたいのであって、抽象クラスを増やしたいわけではない。**

リファクタリングの判断基準は常に「読みやすくなるか」と「責務が明確になるか」。
パターンを適用することが目的にならないこと。

---

## サイクル

### Red → Green → Refactor

1. **Red**：まず失敗するテストを書く
   - テスト名は「何をすると何になるか」を日本語で表現する
   - 実装を想像しながら、使いやすいインターフェースを先に決める
   - `uv run pytest` を実行して red を確認する

2. **Green**：テストを通す最小限のコードを書く
   - 美しさより動くことを優先する
   - ベタ書きでよい。抽象化は後で行う
   - `uv run pytest` を実行して green を確認する

3. **Refactor**：green を保ちながら設計を改善する
   - **必ず green の状態でのみリファクタリングする**
   - `uv run pytest` を小刻みに実行して green を維持する
   - リファクタリング後も `uv run pytest` で確認する

---

## テストの書き方

### 構造（AAA パターン）

```python
def test_何をすると何になるか(self):
    # Arrange（準備）
    form = ConcatForm(...)

    # Act（実行）
    result = handle_concat_review(form)

    # Assert（確認）
    self.assertEqual(result.kind, "done")
```

### 命名規則

- `test_cancelを選ぶとdoneが返る`
- `test_ValidationErrorが起きるとretryで戻る`
- 「何をテストしているか」が名前だけで分かるように書く

### モックの使い方

- UI（`ask_review_action` など）は mock する。I/O の境界だから
- ビジネスロジックは mock しない。実際の動作を確認する
- `patch` は最小スコープで使う

### Characterization Test

既存コードを変更する前に、**今の振る舞いを固定するテストを先に書く**。
リファクタリング前の安全網として機能する。

---

## 設計パターンの選び方

### Dictionary Dispatch を選ぶとき

分岐の本質が「action → 処理の対応表」のとき。
`handle_*_review` のような action → FlowResult 変換がこれにあたる。

```python
HANDLERS = {
    "cancel": to_done,
    "restart": to_retry,
    "execute": to_execute,
}
result = HANDLERS[action](form)
```

### Strategy を選ぶとき

「差し替え可能なアルゴリズム」が必要なとき。
`concat_strategy` の copy / reencode 切り替えがこれにあたる。

### ガード節 + 小関数分割を選ぶとき

「フロー制御」のとき。orchestration 関数の if はここに属する。

```python
def run_iteration(form):
    review_result = handle_review(form)
    if should_return_immediately(review_result):
        return review_result
    return execute_reviewed(review_result)
```

### 使わないもの

- 3関数全部を Strategy 化（class が増えるだけ）
- OO 化のための OO 化
- 状態遷移パターン（フロー制御には重い）

---

## 進め方のルール

1. **一度に一つのことだけ変える**。テストを書く or 実装する or リファクタリングする
2. **ABC サイズを意識する**。目安は 9 以下。大きくなったら小関数に分割する
3. **既存の振る舞いを壊さない**。テストが green であり続けることが証明
4. **コメントには Why not を書く**。Why（なぜそうしたか）ではなく Why not（他の選択肢を選ばなかった理由）

---

## このプロジェクトのコンテキスト

- テストランナー: `uv run pytest`
- 設計: Dictionary Dispatch（review actions）+ Strategy（concat strategy）+ ガード節（iteration flows）
- `FlowResult(kind, form)` でフローの状態を表現する
- `REVIEW_ACTION_HANDLERS` は `build_review_action_handlers()` で生成する
