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
    try:
        resolve_within_root(path, root)
    except PathOutsideRootError:
        return False
    return True


class PathOutsideRootError(Exception):
    # Why not メッセージにパスを入れる: 範囲の外にどんなパスがあるかを、レスポンス経由で教えてしまう。
    def __init__(self) -> None:
        super().__init__("参照できる範囲の外のパスです。")


def resolve_within_root(path: str | os.PathLike, root: str | os.PathLike | None = None) -> Path:
    # Why not is_within_root で判定してから呼び出し側で resolve し直す: 2 回の resolve の間にリンクを
    # 張り替えられると、判定したパスと実際に使うパスがずれる。判定に使ったパスをそのまま返す。
    allowed_root = Path(root).resolve() if root is not None else get_allowed_root()
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(allowed_root):
        raise PathOutsideRootError()
    return resolved
