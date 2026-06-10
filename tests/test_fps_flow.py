import unittest
from unittest.mock import patch

from usecases.fps_flow import (
    FpsForm,
    execute_fps,
    run_fps_iteration,
)
from usecases.flow_result import FlowResult


class TestExecuteFps(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.fps_flow.build_fps_command")
    def test_execute_fps_runs_command(self, mock_build, mock_run_ffmpeg):
        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        mock_run_ffmpeg.return_value.executed = True

        execute_fps(form)

        mock_build.assert_called_once_with(
            input_file="in.mp4",
            output_file="out.mp4",
            fps=30.0,
        )
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.fps_flow.build_fps_command")
    def test_execute_fps_dry_run(self, mock_build, mock_run_ffmpeg):
        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        mock_run_ffmpeg.return_value.executed = False

        execute_fps(form, dry_run=True)

        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunFpsIteration(unittest.TestCase):
    @patch("usecases.fps_flow.collect_fps_input")
    @patch("usecases.fps_flow.build_fps_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.fps_flow.execute_fps")
    def test_run_fps_iteration_execute_path(
        self, mock_execute, mock_review, mock_summary, mock_collect
    ):
        form = FpsForm()
        updated = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="execute", form=updated)

        result = run_fps_iteration(form)

        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.fps_flow.collect_fps_input")
    @patch("usecases.fps_flow.build_fps_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.fps_flow.execute_fps")
    def test_run_fps_iteration_dry_run_path(
        self, mock_execute, mock_review, mock_summary, mock_collect
    ):
        form = FpsForm()
        updated = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="dry_run", form=updated)

        result = run_fps_iteration(form)

        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=True)

    @patch("usecases.fps_flow.collect_fps_input")
    def test_run_fps_iteration_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad input")

        result = run_fps_iteration(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
