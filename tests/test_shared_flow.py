import unittest
from unittest.mock import MagicMock, patch

from usecases.shared_flow import execute_with_output


class TestExecuteWithOutput(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.shared_flow.format_command")
    def test_prints_command_and_completion_on_execute(self, mock_format, mock_run):
        mock_format.return_value = "ffmpeg -i input.mp4 output.mp4"
        mock_run.return_value = MagicMock(executed=True)

        with patch("builtins.print") as mock_print:
            execute_with_output(["ffmpeg", "-i", "input.mp4", "output.mp4"], "output.mp4", dry_run=False)

        mock_run.assert_called_once_with(["ffmpeg", "-i", "input.mp4", "output.mp4"], dry_run=False)
        printed = [str(call.args[0]) for call in mock_print.call_args_list if call.args]
        self.assertIn("生成された FFmpeg コマンド:", printed)
        self.assertIn("完了: output.mp4", printed)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.shared_flow.format_command")
    def test_prints_dry_run_message_when_not_executed(self, mock_format, mock_run):
        mock_format.return_value = "ffmpeg -i input.mp4 output.mp4"
        mock_run.return_value = MagicMock(executed=False)

        with patch("builtins.print") as mock_print:
            execute_with_output(["ffmpeg", "-i", "input.mp4", "output.mp4"], "output.mp4", dry_run=True)

        printed = [str(call.args[0]) for call in mock_print.call_args_list if call.args]
        self.assertIn("ドライラン完了: 実行はしていません。", printed)


if __name__ == "__main__":
    unittest.main()
