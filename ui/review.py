from typing import Sequence

from ui.prompts import ask_menu


def ask_review_action() -> str:
    return ask_menu(
        "次にどうしますか？",
        [
            ("この内容で実行する", "execute"),
            ("ドライランする（実行しない）", "dry_run"),
            ("最初からやり直す", "restart"),
            ("特定項目を修正する", "edit"),
            ("中止する", "cancel"),
        ],
    )


def ask_field_to_edit(fields: Sequence[tuple[str, str]]) -> str:
    return ask_menu(
        "修正したい項目を選んでください",
        list(fields),
    )
