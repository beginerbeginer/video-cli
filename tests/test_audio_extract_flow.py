import unittest
from unittest.mock import ANY, Mock, patch

from usecases.audio_extract_flow import (
    AudioExtractForm,
    execute_audio_extract,
    handle_audio_extract_review,
    run_audio_extract_iteration,
)
from usecases.flow_result import FlowResult


class TestHandleAudioExtractReview(unittest.TestCase):
    def test_cancel(self):
        form = AudioExtractForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_audio_extract_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_restart(self):
        form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_audio_extract_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, AudioExtractForm())

    def test_execute(self):
        form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_audio_extract_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_dry_run(self):
        form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_audio_extract_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.audio_extract_flow.edit_audio_extract_form")
    def test_edit(self, mock_edit_form):
        form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        edited = AudioExtractForm(input_file="in.mp4", output_file="out.aac")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_audio_extract_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteAudioExtract(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.audio_extract_flow.build_audio_extract_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_audio_extract(form)
        mock_build.assert_called_once_with(input_file="in.mp4", output_file="out.mp3")
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.audio_extract_flow.build_audio_extract_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_audio_extract(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunAudioExtractIteration(unittest.TestCase):
    @patch("usecases.audio_extract_flow.collect_audio_extract_input")
    @patch("usecases.audio_extract_flow.build_audio_extract_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.audio_extract_flow.execute_audio_extract")
    def test_execute_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = AudioExtractForm()
        updated_form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)
        ui = Mock()
        result = run_audio_extract_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.audio_extract_flow.collect_audio_extract_input")
    @patch("usecases.audio_extract_flow.build_audio_extract_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.audio_extract_flow.execute_audio_extract")
    def test_dry_run_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = AudioExtractForm()
        updated_form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)
        ui = Mock()
        result = run_audio_extract_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.audio_extract_flow.collect_audio_extract_input")
    @patch("usecases.audio_extract_flow.build_audio_extract_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.audio_extract_flow.execute_audio_extract")
    def test_retry_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = AudioExtractForm()
        updated_form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)
        ui = Mock()
        result = run_audio_extract_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        mock_execute.assert_not_called()

    @patch("usecases.audio_extract_flow.collect_audio_extract_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = AudioExtractForm(input_file="in.mp4", output_file="out.mp3")
        mock_collect.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_audio_extract_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
