import unittest
from unittest.mock import ANY, Mock, patch

from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.volume_flow import (
    VolumeForm,
    collect_volume_input,
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


class TestCollectVolumeInput(unittest.TestCase):
    """CLI の質問の順番と、エラーを出すタイミングを固定する。"""

    PROMPTS = [
        "対象の動画ファイルを入力してください",
        "音量倍率を入力してください",
        "出力ファイル名を入力してください",
    ]

    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.volume_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def test_asks_in_order_and_returns_form(self):
        ui = make_ui([self.ws.input_file, "1.5", self.ws.output()])
        form, _media_info = collect_volume_input(VolumeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual(form.input_file, self.ws.input_file)
        self.assertEqual(form.output_file, self.ws.output())

    def test_missing_input_file_fails_before_asking_value(self):
        ui = make_ui([self.ws.missing_input])
        with self.assertRaises(ValidationError):
            collect_volume_input(VolumeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:1])

    def test_invalid_value_fails_before_asking_output(self):
        ui = make_ui([self.ws.input_file, "11"])
        with self.assertRaises(ValidationError):
            collect_volume_input(VolumeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:2])

    def test_missing_output_directory_fails_after_asking_output(self):
        ui = make_ui([self.ws.input_file, "1.5", self.ws.output_in_missing_dir])
        with self.assertRaises(ValidationError):
            collect_volume_input(VolumeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)


if __name__ == "__main__":
    unittest.main()
