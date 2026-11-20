import unittest

from scripts.pr_ai_attribution import (
    END_MARKER,
    START_MARKER,
    build_new_body,
    extract_coauthors,
    render_section,
    replace_section,
)

CLAUDE_COMMIT = """feat: 何かを追加する

理由を書く。

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_xxx
"""

CODEX_COMMIT = """fix: 何かを直す

co-authored-by: Codex (gpt-5.5) <noreply@openai.com>
"""

HUMAN_ONLY_COMMIT = """docs: README を直す

人が書いたコミット。
"""


class TestExtractCoauthors(unittest.TestCase):
    def test_トレーラーの名前部分だけを取り出す(self):
        result = extract_coauthors([CLAUDE_COMMIT])

        self.assertEqual(result.counts, {"Claude Opus 5.5": 1})

    def test_大文字小文字が違うトレーラーも拾う(self):
        result = extract_coauthors([CODEX_COMMIT])

        self.assertEqual(result.counts, {"Codex (gpt-5.5)": 1})

    def test_同じツールは件数をまとめ最初に出た順を保つ(self):
        result = extract_coauthors([CODEX_COMMIT, CLAUDE_COMMIT, CODEX_COMMIT])

        self.assertEqual(list(result.counts.items()), [("Codex (gpt-5.5)", 2), ("Claude Opus 5.5", 1)])

    def test_トレーラーの無いコミットを数える(self):
        result = extract_coauthors([CLAUDE_COMMIT, HUMAN_ONLY_COMMIT])

        self.assertEqual(result.commits_without_trailer, 1)

    def test_1コミットに同じトレーラーが重複しても1件と数える(self):
        message = CLAUDE_COMMIT + "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"

        result = extract_coauthors([message])

        self.assertEqual(result.counts, {"Claude Opus 5.5": 1})

    def test_空のメッセージは無視する(self):
        result = extract_coauthors(["", "\n", CLAUDE_COMMIT])

        self.assertEqual(result.commits_without_trailer, 0)


class TestRenderSection(unittest.TestCase):
    def test_マーカーで囲まれツールと件数が並ぶ(self):
        section = render_section(extract_coauthors([CLAUDE_COMMIT, CLAUDE_COMMIT]))

        self.assertTrue(section.startswith(START_MARKER))
        self.assertTrue(section.endswith(END_MARKER))
        self.assertIn("- Claude Opus 5.5（2 コミット）", section)

    def test_トレーラーが1つも無ければその旨を書く(self):
        section = render_section(extract_coauthors([HUMAN_ONLY_COMMIT]))

        self.assertIn("`Co-Authored-By` トレーラーがありません", section)

    def test_トレーラーの無いコミットがあれば件数を書く(self):
        section = render_section(extract_coauthors([CLAUDE_COMMIT, HUMAN_ONLY_COMMIT]))

        self.assertIn("トレーラーの無いコミット: 1 件", section)

    def test_全コミットにトレーラーがあれば無いコミットの行は出さない(self):
        section = render_section(extract_coauthors([CLAUDE_COMMIT]))

        self.assertNotIn("トレーラーの無いコミット", section)


class TestReplaceSection(unittest.TestCase):
    def test_マーカーの間だけを書き換える(self):
        body = f"## 概要\n本文\n\n{START_MARKER}\n古い内容\n{END_MARKER}\n\n末尾"

        result = replace_section(body, f"{START_MARKER}\n新しい内容\n{END_MARKER}")

        self.assertEqual(result, f"## 概要\n本文\n\n{START_MARKER}\n新しい内容\n{END_MARKER}\n\n末尾")

    def test_文中で引用されたマーカーは区画とみなさない(self):
        quoted = f"区画は `{START_MARKER}`〜`{END_MARKER}` に書く"
        body = f"{quoted}\n\n{START_MARKER}\n{END_MARKER}\n"

        result = replace_section(body, f"{START_MARKER}\n新しい内容\n{END_MARKER}")

        self.assertEqual(result, f"{quoted}\n\n{START_MARKER}\n新しい内容\n{END_MARKER}\n")

    def test_文中で引用されたマーカーしか無ければ末尾に追記する(self):
        body = f"区画は `{START_MARKER}`〜`{END_MARKER}` に書く"

        result = replace_section(body, "SECTION")

        self.assertEqual(result, f"{body}\n\nSECTION\n")

    def test_GitHubのWeb編集で入るCRLFの本文でも区画を見つける(self):
        body = f"本文\r\n\r\n{START_MARKER}\r\n古い内容\r\n{END_MARKER}\r\n"

        result = replace_section(body, "SECTION")

        self.assertEqual(result, "本文\r\n\r\nSECTION\r\n")

    def test_マーカーが無ければ末尾に追記する(self):
        result = replace_section("本文\n", "SECTION")

        self.assertEqual(result, "本文\n\nSECTION\n")

    def test_本文が空ならセクションだけになる(self):
        result = replace_section("", "SECTION")

        self.assertEqual(result, "SECTION\n")

    def test_何度書き換えてもセクションは1つだけ(self):
        once = replace_section("本文", render_section(extract_coauthors([CLAUDE_COMMIT])))

        twice = replace_section(once, render_section(extract_coauthors([CODEX_COMMIT])))

        self.assertEqual(twice.count(START_MARKER), 1)
        self.assertIn("Codex (gpt-5.5)", twice)
        self.assertNotIn("Claude Opus 5.5", twice)


class TestBuildNewBody(unittest.TestCase):
    def test_NUL区切りのgit_logからPR本文を組み立てる(self):
        git_log = "\0".join([CLAUDE_COMMIT, HUMAN_ONLY_COMMIT]) + "\0"

        result = build_new_body(git_log, "本文")

        self.assertIn("- Claude Opus 5.5（1 コミット）", result)
        self.assertIn("トレーラーの無いコミット: 1 件", result)
        self.assertTrue(result.startswith("本文"))
