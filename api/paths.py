import os
from pathlib import Path

ROOT_ENV = "VIDEO_GUI_ROOT"


def get_allowed_root() -> Path:
    # Why not 空文字を許す: VIDEO_GUI_ROOT="" で Path("") がカレントディレクトリになり、範囲が気付かず変わる。
    configured = os.environ.get(ROOT_ENV)
    return Path(configured or Path.home()).resolve()


def is_within_root(path: str | os.PathLike, root: str | os.PathLike | None = None) -> bool:
    # Why not 文字列の startswith: "/home/me-evil" が "/home/me" の中と判定され、".." も見抜けない。
    # Why not resolve しない比較: シンボリックリンクで範囲の外の実体を指されると通ってしまう。
    allowed_root = Path(root).resolve() if root is not None else get_allowed_root()
    return Path(path).resolve().is_relative_to(allowed_root)
