from pathlib import Path

from shared.errors import ValidationError

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def validate_input_file_exists(file_path: str) -> None:
    raw = Path(file_path)
    if raw.is_symlink():
        raise ValidationError(f"シンボリックリンクは使用できません: {file_path}")
    path = raw.resolve()
    if not path.exists():
        raise ValidationError(f"入力ファイルが見つかりません: {file_path}")
    if not path.is_file():
        raise ValidationError(f"ファイルではありません: {file_path}")


def validate_video_file_extension(file_path: str) -> None:
    ext = Path(file_path).suffix.lower()
    if ext not in SUPPORTED_VIDEO_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_VIDEO_EXTENSIONS))
        raise ValidationError(
            f"対応していない動画拡張子です: {ext}\n対応形式: {supported}"
        )


def validate_output_directory_exists(file_path: str) -> None:
    raw = Path(file_path)
    raw_parent = raw.parent if str(raw.parent) != "" else Path(".")
    if raw_parent.is_symlink():
        raise ValidationError(f"シンボリックリンクは使用できません: {raw_parent}")
    parent = raw_parent.resolve()
    if not parent.exists():
        raise ValidationError(f"出力先ディレクトリが存在しません: {parent}")
    if not parent.is_dir():
        raise ValidationError(f"出力先ディレクトリではありません: {parent}")
