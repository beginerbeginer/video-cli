import subprocess
import threading
from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from shared.command_formatter import format_command
from shared.errors import FfmpegCancelledError, FfmpegExecutionError

# terminate 後に自発的な終了を待つ秒数。
# すぐ kill しないのは、ffmpeg が SIGTERM を受けるとコンテナのトレーラーを書いてから終わるため。
_TERMINATE_GRACE_SECONDS = 5.0
# 全行を保持しないのは、長い処理では stderr が数 MB になり detail として扱えないため。
_STDERR_TAIL_LINES = 40
_CANCEL_POLL_SECONDS = 0.1


@dataclass(frozen=True)
class ProgressInfo:
    frame: int = 0
    speed: str = ""
    # out_time_ms ではなく out_time（文字列）を使う。
    # FFmpeg の out_time_ms はフィールド名に反してマイクロ秒単位であり混乱を招くため。
    out_time: str = ""
    out_time_seconds: float = 0.0


@dataclass(frozen=True)
class RunResult:
    executed: bool
    command: list[str]


def _parse_clock_seconds(value: str) -> float:
    sign = -1.0 if value.startswith("-") else 1.0
    hours, minutes, seconds = value.lstrip("-").split(":")
    return sign * (int(hours) * 3600 + int(minutes) * 60 + float(seconds))


def _parse_out_time_seconds(kv: dict[str, str]) -> float:
    # out_time_us を優先するのは、文字列を分解するより丸め誤差がなく速いため。
    # 開始直後の ffmpeg は N/A を出すので、数値にならなければ次の候補を見る。
    try:
        return int(kv["out_time_us"]) / 1_000_000
    except (KeyError, ValueError):
        pass
    try:
        return _parse_clock_seconds(kv["out_time"])
    except (KeyError, ValueError):
        return 0.0


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
        out_time_seconds=_parse_out_time_seconds(kv),
    )


def run_ffmpeg(
    command: list[str],
    dry_run: bool = False,
    progress_callback: Callable[[ProgressInfo], None] | None = None,
    cancel_event: threading.Event | None = None,
    log_callback: Callable[[str], None] | None = None,
) -> RunResult:
    if dry_run:
        return RunResult(executed=False, command=command)

    if progress_callback is None and cancel_event is None and log_callback is None:
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            detail = f"終了コード: {exc.returncode}\n実行コマンド: {format_command(command)}"
            raise FfmpegExecutionError("FFmpeg の実行に失敗しました。", detail=detail) from exc
        return RunResult(executed=True, command=command)

    return _run_ffmpeg_with_progress(command, progress_callback, cancel_event, log_callback)


def _drain_stderr(
    stream: Iterable[str],
    tail: deque[str],
    log_callback: Callable[[str], None] | None,
) -> None:
    for raw_line in stream:
        line = raw_line.rstrip("\r\n")
        tail.append(line)
        if log_callback is None:
            continue
        try:
            log_callback(line)
        except Exception:
            # 例外でこのスレッドを終わらせない。読み手がいなくなると
            # パイプが埋まって ffmpeg が止まり、本来の処理まで巻き添えになるため。
            log_callback = None


def _watch_cancel(
    proc: subprocess.Popen,
    cancel_event: threading.Event,
    cancelled: threading.Event,
) -> None:
    # Event.wait をタイムアウトなしで使わないのは、正常終了したときにこのスレッドが残り続けるため。
    while proc.poll() is None:
        if not cancel_event.wait(_CANCEL_POLL_SECONDS):
            continue
        if proc.poll() is not None:
            return
        cancelled.set()
        proc.terminate()
        try:
            proc.wait(timeout=_TERMINATE_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
        return


def _start_process(cmd: list[str]) -> subprocess.Popen:
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        # stderr をキャプチャして非ゼロ終了時の detail に使う。
        # DEVNULL だとエラー原因が隠れるため。
        stderr=subprocess.PIPE,
        text=True,
        # ファイル名などに UTF-8 以外のバイトが混じっても読み取りスレッドを落とさないため。
        encoding="utf-8",
        errors="replace",
    )


def _start_background_threads(
    proc: subprocess.Popen,
    stderr_tail: deque[str],
    cancel_event: threading.Event | None,
    log_callback: Callable[[str], None] | None,
) -> tuple[list[threading.Thread], threading.Event]:
    # stderr を終了後にまとめて読まないのは、パイプのバッファ（数十 KB）が埋まると
    # ffmpeg が書き込みで止まり、stdout を待つこちらと互いに待ち合って固まるため。
    threads = [threading.Thread(target=_drain_stderr, args=(proc.stderr or (), stderr_tail, log_callback))]
    cancelled = threading.Event()
    if cancel_event is not None:
        threads.append(threading.Thread(target=_watch_cancel, args=(proc, cancel_event, cancelled)))
    for thread in threads:
        thread.daemon = True
        thread.start()
    return threads, cancelled


def _read_progress(
    stdout: Iterable[str],
    progress_callback: Callable[[ProgressInfo], None] | None,
) -> None:
    # stdout をこのスレッドで読むのは、progress_callback を呼び出し元のスレッドで呼ぶ
    # 今までの約束を保つため（CLI は端末に直接書いている）。
    chunk: list[str] = []
    for raw_line in stdout:
        line = raw_line.rstrip()
        chunk.append(line)
        if line.startswith("progress="):
            if progress_callback is not None:
                progress_callback(parse_progress_chunk(chunk))
            chunk = []


def _wait_or_kill(proc: subprocess.Popen, progress_callback: Callable[[ProgressInfo], None] | None) -> None:
    assert proc.stdout is not None
    try:
        _read_progress(proc.stdout, progress_callback)
        proc.wait()
    except BaseException:
        # callback の例外や Ctrl+C で ffmpeg を置き去りにしないため。
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise


def _raise_for_outcome(
    proc: subprocess.Popen, cancelled: threading.Event, stderr_tail: deque[str], cmd: list[str]
) -> None:
    if cancelled.is_set():
        raise FfmpegCancelledError("FFmpeg の実行はキャンセルされました。")
    if proc.returncode != 0:
        stderr_text = "\n".join(stderr_tail)
        detail = f"終了コード: {proc.returncode}\n{stderr_text}\n実行コマンド: {format_command(cmd)}"
        raise FfmpegExecutionError("FFmpeg の実行に失敗しました。", detail=detail)


def _run_ffmpeg_with_progress(
    command: list[str],
    progress_callback: Callable[[ProgressInfo], None] | None,
    cancel_event: threading.Event | None,
    log_callback: Callable[[str], None] | None,
) -> RunResult:
    if cancel_event is not None and cancel_event.is_set():
        raise FfmpegCancelledError("FFmpeg の実行はキャンセルされました。")

    cmd = command[:1] + ["-progress", "pipe:1"] + command[1:]
    proc = _start_process(cmd)
    stderr_tail: deque[str] = deque(maxlen=_STDERR_TAIL_LINES)
    threads, cancelled = _start_background_threads(proc, stderr_tail, cancel_event, log_callback)
    try:
        _wait_or_kill(proc, progress_callback)
    finally:
        for thread in threads:
            thread.join()
    _raise_for_outcome(proc, cancelled, stderr_tail, cmd)
    return RunResult(executed=True, command=command)
