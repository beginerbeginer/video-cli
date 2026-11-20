import unittest
from unittest.mock import ANY, Mock, patch

from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.speed_flow import (
    SpeedForm,
    collect_speed_input,
    execute_speed,
    handle_speed_review,
    run_speed_iteration,
)


class TestHandleSpeedReview(unittest.TestCase):
    def test_cancel(self):
        form = SpeedForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_restart(self):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, SpeedForm())

    def test_execute(self):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_dry_run(self):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.speed_flow.edit_speed_form")
    def test_edit(self, mock_edit_form):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        edited = SpeedForm(input_file="in.mp4", speed_raw="1.5", output_file="out.mp4")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteSpeed(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.speed_flow.build_speed_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_speed(form)
        mock_build.assert_called_once_with(input_file="in.mp4", output_file="out.mp4", speed=2.0)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.speed_flow.build_speed_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_speed(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunSpeedIteration(unittest.TestCase):
    @patch("usecases.speed_flow.collect_speed_input")
    @patch("usecases.speed_flow.build_speed_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.speed_flow.execute_speed")
    def test_execute_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = SpeedForm()
        updated_form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)
        ui = Mock()
        result = run_speed_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.speed_flow.collect_speed_input")
    @patch("usecases.speed_flow.build_speed_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.speed_flow.execute_speed")
    def test_dry_run_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = SpeedForm()
        updated_form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)
        ui = Mock()
        result = run_speed_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.speed_flow.collect_speed_input")
    @patch("usecases.speed_flow.build_speed_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.speed_flow.execute_speed")
    def test_retry_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = SpeedForm()
        updated_form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)
        ui = Mock()
        result = run_speed_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        mock_execute.assert_not_called()

    @patch("usecases.speed_flow.collect_speed_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_speed_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


class TestCollectSpeedInput(unittest.TestCase):
    """CLI の質問の順番と、エラーを出すタイミングを固定する。"""

    PROMPTS = [
        "対象の動画ファイルを入力してください",
        "速度倍率を入力してください",
        "出力ファイル名を入力してください",
    ]

    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.speed_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def test_asks_in_order_and_returns_form(self):
        ui = make_ui([self.ws.input_file, "2.0", self.ws.output()])
        form, _media_info = collect_speed_input(SpeedForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual(form.input_file, self.ws.input_file)
        self.assertEqual(form.output_file, self.ws.output())

    def test_missing_input_file_fails_before_asking_value(self):
        ui = make_ui([self.ws.missing_input])
        with self.assertRaises(ValidationError):
            collect_speed_input(SpeedForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:1])

    def test_invalid_value_fails_before_asking_output(self):
        ui = make_ui([self.ws.input_file, "5"])
        with self.assertRaises(ValidationError):
            collect_speed_input(SpeedForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:2])

    def test_missing_output_directory_fails_after_asking_output(self):
        ui = make_ui([self.ws.input_file, "2.0", self.ws.output_in_missing_dir])
        with self.assertRaises(ValidationError):
            collect_speed_input(SpeedForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)


if __name__ == "__main__":
    unittest.main()
