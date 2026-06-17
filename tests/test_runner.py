import subprocess
import unittest
from unittest.mock import MagicMock, patch

from ffmpeg.runner import RunResult, parse_progress_chunk, run_ffmpeg
from shared.errors import FfmpegExecutionError


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
            "frame=10", "speed=1.0x", "out_time=00:00:01.000000", "progress=continue",
            "frame=20", "speed=1.0x", "out_time=00:00:02.000000", "progress=continue",
            "frame=30", "speed=1.0x", "out_time=00:00:03.000000", "progress=end",
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
        # 仕様: チャンクにフィールドがなければ frame=0, speed="", out_time="" を返す
        info = parse_progress_chunk(["progress=continue"])
        self.assertEqual(info.frame, 0)
        self.assertEqual(info.speed, "")
        self.assertEqual(info.out_time, "")


if __name__ == "__main__":
    unittest.main()
