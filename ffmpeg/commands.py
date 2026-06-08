from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Generator

from domain.trim_range import TrimRange


def build_trim_command(
    input_file: str,
    output_file: str,
    trim_range: TrimRange,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-ss",
        str(trim_range.start_seconds),
        "-i",
        input_file,
        "-t",
        str(trim_range.duration_seconds),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_file,
    ]


def build_resize_command(
    input_file: str,
    output_file: str,
    width: int,
    height: int,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        f"scale={width}:{height}",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_file,
    ]


def build_atempo_filter(speed: float) -> str:
    filters = []
    s = speed
    while s > 2.0:
        filters.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        filters.append("atempo=0.5")
        s /= 0.5
    filters.append(f"atempo={s}")
    return ",".join(filters)


def build_speed_command(
    input_file: str,
    output_file: str,
    speed: float,
) -> list[str]:
    pts_factor = round(1.0 / speed, 10)
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        f"setpts={pts_factor}*PTS",
        "-filter:a",
        build_atempo_filter(speed),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_file,
    ]


def build_gif_command(
    input_file: str,
    output_file: str,
    fps: int,
    width: int,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        f"fps={fps},scale={width}:-1:flags=lanczos",
        output_file,
    ]


def build_thumbnail_command(
    input_file: str,
    output_file: str,
    timestamp_seconds: int,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-ss",
        str(timestamp_seconds),
        "-i",
        input_file,
        "-vframes",
        "1",
        output_file,
    ]


def build_convert_command(input_file: str, output_file: str) -> list[str]:
    return ["ffmpeg", "-y", "-i", input_file, "-c", "copy", output_file]


def build_crop_command(
    input_file: str,
    output_file: str,
    width: int,
    height: int,
    x: int,
    y: int,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        f"crop={width}:{height}:{x}:{y}",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_file,
    ]


ROTATE_FILTERS: dict[str, str] = {
    "right90": "transpose=1",
    "left90": "transpose=2",
    "rot180": "transpose=1,transpose=1",
    "hflip": "hflip",
    "vflip": "vflip",
}


def build_rotate_command(input_file: str, output_file: str, direction: str) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        ROTATE_FILTERS[direction],
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_file,
    ]


def build_mute_command(input_file: str, output_file: str) -> list[str]:
    return ["ffmpeg", "-y", "-i", input_file, "-an", "-c:v", "copy", output_file]


def build_audio_extract_command(
    input_file: str,
    output_file: str,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vn",
        "-c:a",
        "copy",
        output_file,
    ]


def build_compress_command(
    input_file: str,
    output_file: str,
    crf: int = 23,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-c:v",
        "libx264",
        "-crf",
        str(crf),
        "-c:a",
        "aac",
        output_file,
    ]


def build_volume_command(
    input_file: str,
    output_file: str,
    volume_level: float,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-filter:a",
        f"volume={volume_level}",
        "-c:v",
        "copy",
        output_file,
    ]


def escape_concat_file_path(file_path: str) -> str:
    return Path(file_path).resolve().as_posix().replace("'", r"'\''")


def build_concat_list_content(input_files: list[str]) -> str:
    lines = []
    for file_path in input_files:
        escaped_path = escape_concat_file_path(file_path)
        lines.append(f"file '{escaped_path}'\n")
    return "".join(lines)


@contextmanager
def create_concat_list_file(input_files: list[str]) -> Generator[str, None, None]:
    temp = NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        prefix="video_cli_concat_",
        delete=False,
    )
    temp_path = Path(temp.name)
    try:
        with temp:
            temp.write(build_concat_list_content(input_files))
        yield str(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def build_concat_copy_command(concat_list_file: str, output_file: str) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list_file,
        "-c",
        "copy",
        output_file,
    ]


def build_concat_reencode_command(concat_list_file: str, output_file: str) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list_file,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_file,
    ]
