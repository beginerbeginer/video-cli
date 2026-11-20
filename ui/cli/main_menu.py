from domain import operations
from ui.cli.prompts import ask_menu


def prompt_main_menu() -> str:
    return ask_menu(
        "何をしたいですか？",
        [(label, operation) for operation, label in operations.OPERATION_LABELS.items()],
    )
