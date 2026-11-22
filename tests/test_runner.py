import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from ffmpeg.runner import RunResult, parse_progress_chunk, run_ffmpeg
from shared.errors import FfmpegCancelledError, FfmpegExecutionError


class TestRunFfmpeg(unittest.TestCase):
    # 仕様: callback なしの通常パスは既存の subprocess.run ベースの動作を維持する

    @patch("ffmpeg.runner.subprocess.run")
    def test_run_ffmpeg_executes_subprocess_when_not_dry_run(self, mock_run):
        command = ["ffmpeg", "-version"]

        result = run_ffmpeg(command)

        mock_run.assert_called_once_with(command, check=True)
        self.assertEqual(result, RunResult(executed=True, command=command))

    @patch("ffmpeg.runner.subprocess.run")
    def test_run_ffmpeg_skips_subprocess_when_dry_run(self, mock_run):
        command = ["ffmpeg", "-i", "in.mp4", "out.mp4"]

        result = run_ffmpeg(command, dry_run=True)

        mock_run.assert_not_called()
        self.assertEqual(result, RunResult(executed=False, command=command))

    @patch("ffmpeg.runner.subprocess.run")
    def test_run_ffmpeg_wraps_called_process_error(self, mock_run):
        command = ["ffmpeg", "-i", "broken.mp4", "out.mp4"]
        mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd=command)

        with self.assertRaises(FfmpegExecutionError):
            run_ffmpeg(command)


def _make_mock_popen(stdout_lines: list[str], returncode: int = 0):
    mock_proc = MagicMock()
    mock_proc.stdout = iter(line + "\n" for line in stdout_lines)
    mock_proc.returncode = returncode
    mock_proc.wait.return_value = None
    mock_popen = MagicMock(return_value=mock_proc)
    return mock_popen, mock_proc


class TestRunFfmpegWithCallback(unittest.TestCase):
    # 仕様: progress_callback を渡すと Popen ベースでリアルタイム進捗を受け取れる

    @patch("ffmpeg.runner.subprocess.run")
    def test_no_callback_uses_subprocess_run_without_modifying_command(self, mock_run):
        # 仕様: callback=None のとき、コマンドを変えず subprocess.run を呼ぶ
        #       既存の全呼び出し元への後方互換を保つため
        command = ["ffmpeg", "-i", "in.mp4", "out.mp4"]
        run_ffmpeg(command)
        mock_run.assert_called_once_with(command, check=True)

    @patch("ffmpeg.runner.subprocess.Popen")
    def test_callback_inserts_progress_flag_immediately_after_ffmpeg(self, mock_popen_cls):
        # 仕様: -progress pipe:1 はインデックス1（ffmpeg の直後）に挿入される
        #       FFmpeg のグローバルオプションは -i より前に置く必要があるため
        mock_popen, _ = _make_mock_popen(["progress=end"])
        mock_popen_cls.side_effect = mock_popen
        command = ["ffmpeg", "-i", "in.mp4", "out.mp4"]
        run_ffmpeg(command, progress_callback=lambda _: None)
        called_cmd = mock_popen_cls.call_args[0][0]
        self.assertEqual(called_cmd[:3], ["ffmpeg", "-progress", "pipe:1"])

    @patch("ffmpeg.runner.subprocess.Popen")
    def test_callback_is_called_for_every_chunk_including_end(self, mock_popen_cls):
        # 仕様: progress=continue と progress=end の各チャンクでコールバックを呼ぶ
        #       progress=end 時にも呼ぶことで最終進捗（100%）を表示できる
        lines = [
            "frame=10",
            "speed=1.0x",
            "out_time=00:00:01.000000",
            "progress=continue",
            "frame=20",
            "speed=1.0x",
            "out_time=00:00:02.000000",
            "progress=continue",
            "frame=30",
            "speed=1.0x",
            "out_time=00:00:03.000000",
            "progress=end",
        ]
        mock_popen, _ = _make_mock_popen(lines)
        mock_popen_cls.side_effect = mock_popen
        cb = MagicMock()
        run_ffmpeg(["ffmpeg", "-i", "in.mp4", "out.mp4"], progress_callback=cb)
        self.assertEqual(cb.call_count, 3)

    @patch("ffmpeg.runner.subprocess.Popen")
    def test_callback_receives_parsed_progress_info(self, mock_popen_cls):
        # 仕様: コールバックには parse_progress_chunk で変換した ProgressInfo が渡される
        lines = ["frame=100", "speed=2.0x", "out_time=00:00:05.000000", "progress=end"]
        mock_popen, _ = _make_mock_popen(lines)
        mock_popen_cls.side_effect = mock_popen
        cb = MagicMock()
        run_ffmpeg(["ffmpeg", "-i", "in.mp4", "out.mp4"], progress_callback=cb)
        self.assertEqual(cb.call_count, 1)
        self.assertEqual(cb.call_args[0][0].frame, 100)

    @patch("ffmpeg.runner.subprocess.Popen")
    def test_nonzero_exit_raises_ffmpeg_execution_error(self, mock_popen_cls):
        # 仕様: FFmpeg が非ゼロで終了したとき FfmpegExecutionError を送出する
        mock_popen, _ = _make_mock_popen(["progress=end"], returncode=1)
        mock_popen_cls.side_effect = mock_popen
        with self.assertRaises(FfmpegExecutionError):
            run_ffmpeg(["ffmpeg", "-i", "in.mp4", "out.mp4"], progress_callback=lambda _: None)


