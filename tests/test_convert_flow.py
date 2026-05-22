import unittest
from unittest.mock import patch

from usecases.convert_flow import (
    ConvertForm,
    execute_convert,
    handle_convert_review,
    run_convert_iteration,
)
from usecases.flow_result import FlowResult


class TestHandleConvertReview(unittest.TestCase):
    @patch("usecases.shared_flow.ask_review_action", return_value="cancel")
    def test_cancel(self, _mock_action):
        form = ConvertForm()
        result = handle_convert_review(form)
        self.assertEqual(result.kind, "done")

    @patch("usecases.shared_flow.ask_review_action", return_value="restart")
    def test_restart(self, _mock_action):
        form = ConvertForm(input_file="in.mov", output_file="out.mp4")
        result = handle_convert_review(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, ConvertForm())

    @patch("usecases.shared_flow.ask_review_action", return_value="execute")
    def test_execute(self, _mock_action):
        form = ConvertForm(input_file="in.mov", output_file="out.mp4")
        result = handle_convert_review(form)
        self.assertEqual(result.kind, "execute")

    @patch("usecases.shared_flow.ask_review_action", return_value="dry_run")
    def test_dry_run(self, _mock_action):
        form = ConvertForm(input_file="in.mov", output_file="out.mp4")
        result = handle_convert_review(form)
        self.assertEqual(result.kind, "dry_run")

    @patch("usecases.shared_flow.ask_review_action", return_value="edit")
    @patch("usecases.convert_flow.edit_convert_form")
    def test_edit(self, mock_edit, _mock_action):
        form = ConvertForm(input_file="in.mov", output_file="out.mp4")
        edited = ConvertForm(input_file="in.mov", output_file="out.mkv")
        mock_edit.return_value = edited
        result = handle_convert_review(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)


class TestExecuteConvert(unittest.TestCase):
    @patch("usecases.convert_flow.run_ffmpeg")
    @patch("usecases.convert_flow.build_convert_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = ConvertForm(input_file="in.mov", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_convert(form)
        mock_build.assert_called_once_with(input_file="in.mov", output_file="out.mp4")
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.convert_flow.run_ffmpeg")
    @patch("usecases.convert_flow.build_convert_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = ConvertForm(input_file="in.mov", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_convert(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunConvertIteration(unittest.TestCase):
    @patch("usecases.convert_flow.collect_convert_input")
    @patch("usecases.convert_flow.build_convert_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.convert_flow.execute_convert")
    def test_execute_path(self, mock_execute, mock_review, mock_summary, mock_collect):
        form = ConvertForm()
        updated = ConvertForm(input_file="in.mov", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="execute", form=updated)
        result = run_convert_iteration(form)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.convert_flow.collect_convert_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError
        form = ConvertForm(input_file="in.mov", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad")
        result = run_convert_iteration(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
