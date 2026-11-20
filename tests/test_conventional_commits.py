import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.conventional_commits import check_commits, check_header, main


class TestCheckHeader(unittest.TestCase):
    def test_種類と日本語の要約なら問題なし(self):
        self.assertIsNone(check_header("feat: 動画の分割機能を追加する"))

    def test_スコープ付きでも問題なし(self):
        self.assertIsNone(check_header("chore(main): release 0.2.0"))

    def test_互換性を壊す印の感嘆符付きでも問題なし(self):
        self.assertIsNone(check_header("feat!: 設定ファイルの形式を変える"))

    def test_スコープと感嘆符の両方付きでも問題なし(self):
        self.assertIsNone(check_header("fix(ffmpeg)!: 出力先の既定を変える"))

    def test_決めた種類はすべて通る(self):
        for kind in ["feat", "fix", "perf", "refactor", "test", "docs", "ci", "build", "chore", "style", "revert"]:
            with self.subTest(kind=kind):
                self.assertIsNone(check_header(f"{kind}: 何かを変える"))

    def test_種類が無ければエラー(self):
        self.assertIsNotNone(check_header("動画圧縮機能を追加する"))

    def test_決めていない種類はエラー(self):
        error = check_header("ruff: import を整列する")

        self.assertIn("ruff", error)

    def test_種類が大文字だとエラー(self):
        self.assertIsNotNone(check_header("Feat: 何かを追加する"))

    def test_コロンの後に空白が無いとエラー(self):
        self.assertIsNotNone(check_header("feat:何かを追加する"))

    def test_要約が空だとエラー(self):
        self.assertIsNotNone(check_header("feat:   "))

    def test_空のスコープはエラー(self):
        self.assertIsNotNone(check_header("feat(): 何かを追加する"))

    def test_前後の空白は無視する(self):
        self.assertIsNone(check_header("  fix: 何かを直す \n"))


COMMITS_LOG = "\0".join(
    [
        "feat: 何かを追加する\n\n理由。\n",
        "ruff: import を整列する\n",
        "fix: 何かを直す\n",
        "",
    ]
)


class TestCheckCommits(unittest.TestCase):
    def test_形の違うコミットの1行目だけを返す(self):
        problems = check_commits(COMMITS_LOG)

        self.assertEqual([header for header, _ in problems], ["ruff: import を整列する"])

    def test_すべて正しければ空(self):
        self.assertEqual(check_commits("feat: a\n\0fix: b\n\0"), [])


class TestMain(unittest.TestCase):
    def run_main(self, argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(argv)
        return code, out.getvalue()

    def test_正しいタイトルなら終了コード0(self):
        code, _ = self.run_main(["title", "ci: PR タイトルを確かめる"])

        self.assertEqual(code, 0)

    def test_形の違うタイトルなら終了コード1でエラー注釈を出す(self):
        code, out = self.run_main(["title", "PR タイトルを確かめる"])

        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("::error"))

    def test_形の違うコミットがあっても終了コード0で警告注釈を出す(self):
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "commits.log"
            log.write_text(COMMITS_LOG, encoding="utf-8")

            code, out = self.run_main(["commits", str(log)])

        self.assertEqual(code, 0)
        self.assertIn("::warning", out)
        self.assertIn("ruff: import を整列する", out)

    def test_コミットがすべて正しければ注釈を出さない(self):
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "commits.log"
            log.write_text("feat: a\n\0", encoding="utf-8")

            code, out = self.run_main(["commits", str(log)])

        self.assertEqual(code, 0)
        self.assertNotIn("::warning", out)


if __name__ == "__main__":
    unittest.main()
