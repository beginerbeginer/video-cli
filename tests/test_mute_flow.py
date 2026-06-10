import unittest
from unittest.mock import Mock, patch

from usecases.flow_result import FlowResult
from usecases.mute_flow import (
    MuteForm,
    execute_mute,
    handle_mute_review,
    run_mute_iteration,
)


class TestHandleMuteReview(unittest.TestCase):
    def test_cancel(self):
        form = MuteForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_mute_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_restart(self):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_mute_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, MuteForm())

    def test_execute(self):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_mute_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_dry_run(self):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_mute_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.mute_flow.edit_mute_form")
    def test_edit(self, mock_edit_form):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        edited = MuteForm(input_file="in.mp4", output_file="other.mp4")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_mute_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteMute(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.mute_flow.build_mute_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_mute(form)
        mock_build.assert_called_once_with(input_file="in.mp4", output_file="out.mp4")
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.mute_flow.build_mute_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_mute(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunMuteIteration(unittest.TestCase):
    @patch("usecases.mute_flow.collect_mute_input")
    @patch("usecases.mute_flow.build_mute_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.mute_flow.execute_mute")
    def test_execute_path(self, mock_execute, mock_review, mock_summary, mock_collect):
        form = MuteForm()
        updated = MuteForm(input_file="in.mp4", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="execute", form=updated)
        ui = Mock()
        result = run_mute_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.mute_flow.collect_mute_input")
    @patch("usecases.mute_flow.build_mute_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.mute_flow.execute_mute")
    def test_dry_run_path(self, mock_execute, mock_review, mock_summary, mock_collect):
        form = MuteForm()
        updated = MuteForm(input_file="in.mp4", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="dry_run", form=updated)
        ui = Mock()
        result = run_mute_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=True)

    @patch("usecases.mute_flow.collect_mute_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad")
        ui = Mock()
        result = run_mute_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
