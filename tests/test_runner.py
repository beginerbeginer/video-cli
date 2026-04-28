import subprocess
import unittest
from unittest.mock import patch

from ffmpeg.runner import RunResult, run_ffmpeg
from shared.errors import FfmpegExecutionError


class TestRunFfmpeg(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