class _FakeFfmpegTestCase(unittest.TestCase):
    # 本物の子プロセスを動かして、パイプ・スレッド・シグナルの扱いを固定する。
    # Popen を mock するとパイプが埋まる問題やプロセスの終了を再現できないため。
    #
    # sys.executable -c を直接 command にしないのは、run_ffmpeg が command[0] の直後に
    # -progress pipe:1 を挿入し、python がそれを自分のオプションとして解釈して落ちるため。
    # 代わりに引数を無視する Python スクリプトを command[0] として置く。

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.procs: list[subprocess.Popen] = []
        real_popen = subprocess.Popen

        def spy(*args, **kwargs):
            proc = real_popen(*args, **kwargs)
            self.procs.append(proc)
            return proc

        patcher = patch("ffmpeg.runner.subprocess.Popen", side_effect=spy)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._kill_leftovers)

    def _kill_leftovers(self):
        for proc in self.procs:
            if proc.poll() is None:
                proc.kill()
                proc.wait()

    def make_fake_ffmpeg(self, body: str) -> list[str]:
        path = os.path.join(self._tmpdir.name, "fake_ffmpeg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"#!{sys.executable}\n")
            f.write(textwrap.dedent(body))
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        return [path, "-i", "in.mp4", "out.mp4"]

    def run_with_timeout(self, timeout: float, **kwargs):
        outcome: dict = {}

        def target():
            try:
                outcome["result"] = run_ffmpeg(**kwargs)
            except BaseException as exc:  # テスト側で検証するため全て拾う
                outcome["error"] = exc

        worker = threading.Thread(target=target, daemon=True)
        worker.start()
        worker.join(timeout)
        if worker.is_alive():
            self._kill_leftovers()
            self.fail(f"run_ffmpeg が {timeout} 秒以内に終わらなかった（パイプ詰まりの疑い）")
        return outcome


@unittest.skipIf(sys.platform == "win32", "shebang 付きスクリプトを実行ファイルとして使うため")
class TestRunFfmpegStderrDrain(_FakeFfmpegTestCase):
    # 仕様: stderr を大量に書くプロセスでもパイプが埋まって止まらない

    _NOISY_BODY = """
        import sys
        line = "x" * 1023 + "\\n"
        for i in range(1024):
            sys.stderr.write(line)
        sys.stderr.write("LAST_STDERR_LINE\\n")
        sys.stderr.flush()
        sys.stdout.write("frame=1\\nout_time_us=1000000\\nprogress=end\\n")
        sys.stdout.flush()
        sys.exit(int(sys.argv[-1]) if sys.argv[-1].isdigit() else 0)
    """

    def test_stderrに1MB書くプロセスでも止まらずに完了する(self):
        # Arrange
        command = self.make_fake_ffmpeg(self._NOISY_BODY)
        received = []

        # Act
        outcome = self.run_with_timeout(10, command=command, progress_callback=received.append)

        # Assert
        self.assertNotIn("error", outcome)
        self.assertEqual(outcome["result"], RunResult(executed=True, command=command))
        self.assertEqual([info.out_time_seconds for info in received], [1.0])

    def test_失敗するとdetailにはstderrの末尾だけが入る(self):
        # 仕様: 1MB 全てを入れると例外メッセージとして扱えない大きさになるため
        # Arrange
        command = self.make_fake_ffmpeg(self._NOISY_BODY) + ["1"]

        # Act
        outcome = self.run_with_timeout(10, command=command, progress_callback=lambda _: None)

        # Assert
        error = outcome.get("error")
        self.assertIsInstance(error, FfmpegExecutionError)
        self.assertIn("終了コード: 1", error.detail)
        self.assertIn("LAST_STDERR_LINE", error.detail)
        self.assertLess(len(error.detail), 100 * 1024)


@unittest.skipIf(sys.platform == "win32", "shebang 付きスクリプトを実行ファイルとして使うため")
class TestRunFfmpegLogCallback(_FakeFfmpegTestCase):
    # 仕様: log_callback に stderr の各行（改行なし）を順番どおりに渡す

    def test_log_callbackを渡すとstderrの各行が順番に渡される(self):
        # Arrange
        command = self.make_fake_ffmpeg("""
            import sys
            sys.stderr.write("first line\\nsecond line\\n")
            sys.stderr.flush()
            sys.stdout.write("progress=end\\n")
        """)
        lines = []

        # Act
        outcome = self.run_with_timeout(10, command=command, log_callback=lines.append)

        # Assert
        self.assertNotIn("error", outcome)
        self.assertEqual(lines, ["first line", "second line"])


@unittest.skipIf(sys.platform == "win32", "SIGTERM を無視する子プロセスを使うため")
class TestRunFfmpegCancel(_FakeFfmpegTestCase):
    # 仕様: cancel_event がセットされたら ffmpeg を止めて FfmpegCancelledError を投げる

    _ENDLESS_BODY = """
        import signal, sys, time
        if "ignore-term" in sys.argv:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            sys.stdout.write("out_time_us=500000\\nprogress=continue\\n")
            sys.stdout.flush()
            time.sleep(0.05)
    """

    def test_cancel_eventをセットするとプロセスが止まりFfmpegCancelledErrorになる(self):
        # Arrange
        command = self.make_fake_ffmpeg(self._ENDLESS_BODY)
        cancel = threading.Event()
        started = time.monotonic()

        # Act
        outcome = self.run_with_timeout(
            10, command=command, cancel_event=cancel, progress_callback=lambda _: cancel.set()
        )

        # Assert
        self.assertIsInstance(outcome.get("error"), FfmpegCancelledError)
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual(len(self.procs), 1)
        self.assertIsNotNone(self.procs[0].poll())

    def test_terminateを無視するプロセスは猶予のあとkillされる(self):
        # Arrange
        command = self.make_fake_ffmpeg(self._ENDLESS_BODY) + ["ignore-term"]
        cancel = threading.Event()

        # Act
        with patch("ffmpeg.runner._TERMINATE_GRACE_SECONDS", 0.3):
            outcome = self.run_with_timeout(
                10, command=command, cancel_event=cancel, progress_callback=lambda _: cancel.set()
            )

        # Assert
        self.assertIsInstance(outcome.get("error"), FfmpegCancelledError)
        self.assertEqual(self.procs[0].poll(), -9)

    def test_progress_callbackなしでもcancel_eventでキャンセルできる(self):
        # 仕様: API はログだけ購読してキャンセルボタンを出すことがあるため
        # Arrange
        command = self.make_fake_ffmpeg(self._ENDLESS_BODY)
        cancel = threading.Event()
        threading.Timer(0.3, cancel.set).start()

        # Act
        outcome = self.run_with_timeout(10, command=command, cancel_event=cancel)

        # Assert
        self.assertIsInstance(outcome.get("error"), FfmpegCancelledError)

    def test_開始前にcancel_eventがセット済みならプロセスを起動しない(self):
        # Arrange
        command = self.make_fake_ffmpeg(self._ENDLESS_BODY)
        cancel = threading.Event()
        cancel.set()

        # Act
        outcome = self.run_with_timeout(10, command=command, cancel_event=cancel)

        # Assert
        self.assertIsInstance(outcome.get("error"), FfmpegCancelledError)
        self.assertEqual(self.procs, [])

    def test_FfmpegCancelledErrorはFfmpegExecutionErrorのサブクラスではない(self):
        # 仕様: 呼び出し側がキャンセルを「失敗しました」と表示しないで済むようにするため
        self.assertFalse(issubclass(FfmpegCancelledError, FfmpegExecutionError))


class TestParseProgressChunk(unittest.TestCase):
    # 仕様: FFmpeg の -progress pipe:1 出力（key=value 形式）を ProgressInfo に変換する

    def test_out_time_is_trimmed_to_seconds_precision(self):
        # 仕様: out_time のマイクロ秒以下（.ffffff）は切り捨て、HH:MM:SS 形式で返す
        lines = ["out_time=00:01:30.000000", "progress=continue"]
        info = parse_progress_chunk(lines)
        self.assertEqual(info.out_time, "00:01:30")

    def test_speed_is_preserved_as_string(self):
        # 仕様: speed は "2.0x" のように単位込みの文字列のまま保持する
        lines = ["speed=2.0x", "progress=continue"]
        info = parse_progress_chunk(lines)
        self.assertEqual(info.speed, "2.0x")

    def test_frame_is_parsed_as_int(self):
        # 仕様: frame は整数にパースする
        lines = ["frame=120", "progress=continue"]
        info = parse_progress_chunk(lines)
        self.assertEqual(info.frame, 120)

    def test_missing_fields_fall_back_to_defaults(self):
        # 仕様: チャンクにフィールドがなければ frame=0, speed="", out_time="", out_time_seconds=0.0 を返す
        info = parse_progress_chunk(["progress=continue"])
        self.assertEqual(info.frame, 0)
        self.assertEqual(info.speed, "")
        self.assertEqual(info.out_time, "")
        self.assertEqual(info.out_time_seconds, 0.0)

    def test_out_time_usがあると秒に換算してout_time_secondsになる(self):
        # Arrange
        lines = ["out_time_us=90500000", "out_time=00:01:30.500000", "progress=continue"]

        # Act
        info = parse_progress_chunk(lines)

        # Assert
        self.assertEqual(info.out_time_seconds, 90.5)

    def test_out_time_usが無いとout_timeから秒を計算する(self):
        # Arrange
        lines = ["out_time=01:02:03.250000", "progress=continue"]

        # Act
        info = parse_progress_chunk(lines)

        # Assert
        self.assertEqual(info.out_time_seconds, 3723.25)

    def test_out_time_usがNAならout_timeから秒を計算する(self):
        # 仕様: 開始直後の ffmpeg は out_time_us に N/A を出すことがあるため
        # Arrange
        lines = ["out_time_us=N/A", "out_time=00:00:02.000000", "progress=continue"]

        # Act
        info = parse_progress_chunk(lines)

        # Assert
        self.assertEqual(info.out_time_seconds, 2.0)

    def test_out_time_usもout_timeもNAならout_time_secondsは0になる(self):
        # Arrange
        lines = ["out_time_us=N/A", "out_time=N/A", "progress=continue"]

        # Act
        info = parse_progress_chunk(lines)

        # Assert
        self.assertEqual(info.out_time_seconds, 0.0)

    def test_out_time_secondsを足してもout_time文字列は今までどおり(self):
        # 仕様: CLI の進捗表示（make_cli_progress_callback）の見た目を変えないため
        # Arrange
        lines = ["out_time_us=5000000", "out_time=00:00:05.000000", "progress=continue"]

        # Act
        info = parse_progress_chunk(lines)

        # Assert
        self.assertEqual(info.out_time, "00:00:05")



if __name__ == "__main__":
    unittest.main()
