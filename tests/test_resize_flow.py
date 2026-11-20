import unittest
from unittest.mock import ANY, Mock, patch

from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.resize_flow import (
    ResizeForm,
    collect_resize_input,
    execute_resize,
    handle_resize_review,
    run_resize_iteration,
)


class TestHandleResizeReview(unittest.TestCase):
    def test_handle_resize_review_cancel(self):
        form = ResizeForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_resize_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_handle_resize_review_restart(self):
        form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_resize_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, ResizeForm())

    def test_handle_resize_review_execute(self):
        form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_resize_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_handle_resize_review_dry_run(self):
        form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_resize_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.resize_flow.edit_resize_form")
    def test_handle_resize_review_edit(self, mock_edit_form):
        form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        edited = ResizeForm(input_file="in.mp4", width_raw="640", height_raw="720", output_file="out.mp4")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_resize_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteResize(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.resize_flow.build_resize_command")
    def test_execute_resize_runs_command(self, mock_build_resize_command, mock_run_ffmpeg):
        form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        mock_build_resize_command.return_value = ["ffmpeg", "..."]
        execute_resize(form)
        mock_build_resize_command.assert_called_once_with(
            input_file="in.mp4", output_file="out.mp4", width=1280, height=720
        )
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.resize_flow.build_resize_command")
    def test_execute_resize_dry_run(self, mock_build_resize_command, mock_run_ffmpeg):
        form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        mock_build_resize_command.return_value = ["ffmpeg", "..."]
        execute_resize(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunResizeIteration(unittest.TestCase):
    @patch("usecases.resize_flow.collect_resize_input")
    @patch("usecases.resize_flow.build_resize_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.resize_flow.execute_resize")
    def test_run_resize_iteration_execute_path(
        self, mock_execute_resize, mock_handle_review, mock_build_resize_summary, mock_collect_resize_input
    ):
        form = ResizeForm()
        updated_form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        media_info = object()
        mock_collect_resize_input.return_value = (updated_form, media_info)
        mock_build_resize_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)
        ui = Mock()
        result = run_resize_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_resize.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.resize_flow.collect_resize_input")
    @patch("usecases.resize_flow.build_resize_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.resize_flow.execute_resize")
    def test_run_resize_iteration_dry_run_path(
        self, mock_execute_resize, mock_handle_review, mock_build_resize_summary, mock_collect_resize_input
    ):
        form = ResizeForm()
        updated_form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        media_info = object()
        mock_collect_resize_input.return_value = (updated_form, media_info)
        mock_build_resize_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)
        ui = Mock()
        result = run_resize_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_resize.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.resize_flow.collect_resize_input")
    @patch("usecases.resize_flow.build_resize_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.resize_flow.execute_resize")
    def test_run_resize_iteration_retry_path(
        self, mock_execute_resize, mock_handle_review, mock_build_resize_summary, mock_collect_resize_input
    ):
        form = ResizeForm()
        updated_form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        media_info = object()
        mock_collect_resize_input.return_value = (updated_form, media_info)
        mock_build_resize_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)
        ui = Mock()
        result = run_resize_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, updated_form)
        mock_execute_resize.assert_not_called()

    @patch("usecases.resize_flow.collect_resize_input")
    def test_run_resize_iteration_validation_error_returns_retry(self, mock_collect_resize_input):
        from shared.errors import ValidationError

        form = ResizeForm(input_file="in.mp4", width_raw="1280", height_raw="720", output_file="out.mp4")
        mock_collect_resize_input.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_resize_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


class TestCollectResizeInput(unittest.TestCase):
    """CLI の質問の順番と、エラーを出すタイミングを固定する。"""

    PROMPTS = [
        "対象の動画ファイルを入力してください",
        "幅を入力してください",
        "高さを入力してください",
        "出力ファイル名を入力してください",
    ]

    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.resize_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def test_asks_in_order_and_returns_form(self):
        ui = make_ui([self.ws.input_file, "640", "360", self.ws.output()])
        form, _media_info = collect_resize_input(ResizeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual((form.width_raw, form.height_raw), ("640", "360"))

    def test_missing_input_file_fails_before_asking_width(self):
        ui = make_ui([self.ws.missing_input])
        with self.assertRaises(ValidationError):
            collect_resize_input(ResizeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:1])

    def test_empty_width_fails_before_asking_height(self):
        ui = make_ui([self.ws.input_file, ""])
        with self.assertRaises(ValidationError):
            collect_resize_input(ResizeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:2])

    def test_out_of_range_width_fails_after_asking_height(self):
        ui = make_ui([self.ws.input_file, "8", "360"])
        with self.assertRaises(ValidationError):
            collect_resize_input(ResizeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:3])

    def test_missing_output_directory_fails_after_asking_output(self):
        ui = make_ui([self.ws.input_file, "640", "360", self.ws.output_in_missing_dir])
        with self.assertRaises(ValidationError):
            collect_resize_input(ResizeForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)


if __name__ == "__main__":
    unittest.main()
