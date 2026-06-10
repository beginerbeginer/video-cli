import unittest
from unittest.mock import Mock, patch

from usecases.flow_result import FlowResult
from usecases.rotate_flow import (
    RotateForm,
    execute_rotate,
    handle_rotate_review,
    run_rotate_iteration,
)


class TestHandleRotateReview(unittest.TestCase):
    def test_cancel(self):
        form = RotateForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_rotate_review(form, ui)
        self.assertEqual(result.kind, "done")

    def test_restart(self):
        form = RotateForm(input_file="in.mp4", direction="left90", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_rotate_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, RotateForm())

    def test_execute(self):
        form = RotateForm(input_file="in.mp4", direction="right90", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_rotate_review(form, ui)
        self.assertEqual(result.kind, "execute")

    def test_dry_run(self):
        form = RotateForm(input_file="in.mp4", direction="hflip", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_rotate_review(form, ui)
        self.assertEqual(result.kind, "dry_run")

    @patch("usecases.rotate_flow.edit_rotate_form")
    def test_edit(self, mock_edit):
        form = RotateForm(input_file="in.mp4", direction="right90", output_file="out.mp4")
        edited = RotateForm(input_file="in.mp4", direction="left90", output_file="out.mp4")
        mock_edit.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_rotate_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit.assert_called_once_with(form, ui)


class TestExecuteRotate(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.rotate_flow.build_rotate_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = RotateForm(input_file="in.mp4", direction="right90", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_rotate(form)
        mock_build.assert_called_once_with(input_file="in.mp4", output_file="out.mp4", direction="right90")
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.rotate_flow.build_rotate_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = RotateForm(input_file="in.mp4", direction="hflip", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_rotate(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunRotateIteration(unittest.TestCase):
    @patch("usecases.rotate_flow.collect_rotate_input")
    @patch("usecases.rotate_flow.build_rotate_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.rotate_flow.execute_rotate")
    def test_execute_path(self, mock_execute, mock_review, mock_summary, mock_collect):
        form = RotateForm()
        updated = RotateForm(input_file="in.mp4", direction="right90", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="execute", form=updated)
        ui = Mock()
        result = run_rotate_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.rotate_flow.collect_rotate_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = RotateForm(input_file="in.mp4", direction="right90", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad")
        ui = Mock()
        result = run_rotate_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
