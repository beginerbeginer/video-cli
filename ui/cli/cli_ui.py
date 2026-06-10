from collections.abc import Sequence

from ui.cli.prompts import ask_menu, ask_text


class CliUI:
    def ask_text(self, message: str, default: str | None = None) -> str:
        return ask_text(message, default)

    def ask_menu(self, message: str, choices: Sequence[tuple[str, str]]) -> str:
        return ask_menu(message, choices)
