from domain import operations
from ui.prompts import ask_menu


def prompt_main_menu() -> str:
    return ask_menu(
        "何をしたいですか？",
        [
            ("動画を切り出す", operations.TRIM),
            ("動画を結合する", operations.CONCAT),
            ("動画サイズを変更する", operations.RESIZE),
            ("終了する", operations.EXIT),
        ],
    )
