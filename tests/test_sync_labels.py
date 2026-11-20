import json
import re
import unittest
from pathlib import Path

from scripts.sync_labels import (
    LabelDefinitionError,
    build_gh_commands,
    load_labels,
    parse_labels,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
LABELS_PATH = REPO_ROOT / ".github" / "labels.json"
LABELER_PATH = REPO_ROOT / ".github" / "labeler.yml"

# issue #110 で決めたラベル。すでに issue と PR に付いているので、名前を変えると付け替えが要る
EXPECTED_NAMES = {
    "feat",
    "infra",
    "まとめ",
    "GUI刷新",
    "領域:CLI",
    "領域:ロジック",
    "領域:FFmpeg",
    "領域:API",
    "領域:フロント",
    "領域:開発環境",
}


def _label(name="feat", color="1D76DB", description="新しい機能を追加する"):
    return {"name": name, "color": color, "description": description}


class TestParseLabels(unittest.TestCase):
    def test_名前と色と説明を取り出す(self):
        labels = parse_labels([_label()])

        self.assertEqual(labels[0].name, "feat")
        self.assertEqual(labels[0].color, "1D76DB")
        self.assertEqual(labels[0].description, "新しい機能を追加する")

    def test_色の先頭のシャープは取り除く(self):
        labels = parse_labels([_label(color="#1d76db")])

        self.assertEqual(labels[0].color, "1d76db")

    def test_色が6桁の16進数でなければエラーになる(self):
        with self.assertRaises(LabelDefinitionError):
            parse_labels([_label(color="blue")])

    def test_説明が100文字を超えるとエラーになる(self):
        with self.assertRaises(LabelDefinitionError):
            parse_labels([_label(description="あ" * 101)])

    def test_説明がちょうど100文字なら通る(self):
        labels = parse_labels([_label(description="あ" * 100)])

        self.assertEqual(len(labels[0].description), 100)

    def test_名前が重複するとエラーになる(self):
        with self.assertRaises(LabelDefinitionError):
            parse_labels([_label(), _label(color="000000")])

    def test_名前が空だとエラーになる(self):
        with self.assertRaises(LabelDefinitionError):
            parse_labels([_label(name=" ")])

    def test_必須の項目が欠けているとエラーになる(self):
        with self.assertRaises(LabelDefinitionError):
            parse_labels([{"name": "feat", "color": "1D76DB"}])


class TestBuildGhCommands(unittest.TestCase):
    def test_ラベルごとにforce付きのgh_label_createを作る(self):
        commands = build_gh_commands(parse_labels([_label()]))

        expected = ["gh", "label", "create", "feat", "--color", "1D76DB", "--description", "新しい機能を追加する"]
        self.assertEqual(commands, [expected + ["--force"]])

    def test_定義に無いラベルを消すコマンドは作らない(self):
        commands = build_gh_commands(parse_labels([_label(), _label(name="infra")]))

        self.assertTrue(all(command[:3] == ["gh", "label", "create"] for command in commands))


class TestLabelsFile(unittest.TestCase):
    """リポジトリに置いた定義ファイルそのものを確かめる。壊れたまま main に入ると同期が止まるため。"""

    def test_定義ファイルが検証を通る(self):
        load_labels(LABELS_PATH)

    def test_issue110で決めたラベルがそろっている(self):
        names = {label.name for label in load_labels(LABELS_PATH)}

        self.assertEqual(names, EXPECTED_NAMES)

    def test_領域のラベルは同じ色にそろえる(self):
        colors = {label.color.lower() for label in load_labels(LABELS_PATH) if label.name.startswith("領域:")}

        self.assertEqual(len(colors), 1)

    def test_定義ファイルはJSONの配列である(self):
        self.assertIsInstance(json.loads(LABELS_PATH.read_text(encoding="utf-8")), list)


class TestLabelerConfig(unittest.TestCase):
    """actions/labeler の設定が、定義済みの領域ラベルとずれないことを確かめる。"""

    # Why not PyYAML: 実行時もテスト時も標準ライブラリだけで済ませる方針のため。
    # 確かめたいのはトップレベルのキー（ラベル名）だけなので、行単位で読めば足りる。
    # ラベル名に `:` を含むので、キーはシングルクォートで書く決まりにする。
    _QUOTED_KEY_RE = re.compile(r"^'([^']+)':\s*$")

    def _top_level_lines(self):
        lines = LABELER_PATH.read_text(encoding="utf-8").splitlines()
        return [line for line in lines if line.strip() and not line[0].isspace() and not line.startswith("#")]

    def _labeler_labels(self):
        return {self._QUOTED_KEY_RE.match(line).group(1) for line in self._top_level_lines()}

    def test_トップレベルのキーはすべてクォートされている(self):
        self.assertTrue(all(self._QUOTED_KEY_RE.match(line) for line in self._top_level_lines()))

    def test_自動で付けるのは領域のラベルだけ(self):
        self.assertTrue(all(name.startswith("領域:") for name in self._labeler_labels()))

    def test_すべての領域ラベルにパスが割り当てられている(self):
        area_names = {name for name in EXPECTED_NAMES if name.startswith("領域:")}

        self.assertEqual(self._labeler_labels(), area_names)


if __name__ == "__main__":
    unittest.main()
