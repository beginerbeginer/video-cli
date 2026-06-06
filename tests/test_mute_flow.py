import unittest
from unittest.mock import patch

from usecases.flow_result import FlowResult
from usecases.mute_flow import (
    MuteForm,
    execute_mute,
    handle_mute_review,
    run_mute_iteration,
)


class TestHandleMuteReview(unittest.TestCase):
    @patch("usecases.shared_flow.ask_review_action", return_value="cancel")
    def test_cancel(self, _mock_action):
        form = MuteForm()
        result = handle_mute_review(form)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="restart")
    def test_restart(self, _mock_action):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        result = handle_mute_review(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, MuteForm())

    @patch("usecases.shared_flow.ask_review_action", return_value="execute")
    def test_execute(self, _mock_action):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        result = handle_mute_review(form)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="dry_run")
    def test_dry_run(self, _mock_action):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        result = handle_mute_review(form)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="edit")
    @patch("usecases.mute_flow.edit_mute_form")
    def test_edit(self, mock_edit_form, _mock_action):
        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        edited = MuteForm(input_file="in.mp4", output_file="other.mp4")
        mock_edit_form.return_value = edited
        result = handle_mute_review(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form)


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
        result = run_mute_iteration(form)
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
        result = run_mute_iteration(form)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=True)

    @patch("usecases.mute_flow.collect_mute_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = MuteForm(input_file="in.mp4", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad")
        result = run_mute_iteration(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
