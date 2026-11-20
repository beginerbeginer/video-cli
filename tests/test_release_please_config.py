"""release-please の設定が、CLAUDE.md の「リリースのルール」とずれていないかを確かめる。"""

import json
import re
import subprocess
import unittest
from pathlib import Path

from scripts.conventional_commits import ALLOWED_TYPES

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
RELEASE_WORKFLOW = WORKFLOWS_DIR / "release-please.yml"


def load_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def _on_block(text: str) -> str:
    # Why not PyYAML: 標準ライブラリだけで済ませる方針のため。トップレベルの on: の中身だけ切り出せれば足りる
    match = re.search(r"^on:\n((?:[ #].*\n|\n)*)", text, re.MULTILINE)
    return match.group(1)


def _runs_on_pull_request(text: str) -> bool:
    return re.search(r"^  pull_request(_target)?:", _on_block(text), re.MULTILINE) is not None


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

    def test_CHANGELOGの大見出しは先頭の1つだけ(self):
        # Why not 気にしない: 版の項目が 1 つも無い CHANGELOG に release-please が初めて書き込むと、
        # 元の `# Changelog` を 1 段下げた `## Changelog` を末尾に残す（v0.4.0 で起きた）。
        # 版の見出しと同じ段に紛れ込むので、残っていたら気づけるようにする
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        headings = re.findall(r"^#{1,2} (?!\[\d)(.+)$", changelog, re.MULTILINE)

        self.assertEqual(headings, ["Changelog"])
        self.assertTrue(changelog.startswith("# Changelog\n"))

    def test_CHANGELOGの同じ版に同じ項目を2回載せない(self):
        # Why not 重複を許す: マージコミットでマージしていた頃は、マージコミット（本文が PR のタイトル）と
        # 元のコミットの両方を release-please が数え、同じ項目が 2 回ずつ載った（issue #127）
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        for release in re.split(r"^## \[", changelog, flags=re.MULTILINE)[1:]:
            version = release.split("]", 1)[0]
            # 項目の文はリンクの前まで。コミットのハッシュは項目ごとに違うので比べない
            entries = re.findall(r"^\* (.+?) \(\[", release, re.MULTILINE)
            duplicates = sorted({e for e in entries if entries.count(e) > 1})
            with self.subTest(version=version):
                self.assertEqual(duplicates, [])

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
