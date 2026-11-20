"""release-please の設定が、CLAUDE.md の「リリースのルール」とずれていないかを確かめる。"""

import json
import re
import subprocess
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

    # release-please を入れる前（2026-05-22）に手で作ったタグ。
    # Why not git のタグだけを見る: CI の actions/checkout は既定でタグを取ってこないので、
    # タグが無いクローンでもこの下限で確かめられるよう、ここに書いておく
    MANUAL_RELEASE_TAGS = ("v0.2.0", "v0.3.0")

    @staticmethod
    def parse_version(text: str) -> tuple[int, ...]:
        return tuple(int(part) for part in text.removeprefix("v").split("."))

    @staticmethod
    def git_release_tags() -> list[str]:
        try:
            result = subprocess.run(
                ["git", "tag", "--list", "v[0-9]*"], cwd=ROOT, capture_output=True, text=True, check=True
            )
        except (OSError, subprocess.CalledProcessError):
            return []
        return [tag for tag in result.stdout.split() if re.fullmatch(r"v\d+\.\d+\.\d+", tag)]

    def manifest_version(self) -> str:
        return load_json(".release-please-manifest.json")["."]

    def test_manifestのバージョンがpyprojectと同じ(self):
        # Why not tomllib: requires-python が 3.10 からで、tomllib は 3.11 から
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE).group(1)

        self.assertEqual(self.manifest_version(), version)

    def test_manifestのバージョンがuvのロックファイルと同じ(self):
        lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
        version = re.search(r'^name = "video-cli"\nversion = "([^"]+)"$', lock, re.MULTILINE).group(1)

        self.assertEqual(self.manifest_version(), version)

    def test_manifestのバージョンは既存のタグより小さくならない(self):
        # Why not 小さくてもよい: release-please はマニフェストの次の版を出すので、
        # 既存のタグより古い番号だと、すでにあるタグと同じ番号を作ろうとして失敗する
        tags = [*self.MANUAL_RELEASE_TAGS, *self.git_release_tags()]
        latest_tag = max(tags, key=self.parse_version)

        self.assertGreaterEqual(self.parse_version(self.manifest_version()), self.parse_version(latest_tag))

    def test_CHANGELOGには手で作ったタグと同じかそれより古い版を載せない(self):
        # Why not 載せてもよい: 手で作ったタグの版は release-please が出したものではないので、
        # CHANGELOG にあると、その版を release-please が出したことになってしまう
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        versions = re.findall(r"^##? \[(\d+\.\d+\.\d+)\]", changelog, re.MULTILINE)
        floor = max(self.parse_version(tag) for tag in self.MANUAL_RELEASE_TAGS)

        self.assertEqual([v for v in versions if self.parse_version(v) <= floor], [])

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
