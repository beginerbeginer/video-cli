"""`.github/labels.json` の定義を、GitHub のラベルに反映する。

使い方: python scripts/sync_labels.py <定義ファイル> [--dry-run]
--dry-run のときは、実行する gh コマンドを表示するだけで GitHub には書き込まない。
"""

import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# GitHub がラベルの説明に課している上限
MAX_DESCRIPTION_LENGTH = 100

_COLOR_RE = re.compile(r"^[0-9a-fA-F]{6}$")
_REQUIRED_KEYS = ("name", "color", "description")


class LabelDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class Label:
    name: str
    color: str
    description: str


def _parse_label(raw: dict) -> Label:
    missing = [key for key in _REQUIRED_KEYS if key not in raw]
    if missing:
        raise LabelDefinitionError(f"{raw!r} に {', '.join(missing)} がありません")
    name = raw["name"].strip()
    color = raw["color"].lstrip("#")
    description = raw["description"]
    if not name:
        raise LabelDefinitionError("名前が空のラベルがあります")
    if not _COLOR_RE.match(color):
        raise LabelDefinitionError(f"{name}: 色 {raw['color']!r} は 6 桁の 16 進数ではありません")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise LabelDefinitionError(f"{name}: 説明が {MAX_DESCRIPTION_LENGTH} 文字を超えています")
    return Label(name=name, color=color, description=description)


def parse_labels(raw_labels: list[dict]) -> list[Label]:
    labels = [_parse_label(raw) for raw in raw_labels]
    names = [label.name for label in labels]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise LabelDefinitionError(f"名前が重複しています: {', '.join(duplicates)}")
    return labels


def load_labels(path: Path) -> list[Label]:
    return parse_labels(json.loads(Path(path).read_text(encoding="utf-8")))


def build_gh_commands(labels: list[Label]) -> list[list[str]]:
    # Why not 定義に無いラベルの削除: `bug` など GitHub が用意したラベルや、
    # 定義ファイルに入れる前の試しのラベルまで消え、付いている issue から外れてしまう。
    # Why not REST API を直接呼ぶ: `--force` で「無ければ作る・あれば更新」を 1 回で済ませられ、
    # 既存ラベルの一覧を取って差分を出す処理が要らない。
    return [
        ["gh", "label", "create", label.name, "--color", label.color, "--description", label.description, "--force"]
        for label in labels
    ]


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    (path,) = [arg for arg in argv if arg != "--dry-run"]
    for command in build_gh_commands(load_labels(Path(path))):
        print(shlex.join(command))
        if not dry_run:
            subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
