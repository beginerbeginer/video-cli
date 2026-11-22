"""CLAUDE.md と AGENTS.md のマージの手順が Squash and merge になっていることを固定する（issue #127）。"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Why not CLAUDE.md だけ: Codex は AGENTS.md を読むので、片方だけ直すと手順が食い違う
DOCS = ("CLAUDE.md", "AGENTS.md")


def _procedure(text: str) -> str:
    match = re.search(r"^## 新機能追加の手順.*?\n```\n(.*?)```", text, re.MULTILINE | re.DOTALL)
    return match.group(1)


class TestMergeMethodDocs(unittest.TestCase):
    def test_新機能追加の手順はSquashでマージしブランチを消す(self):
        for name in DOCS:
            with self.subTest(doc=name):
                procedure = _procedure((ROOT / name).read_text(encoding="utf-8"))

                self.assertIn("gh pr merge N --squash --delete-branch", procedure)

    def test_新機能追加の手順にマージコミットでマージする指示を残さない(self):
        # Why not gh pm を残す: 既定の gh pm（gh pr merge）はマージ方法を聞くか、マージコミットでマージする
        for name in DOCS:
            with self.subTest(doc=name):
                procedure = _procedure((ROOT / name).read_text(encoding="utf-8"))

                self.assertNotIn("gh pm", procedure)
                self.assertNotIn("--merge", procedure)


if __name__ == "__main__":
    unittest.main()
