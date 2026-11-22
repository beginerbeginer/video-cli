import unittest
from dataclasses import replace
from unittest.mock import ANY, Mock, patch

from ffmpeg.commands import build_resize_command
from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.resize_flow import (
    ResizeForm,
    build_resize_command_from_form,
    collect_resize_input,
    execute_resize,
    handle_resize_review,
    run_resize_iteration,
    validate_resize_form,
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

    def assert_fails_after_asking(self, answers: list[str], asked: int) -> None:
        # Arrange
        ui = make_ui(answers)

        # Act
        with self.assertRaises(ValidationError):
            collect_resize_input(ResizeForm(), ui)

        # Assert
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:asked])

    def test_正しく答えると入力_幅_高さ_出力の順に聞いてFormを返す(self):
        # Arrange
        ui = make_ui([self.ws.input_file, "640", "360", self.ws.output()])

        # Act
        form, media_info = collect_resize_input(ResizeForm(), ui)

        # Assert
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual((form.width_raw, form.height_raw), ("640", "360"))
        self.assertEqual(media_info, self.mock_probe.return_value)

    def test_入力ファイルが無いと幅を聞く前にエラーになる(self):
        self.assert_fails_after_asking([self.ws.missing_input], asked=1)

    def test_幅が空だと高さを聞く前にエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, ""], asked=2)

    def test_幅が範囲外だと高さを聞いたあとでエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "8", "360"], asked=3)

    def test_出力ディレクトリが無いと出力を聞いたあとでエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "640", "360", self.ws.output_in_missing_dir], asked=4)


class TestValidateResizeForm(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        (self.ws.root / "in.txt").write_text("")
        patcher = patch("usecases.resize_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def valid_form(self, **overrides) -> ResizeForm:
        form = ResizeForm(
            input_file=self.ws.input_file, width_raw="640", height_raw="360", output_file=self.ws.output()
        )
        return replace(form, **overrides)

    def test_正しいFormを渡すと対話なしでMediaInfoが返る(self):
        # Arrange
        form = self.valid_form()

        # Act
        media_info = validate_resize_form(form)

        # Assert
        self.assertEqual(media_info, self.mock_probe.return_value)
        self.mock_probe.assert_called_once_with(self.ws.input_file)

    def test_項目が不正だとその項目名がfieldに入る(self):
        cases = [
            ({"input_file": ""}, "input_file"),
            ({"input_file": self.ws.missing_input}, "input_file"),
            ({"input_file": str(self.ws.root / "in.txt")}, "input_file"),
            ({"width_raw": ""}, "width_raw"),
            ({"width_raw": "abc"}, "width_raw"),
            ({"width_raw": "15"}, "width_raw"),
            ({"height_raw": ""}, "height_raw"),
            ({"height_raw": "7681"}, "height_raw"),
            ({"output_file": ""}, "output_file"),
            ({"output_file": self.ws.output_in_missing_dir}, "output_file"),
        ]
        for overrides, expected_field in cases:
            with self.subTest(overrides=overrides):
                # Arrange
                form = self.valid_form(**overrides)

                # Act
                with self.assertRaises(ValidationError) as ctx:
                    validate_resize_form(form)

                # Assert
                self.assertEqual(ctx.exception.field, expected_field)

    def test_probeに失敗するとfieldはinput_fileになる(self):
        # Arrange
        self.mock_probe.side_effect = ValidationError("ffprobe でメディア情報を取得できませんでした")

        # Act
        with self.assertRaises(ValidationError) as ctx:
            validate_resize_form(self.valid_form())

        # Assert
        self.assertEqual(ctx.exception.field, "input_file")


class TestBuildResizeCommandFromForm(unittest.TestCase):
    def test_build_resize_commandを直接呼んだときと同じコマンドが返る(self):
        # Arrange
        form = ResizeForm(input_file="in.mp4", width_raw="640", height_raw="360", output_file="out.mp4")

        # Act
        command = build_resize_command_from_form(form)

        # Assert
        self.assertEqual(
            command, build_resize_command(input_file="in.mp4", output_file="out.mp4", width=640, height=360)
        )

    def test_値が不正だとその項目名がfieldに入る(self):
        # Arrange
        form = ResizeForm(input_file="in.mp4", width_raw="640", height_raw="abc", output_file="out.mp4")

        # Act
        with self.assertRaises(ValidationError) as ctx:
            build_resize_command_from_form(form)

        # Assert
        self.assertEqual(ctx.exception.field, "height_raw")


if __name__ == "__main__":
    unittest.main()
