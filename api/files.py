import stat
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from api.paths import PathOutsideRootError, get_allowed_root, is_within_root, resolve_within_root
from domain.media_info import MediaInfo
from ffmpeg.probe import ensure_ffprobe_installed, probe_media_info
from shared.errors import ValidationError
from validation.file_validators import SUPPORTED_VIDEO_EXTENSIONS, validate_input_file_exists

router = APIRouter(prefix="/api")

PATH_FIELD = "path"


class FsHome(BaseModel):
    path: str


class FsEntry(BaseModel):
    name: str
    path: str
    kind: Literal["dir", "file"]
    size: int | None
    modified: datetime
    is_video: bool


class FsList(BaseModel):
    path: str
    parent: str | None
    entries: list[FsEntry]


class ProbeRequest(BaseModel):
    path: str


@contextmanager
def _errors_for(field: str) -> Iterator[None]:
    # Why not 各 raise で field を渡す: validation/ の関数は field を知らないので、API の側で入力項目に結び付ける。
    try:
        yield
    except (ValidationError, PathOutsideRootError) as exc:
        if getattr(exc, "field", None) is None:
            exc.field = field
        raise


def _resolve_requested(raw: str) -> Path:
    # Why not 相対パスを許す: 解決の基準がサーバーのカレントディレクトリになり、起動場所で結果が変わる。
    if not Path(raw).is_absolute():
        raise ValidationError(f"絶対パスを指定してください: {raw}")
    return resolve_within_root(raw)


def _kind_of(mode: int) -> Literal["dir", "file"] | None:
    if stat.S_ISDIR(mode):
        return "dir"
    if stat.S_ISREG(mode):
        return "file"
    return None


def _to_entry(child: Path) -> FsEntry | None:
    # Why not シンボリックリンクをたどって表示する: 範囲の外の実体を指せるうえ、既存の validator も拒否する。
    if child.name.startswith(".") or child.is_symlink():
        return None
    try:
        st = child.stat()
    except OSError:
        return None
    kind = _kind_of(st.st_mode)
    if kind is None:
        return None
    return FsEntry(
        name=child.name,
        path=str(child),
        kind=kind,
        size=st.st_size if kind == "file" else None,
        modified=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
        is_video=kind == "file" and child.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS,
    )


def _list_entries(directory: Path) -> list[FsEntry]:
    if not directory.is_dir():
        raise ValidationError(f"ディレクトリではありません: {directory}")
    try:
        children = list(directory.iterdir())
    except OSError as exc:
        raise ValidationError(f"ディレクトリを読み取れません: {directory}") from exc
    entries = [entry for entry in map(_to_entry, children) if entry is not None]
    return sorted(entries, key=lambda e: (e.kind != "dir", e.name.casefold()))


@router.get("/fs/home")
def fs_home() -> FsHome:
    # Why not ホームをそのまま返す: VIDEO_GUI_ROOT でホームの外に範囲を変えると、最初の一覧が 403 になる。
    home = Path.home()
    return FsHome(path=str(home.resolve() if is_within_root(home) else get_allowed_root()))


@router.get("/fs/list")
def fs_list(path: str | None = None) -> FsList:
    root = get_allowed_root()
    with _errors_for(PATH_FIELD):
        directory = root if path is None else _resolve_requested(path)
        entries = _list_entries(directory)
    parent = None if directory == root else str(directory.parent)
    return FsList(path=str(directory), parent=parent, entries=entries)


@router.post("/probe")
def probe(request: ProbeRequest) -> MediaInfo:
    with _errors_for(PATH_FIELD):
        resolved = _resolve_requested(request.path)
        validate_input_file_exists(request.path)
    ensure_ffprobe_installed()
    with _errors_for(PATH_FIELD):
        return probe_media_info(str(resolved))
