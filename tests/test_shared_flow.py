import unittest
from unittest.mock import ANY, MagicMock, patch

from ffmpeg.runner import ProgressInfo
from usecases.shared_flow import execute_with_output, make_cli_progress_callback


class TestExecuteWithOutput(unittest.TestCase):
    # 仕様: execute_with_output はコマンドを表示し、run_ffmpeg を呼び、完了メッセージを出す

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.shared_flow.format_command")
    def test_prints_command_and_completion_on_execute(self, mock_format, mock_run):
        # 仕様: 実行前にコマンドを表示し、実行後に完了ファイル名を表示する
        mock_format.return_value = "ffmpeg -i input.mp4 output.mp4"
        mock_run.return_value = MagicMock(executed=True)

        with patch("builtins.print") as mock_print:
            execute_with_output(["ffmpeg", "-i", "input.mp4", "output.mp4"], "output.mp4", dry_run=False)

        mock_run.assert_called_once_with(
            ["ffmpeg", "-i", "input.mp4", "output.mp4"], dry_run=False, progress_callback=ANY
        )
        printed = [str(c.args[0]) for c in mock_print.call_args_list if c.args]
        self.assertIn("生成された FFmpeg コマンド:", printed)
        self.assertIn("完了: output.mp4", printed)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.shared_flow.format_command")
    def test_prints_dry_run_message_when_not_executed(self, mock_format, mock_run):
        # 仕様: dry_run=True のとき「ドライラン完了」メッセージを表示する
        mock_format.return_value = "ffmpeg -i input.mp4 output.mp4"
        mock_run.return_value = MagicMock(executed=False)

        with patch("builtins.print") as mock_print:
            execute_with_output(["ffmpeg", "-i", "input.mp4", "output.mp4"], "output.mp4", dry_run=True)

        printed = [str(c.args[0]) for c in mock_print.call_args_list if c.args]
        self.assertIn("ドライラン完了: 実行はしていません。", printed)

    @patch("usecases.shared_flow.run_ffmpeg")
    def test_passes_progress_callback_to_run_ffmpeg(self, mock_run):
        # 仕様: run_ffmpeg に callable な progress_callback を渡す
        #       None を渡すと -progress フラグが挿入されず進捗が表示されないため
        mock_run.return_value = MagicMock(executed=True)
        execute_with_output(["ffmpeg", "-i", "in.mp4", "out.mp4"], "out.mp4", dry_run=False)
        _, kwargs = mock_run.call_args
        self.assertIsNotNone(kwargs.get("progress_callback"))
        self.assertTrue(callable(kwargs["progress_callback"]))


class TestMakeCliProgressCallback(unittest.TestCase):
    # 仕様: \r で同一行を上書きし、経過時間と処理速度をリアルタイム表示するコールバックを返す

    def test_writes_out_time_and_speed_with_carriage_return(self):
        # 仕様: 経過時間（out_time）と速度（speed）を \r 付きで stdout に書き込む
        cb = make_cli_progress_callback()
        info = ProgressInfo(out_time="00:01:30", speed="2.0x", frame=100)
        with patch("sys.stdout") as mock_stdout:
            cb(info)
        written = mock_stdout.write.call_args[0][0]
        self.assertIn("\r", written)
        self.assertIn("00:01:30", written)
        self.assertIn("2.0x", written)

    def test_flushes_stdout_after_write(self):
        # 仕様: write 後に flush する（バッファリングで表示が遅延しないため）
        cb = make_cli_progress_callback()
        info = ProgressInfo(out_time="00:00:05", speed="1.5x", frame=10)
        with patch("sys.stdout") as mock_stdout:
            cb(info)
        mock_stdout.flush.assert_called_once()


if __name__ == "__main__":
    unittest.main()
