import unittest
from unittest.mock import ANY, Mock, patch

from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.fps_flow import (
    FpsForm,
    collect_fps_input,
    execute_fps,
    run_fps_iteration,
)


class TestExecuteFps(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.fps_flow.build_fps_command")
    def test_execute_fps_runs_command(self, mock_build, mock_run_ffmpeg):
        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        mock_run_ffmpeg.return_value.executed = True

        execute_fps(form)

        mock_build.assert_called_once_with(
            input_file="in.mp4",
            output_file="out.mp4",
            fps=30.0,
        )
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.fps_flow.build_fps_command")
    def test_execute_fps_dry_run(self, mock_build, mock_run_ffmpeg):
        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        mock_run_ffmpeg.return_value.executed = False

        execute_fps(form, dry_run=True)

        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunFpsIteration(unittest.TestCase):
    @patch("usecases.fps_flow.collect_fps_input")
    @patch("usecases.fps_flow.build_fps_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.fps_flow.execute_fps")
    def test_run_fps_iteration_execute_path(
        self, mock_execute, mock_review, mock_summary, mock_collect
    ):
        form = FpsForm()
        updated = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="execute", form=updated)
        ui = Mock()
        result = run_fps_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.fps_flow.collect_fps_input")
    @patch("usecases.fps_flow.build_fps_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.fps_flow.execute_fps")
    def test_run_fps_iteration_dry_run_path(
        self, mock_execute, mock_review, mock_summary, mock_collect
    ):
        form = FpsForm()
        updated = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="dry_run", form=updated)
        ui = Mock()
        result = run_fps_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=True)

    @patch("usecases.fps_flow.collect_fps_input")
    def test_run_fps_iteration_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_fps_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


class TestCollectFpsInput(unittest.TestCase):
    """CLI の質問の順番と、エラーを出すタイミングを固定する。"""

    PROMPTS = [
        "対象の動画ファイルを入力してください",
        "フレームレートを入力してください",
        "出力ファイル名を入力してください",
    ]

    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.fps_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def test_asks_in_order_and_returns_form(self):
        ui = make_ui([self.ws.input_file, "30", self.ws.output()])
        form, _media_info = collect_fps_input(FpsForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual(form.input_file, self.ws.input_file)
        self.assertEqual(form.output_file, self.ws.output())

    def test_missing_input_file_fails_before_asking_value(self):
        ui = make_ui([self.ws.missing_input])
        with self.assertRaises(ValidationError):
            collect_fps_input(FpsForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:1])

    def test_invalid_value_fails_before_asking_output(self):
        ui = make_ui([self.ws.input_file, "0"])
        with self.assertRaises(ValidationError):
            collect_fps_input(FpsForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:2])

    def test_missing_output_directory_fails_after_asking_output(self):
        ui = make_ui([self.ws.input_file, "30", self.ws.output_in_missing_dir])
        with self.assertRaises(ValidationError):
            collect_fps_input(FpsForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)

    def test_unsupported_output_extension_fails_after_asking_output(self):
        ui = make_ui([self.ws.input_file, "30", self.ws.output("out.txt")])
        with self.assertRaises(ValidationError):
            collect_fps_input(FpsForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)


if __name__ == "__main__":
    unittest.main()
