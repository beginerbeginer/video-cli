"""release-please の設定が、CLAUDE.md の「リリースのルール」とずれていないかを確かめる。"""

import json
import re
import unittest
from pathlib import Path

from scripts.conventional_commits import ALLOWED_TYPES

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
RELEASE_WORKFLOW = WORKFLOWS_DIR / "release-please.yml"


def load_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class TestReleasePleaseConfig(unittest.TestCase):
    def setUp(self):
        self.config = load_json("release-please-config.json")
        self.package = self.config["packages"]["."]

    def test_manifestのバージョンがpyprojectと同じ(self):
        manifest = load_json(".release-please-manifest.json")
        # Why not tomllib: requires-python が 3.10 からで、tomllib は 3.11 から
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE).group(1)

        self.assertEqual(manifest["."], version)

    def test_出発点のコミットを指定している(self):
        self.assertRegex(self.config["bootstrap-sha"], r"^[0-9a-f]{40}$")

    def test_0x系では互換性を壊す変更でもマイナーを上げる(self):
        self.assertTrue(self.config["bump-minor-pre-major"])
        self.assertFalse(self.config.get("bump-patch-for-minor-pre-major", False))

    def test_pythonのリリース種別でタグにvを付けコンポーネント名を付けない(self):
        self.assertEqual(self.package["release-type"], "python")
        self.assertFalse(self.config["include-component-in-tag"])
        self.assertTrue(self.config.get("include-v-in-tag", True))

    def test_uvのロックファイルのバージョンも書き換える(self):
        # Why not 書き換えない: pyproject.toml だけ上がると uv.lock の video-cli のバージョンが古いまま残る
        extra = [f for f in self.package["extra-files"] if f["path"] == "uv.lock"]

        self.assertEqual(
            extra,
            [{"type": "toml", "path": "uv.lock", "jsonpath": "$.package[?(@.name.value==='video-cli')].version"}],
        )

    def test_CHANGELOGに載る種類は新機能と不具合の修正と性能の改善だけ(self):
        sections = self.config["changelog-sections"]
        visible = {s["type"]: s["section"] for s in sections if not s.get("hidden", False)}

        self.assertEqual(visible, {"feat": "新機能", "fix": "不具合の修正", "perf": "性能の改善"})

    def test_CHANGELOGの種類は確認スクリプトの種類と一致する(self):
        types = {s["type"] for s in self.config["changelog-sections"]}

        self.assertEqual(types, set(ALLOWED_TYPES))



def _on_block(text: str) -> str:
    # Why not PyYAML: 標準ライブラリだけで済ませる方針のため。トップレベルの on: の中身だけ切り出せれば足りる
    match = re.search(r"^on:\n((?:[ #].*\n|\n)*)", text, re.MULTILINE)
    return match.group(1)


def _runs_on_pull_request(text: str) -> bool:
    return re.search(r"^  pull_request(_target)?:", _on_block(text), re.MULTILINE) is not None


class TestReleasePleaseWorkflow(unittest.TestCase):
    """リリース用の PR で CI が動くよう専用のトークンを使い、そのトークンが PR に渡らないことを固定する。"""

    def setUp(self):
        self.text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.workflows = {p.name: p.read_text(encoding="utf-8") for p in sorted(WORKFLOWS_DIR.glob("*.yml"))}

    def test_専用のトークンを使い無ければGITHUB_TOKENに戻る(self):
        # Why not secrets.RELEASE_PLEASE_TOKEN だけ: Secret が未登録だと空になり、release-please が動かなくなる
        tokens = re.findall(r"^\s+token:\s*(.+)$", self.text, re.MULTILINE)

        self.assertEqual(tokens, ["${{ secrets.RELEASE_PLEASE_TOKEN || github.token }}"])

    def test_mainへのpushと手動実行でだけ動く(self):
        on = _on_block(self.text)

        self.assertRegex(on, r"(?m)^  push:\n    branches: \[main\]$")
        self.assertRegex(on, r"(?m)^  workflow_dispatch:")
        self.assertFalse(_runs_on_pull_request(self.text))

    def test_GITHUB_TOKENの権限は今のまま必要な分だけ(self):
        permissions = re.search(r"^permissions:\n((?:  .*\n)+)", self.text, re.MULTILINE).group(1)

        self.assertEqual(
            permissions.split(),
            ["contents:", "write", "issues:", "write", "pull-requests:", "write"],
        )

    def test_専用のトークンはrelease_pleaseのワークフローでだけ使う(self):
        users = [name for name, text in self.workflows.items() if "RELEASE_PLEASE_TOKEN" in text]

        self.assertEqual(users, ["release-please.yml"])

    def test_PRで動くワークフローにはSecretを渡さない(self):
        # Why not RELEASE_PLEASE_TOKEN だけを見る: 外部からの PR でほかの Secret が読まれるのも防ぎたい
        on_pr = {name: text for name, text in self.workflows.items() if _runs_on_pull_request(text)}

        self.assertIn("test.yml", on_pr)
        for name, text in on_pr.items():
            with self.subTest(workflow=name):
                self.assertNotIn("secrets.", text)


if __name__ == "__main__":
    unittest.main()
