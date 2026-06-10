from collections.abc import Sequence
from typing import Protocol


class UIPort(Protocol):
    def ask_text(self, message: str, default: str | None = None) -> str: ...

    def ask_menu(self, message: str, choices: Sequence[tuple[str, str]]) -> str: ...
