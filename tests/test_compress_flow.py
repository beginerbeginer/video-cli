import unittest
from unittest.mock import patch

from usecases.compress_flow import (
    CompressForm,
    execute_compress,
    run_compress_iteration,
)
from usecases.flow_result import FlowResult


class TestExecuteCompress(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.compress_flow.build_compress_command")
    def test_execute_compress_runs_command(self, mock_build, mock_run_ffmpeg):
        form = CompressForm(input_file="in.mp4", crf_raw="23", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        mock_run_ffmpeg.return_value.executed = True

        execute_compress(form)

        mock_build.assert_called_once_with(
            input_file="in.mp4",
            output_file="out.mp4",
            crf=23,
        )
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.compress_flow.build_compress_command")
    def test_execute_compress_dry_run(self, mock_build, mock_run_ffmpeg):
        form = CompressForm(input_file="in.mp4", crf_raw="23", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        mock_run_ffmpeg.return_value.executed = False

        execute_compress(form, dry_run=True)

        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunCompressIteration(unittest.TestCase):
    @patch("usecases.compress_flow.collect_compress_input")
    @patch("usecases.compress_flow.build_compress_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.compress_flow.execute_compress")
    def test_run_compress_iteration_execute_path(
        self, mock_execute, mock_review, mock_summary, mock_collect
    ):
        form = CompressForm()
        updated = CompressForm(input_file="in.mp4", crf_raw="18", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="execute", form=updated)

        result = run_compress_iteration(form)

        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.compress_flow.collect_compress_input")
    @patch("usecases.compress_flow.build_compress_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.compress_flow.execute_compress")
    def test_run_compress_iteration_dry_run_path(
        self, mock_execute, mock_review, mock_summary, mock_collect
    ):
        form = CompressForm()
        updated = CompressForm(input_file="in.mp4", crf_raw="18", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="dry_run", form=updated)

        result = run_compress_iteration(form)

        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=True)

    @patch("usecases.compress_flow.collect_compress_input")
    def test_run_compress_iteration_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = CompressForm(input_file="in.mp4", crf_raw="23", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad input")

        result = run_compress_iteration(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
