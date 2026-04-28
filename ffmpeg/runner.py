from dataclasses import dataclass
import subprocess

from shared.command_formatter import format_command
from shared.errors import FfmpegExecutionError


@dataclass(frozen=True)
class RunResult:
    executed: bool
    command: list[str]


def run_ffmpeg(command: list[str], dry_run: bool = False) -> RunResult:
    if dry_run:
        return RunResult(executed=False, command=command)

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        detail = (
            f"終了コード: {exc.returncode}\n"
            f"実行コマンド: {format_command(command)}"
        )
        raise FfmpegExecutionError(
            "FFmpeg の実行に失敗しました。",
            detail=detail,
        ) from exc

    return RunResult(executed=True, command=command)
