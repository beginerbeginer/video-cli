import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from shared.command_formatter import format_command
from shared.errors import FfmpegExecutionError


@dataclass(frozen=True)
class ProgressInfo:
    frame: int = 0
    speed: str = ""
    # out_time_ms ではなく out_time（文字列）を使う。
    # FFmpeg の out_time_ms はフィールド名に反してマイクロ秒単位であり混乱を招くため。
    out_time: str = ""


@dataclass(frozen=True)
class RunResult:
    executed: bool
    command: list[str]


def parse_progress_chunk(lines: list[str]) -> ProgressInfo:
    kv: dict[str, str] = {}
    for line in lines:
        if "=" in line:
            key, _, value = line.partition("=")
            kv[key] = value
    return ProgressInfo(
        frame=int(kv["frame"]) if "frame" in kv else 0,
        speed=kv.get("speed", ""),
        out_time=kv.get("out_time", "")[:8] if "out_time" in kv else "",
    )


def run_ffmpeg(
    command: list[str],
    dry_run: bool = False,
    progress_callback: Callable[[ProgressInfo], None] | None = None,
) -> RunResult:
    if dry_run:
        return RunResult(executed=False, command=command)

    if progress_callback is None:
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            detail = f"終了コード: {exc.returncode}\n実行コマンド: {format_command(command)}"
            raise FfmpegExecutionError("FFmpeg の実行に失敗しました。", detail=detail) from exc
        return RunResult(executed=True, command=command)

    return _run_ffmpeg_with_progress(command, progress_callback)


def _run_ffmpeg_with_progress(
    command: list[str],
    progress_callback: Callable[[ProgressInfo], None],
) -> RunResult:
    cmd = command[:1] + ["-progress", "pipe:1"] + command[1:]
    chunk: list[str] = []
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        # stderr をキャプチャして非ゼロ終了時の detail に使う。
        # DEVNULL だとエラー原因が隠れるため。
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    for raw_line in proc.stdout:
        line = raw_line.rstrip()
        chunk.append(line)
        if line.startswith("progress="):
            progress_callback(parse_progress_chunk(chunk))
            chunk = []
    proc.wait()
    if proc.returncode != 0:
        stderr_text = proc.stderr.read() if proc.stderr else ""
        detail = f"終了コード: {proc.returncode}\n{stderr_text}\n実行コマンド: {format_command(cmd)}"
        raise FfmpegExecutionError("FFmpeg の実行に失敗しました。", detail=detail)
    return RunResult(executed=True, command=command)
