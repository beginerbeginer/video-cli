import json
import shutil
import subprocess

from domain.media_info import MediaInfo
from ffmpeg.probe_parser import build_media_info
from shared.errors import ValidationError


def ensure_ffmpeg_installed() -> None:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise ValidationError(
            "ffmpeg が見つかりません。事前に ffmpeg をインストールし、PATH が通っている状態にしてください。"
        )


def ensure_ffprobe_installed() -> None:
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path is None:
        raise ValidationError(
            "ffprobe が見つかりません。事前に ffprobe をインストールし、PATH が通っている状態にしてください。"
        )


def run_ffprobe(file_path: str) -> dict:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ValidationError(
            f"ffprobe でメディア情報を取得できませんでした: {file_path}"
        ) from exc

    return json.loads(result.stdout)


def probe_media_info(file_path: str) -> MediaInfo:
    return build_media_info(file_path, run_ffprobe(file_path))
