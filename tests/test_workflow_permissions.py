import re
import unittest
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"

# Why not PyYAML: 標準ライブラリだけで済ませる方針のため。
# 確かめたいのはトップレベルの permissions とジョブごとの区切りだけなので、インデントで切り分ければ足りる。
_TOP_LEVEL_KEY_RE = re.compile(r"^([^\s#][^:\n]*):", re.MULTILINE)
_JOB_KEY_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$", re.MULTILINE)


def _top_level_block(text: str, key: str) -> str:
    matches = list(_TOP_LEVEL_KEY_RE.finditer(text))
    for i, match in enumerate(matches):
        if match.group(1) == key:
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[match.start() : end]
    raise AssertionError(f"トップレベルに {key} がありません")


def _jobs(text: str) -> dict[str, str]:
    block = _top_level_block(text, "jobs")
    matches = list(_JOB_KEY_RE.finditer(block))
    return {
        m.group(1): block[m.start() : matches[i + 1].start() if i + 1 < len(matches) else len(block)]
        for i, m in enumerate(matches)
    }


class TestSyncLabelsPermissions(unittest.TestCase):
    """PR のコードが書き込みのトークンで動かないことを固定する。"""

    def setUp(self):
        self.text = (WORKFLOWS_DIR / "sync-labels.yml").read_text(encoding="utf-8")
        self.jobs = _jobs(self.text)

    def test_トップレベルでは書き込みの権限を与えない(self):
        self.assertNotIn("write", _top_level_block(self.text, "permissions"))

    def test_dry_runのジョブはPRでだけ動き書き込みの権限を持たない(self):
        (check,) = [job for job in self.jobs.values() if "--dry-run" in job]

        self.assertIn("github.event_name == 'pull_request'", check)
        self.assertIn("contents: read", check)
        self.assertNotIn("write", check)

    def test_書き込むジョブはPRでは動かない(self):
        (sync,) = [job for job in self.jobs.values() if "issues: write" in job]

        self.assertIn("github.event_name != 'pull_request'", sync)
        self.assertNotIn("--dry-run", sync)


class TestTestWorkflowPermissions(unittest.TestCase):
    def test_読み取りの権限だけを明記する(self):
        text = (WORKFLOWS_DIR / "test.yml").read_text(encoding="utf-8")

        permissions = _top_level_block(text, "permissions")

        self.assertIn("contents: read", permissions)
        self.assertNotIn("write", permissions)


if __name__ == "__main__":
    unittest.main()
