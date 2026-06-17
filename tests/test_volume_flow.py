import unittest
from unittest.mock import ANY, Mock, patch

from usecases.flow_result import FlowResult
from usecases.volume_flow import (
    VolumeForm,
    execute_volume,
    handle_volume_review,
    run_volume_iteration,
)


class TestHandleVolumeReview(unittest.TestCase):
    def test_handle_volume_review_cancel(self):
        form = VolumeForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_handle_volume_review_restart(self):
        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, VolumeForm())

    def test_handle_volume_review_execute(self):
        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_handle_volume_review_dry_run(self):
        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.volume_flow.edit_volume_form")
    def test_handle_volume_review_edit(self, mock_edit_form):
        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        edited = VolumeForm(input_file="in.mp4", volume_raw="1.5", output_file="out.mp4")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteVolume(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.volume_flow.build_volume_command")
    def test_execute_volume_runs_command(self, mock_build_volume_command, mock_run_ffmpeg):
        form = VolumeForm(input_file="in.mp4", volume_raw="1.5", output_file="out.mp4")
        mock_build_volume_command.return_value = ["ffmpeg", "..."]
        execute_volume(form)
        mock_build_volume_command.assert_called_once_with(input_file="in.mp4", output_file="out.mp4", volume_level=1.5)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.volume_flow.build_volume_command")
    def test_execute_volume_dry_run(self, mock_build_volume_command, mock_run_ffmpeg):
        form = VolumeForm(input_file="in.mp4", volume_raw="1.5", output_file="out.mp4")
        mock_build_volume_command.return_value = ["ffmpeg", "..."]
        execute_volume(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunVolumeIteration(unittest.TestCase):
    @patch("usecases.volume_flow.collect_volume_input")
    @patch("usecases.volume_flow.build_volume_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.volume_flow.execute_volume")
    def test_run_volume_iteration_execute_path(
        self, mock_execute_volume, mock_handle_review, mock_build_volume_summary, mock_collect_volume_input
    ):
        form = VolumeForm()
        updated_form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect_volume_input.return_value = (updated_form, media_info)
        mock_build_volume_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)
        ui = Mock()
        result = run_volume_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_volume.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.volume_flow.collect_volume_input")
    @patch("usecases.volume_flow.build_volume_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.volume_flow.execute_volume")
    def test_run_volume_iteration_dry_run_path(
        self, mock_execute_volume, mock_handle_review, mock_build_volume_summary, mock_collect_volume_input
    ):
        form = VolumeForm()
        updated_form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect_volume_input.return_value = (updated_form, media_info)
        mock_build_volume_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)
        ui = Mock()
        result = run_volume_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_volume.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.volume_flow.collect_volume_input")
    @patch("usecases.volume_flow.build_volume_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.volume_flow.execute_volume")
    def test_run_volume_iteration_retry_path(
        self, mock_execute_volume, mock_handle_review, mock_build_volume_summary, mock_collect_volume_input
    ):
        form = VolumeForm()
        updated_form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect_volume_input.return_value = (updated_form, media_info)
        mock_build_volume_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)
        ui = Mock()
        result = run_volume_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, updated_form)
        mock_execute_volume.assert_not_called()

    @patch("usecases.volume_flow.collect_volume_input")
    def test_run_volume_iteration_validation_error_returns_retry(self, mock_collect_volume_input):
        from shared.errors import ValidationError

        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        mock_collect_volume_input.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_volume_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
