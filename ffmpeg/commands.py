from pathlib import Path
from tempfile import NamedTemporaryFile

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


def create_concat_list_file(input_files: list[str]) -> str:
    temp = NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        prefix="video_cli_concat_",
        delete=False,
    )

    with temp:
        for file_path in input_files:
            normalized = Path(file_path).resolve().as_posix().replace("'", r"'\''")
            temp.write(f"file '{normalized}'\n")

    return temp.name


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
