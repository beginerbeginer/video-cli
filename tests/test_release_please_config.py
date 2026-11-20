"""release-please の設定が、CLAUDE.md の「リリースのルール」とずれていないかを確かめる。"""

import json
import re
import unittest
from pathlib import Path

from scripts.conventional_commits import ALLOWED_TYPES

ROOT = Path(__file__).resolve().parent.parent


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


if __name__ == "__main__":
    unittest.main()
